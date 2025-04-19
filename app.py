import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.express as px
from dash import callback_context
from datetime import datetime

# Read the dummy data from the Excel file
df = pd.read_excel("dummy_data.xlsx")

# Function to extract latitude and longitude
def get_lat_lon(location_str):
    if isinstance(location_str, str):
        try:
            lat, lon = map(float, location_str.split(','))
            return lat, lon
        except ValueError:
            print(f"Warning: Could not parse coordinates from string: {location_str}")
            return None, None
    else:
        return None, None

# Apply the function to create separate lat and lon columns
df[['latitude', 'longitude']] = df['Custom Location (Lat,Lon)'].apply(get_lat_lon).tolist()

# Filter out rows with NaN in latitude or longitude
df_cleaned = df.dropna(subset=['latitude', 'longitude'])

# Convert 'Event data' to datetime objects and sort
df_cleaned['event_datetime'] = pd.to_datetime(df_cleaned['Event data dd/mm/yyyy'], format='%d/%m/%Y')
df_sorted = df_cleaned.sort_values(by='event_datetime', ascending=False).reset_index(drop=True)

app = dash.Dash(__name__)

cards = [
    html.Div(
        [
            html.H1(f"{row['A Location']}", style={'fontFamily': 'Arial', 'fontSize': '1.5em', 'marginBottom': '10px'}),
            html.P([html.Strong("Energy Storage Capacity: "),
                    html.Span(f"{row['B Energy Storage Capacity (MWh)']} MWh",
                              style={'color': 'red', 'fontSize': '1.5em', 'fontWeight': 'bold'})],
                   style={'fontFamily': 'Arial', 'marginBottom': '5px'}),
            html.P([html.Strong("Power: "),
                    html.Span(f"{row['C Power (MWh)']} MW",
                              style={'color': 'red', 'fontSize': '1.5em', 'fontWeight': 'bold'})],
                   style={'fontFamily': 'Arial', 'marginBottom': '5px'}),
            *[html.P([html.Strong(f"{col}: "),
                       html.A(f"{row[col]}", href=row[col], target="_blank",
                              style={'fontFamily': 'Arial', 'fontSize': '0.9em'})],
                      style={'fontFamily': 'Arial', 'fontSize': '0.9em', 'marginBottom': '5px'})
              for col in df_sorted.columns
              if col.startswith('Source URL') and isinstance(row[col], str) and row[col].startswith('http')],
            *[html.P([html.Strong(f"{col}: "), f"{row[col]}"], style={'fontFamily': 'Arial', 'fontSize': '0.9em', 'marginBottom': '5px'})
              for col in df_sorted.columns
              if col not in ['latitude', 'longitude', 'event_datetime', 'A Location',
                              'B Energy Storage Capacity (MWh)', 'C Power (MWh)']
              and not col.startswith('Source URL')],
            html.A(f"Read More", href=row['Source URL 1'], target="_blank", style={'fontFamily': 'Arial', 'fontSize': '0.8em'})
        ],
        className="incident-card",
        id={'type': 'card', 'index': str(index)},
        style={'fontFamily': 'Arial', 'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px'}
    )
    for index, row in df_sorted.iterrows()
]

app.layout = html.Div(
    style={'display': 'flex', 'flexDirection': 'row', 'height': '80vh', 'fontFamily': 'Arial', 'padding': '20px'},
    children=[
        html.Div(
            id="cards-container",
            children=cards,
            style={
                'flex': '0 0 40%',
                'overflowY': 'auto',
                'paddingRight': '20px'
            }
        ),
        html.Div(
            dcc.Graph(
                id='incident-map',
                figure=px.scatter_map(df_sorted,
                                     lat="latitude",
                                     lon="longitude",
                                     hover_name="A Location",
                                     size="C Power (MWh)",
                                     size_max=30,
                                     zoom=4,
                                     height=600,
                                     center={'lat': df_sorted['latitude'].mean(), 'lon': df_sorted['longitude'].mean()}),
                config={'scrollZoom': True},
            ),
            style={'flex': '1'}
        )
    ]
)

@app.callback(
    Output('cards-container', 'children'),
    Output('incident-map', 'figure'),
    Input('incident-map', 'clickData'),
    Input({'type': 'card', 'index': dash.ALL}, 'n_clicks'),
    State('cards-container', 'children'),
    State('incident-map', 'figure'),
    State({'type': 'card', 'index': dash.ALL}, 'id')
)
def update_on_click(map_click_data, card_clicks, current_cards, current_figure, card_ids):
    ctx = callback_context
    triggered_id = ctx.triggered_id

    updated_cards = list(current_cards)
    updated_figure = current_figure.copy()

    # Reset styles for all cards (except font and basic layout)
    for i in range(len(updated_cards)):
        default_style = {'fontFamily': 'Arial', 'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px'}
        if 'style' in updated_cards[i]['props']:
            updated_cards[i]['props']['style'] = default_style
        else:
            updated_cards[i]['props']['style'] = default_style

    # Reset marker colors on the map
    if 'data' in updated_figure and len(updated_figure['data']) > 0 and 'marker' in updated_figure['data'][0]:
        updated_figure['data'][0]['marker']['color'] = ['blue'] * len(df_sorted)

    clicked_index = None
    clicked_lat = None
    clicked_lon = None
    clicked_location_name = None

    if triggered_id == 'incident-map' and map_click_data:
        clicked_location_name = map_click_data['points'][0]['hovertext']
        clicked_row = df_sorted[df_sorted['A Location'] == clicked_location_name].iloc[0]
        clicked_index = clicked_row.name
        clicked_lat = clicked_row['latitude']
        clicked_lon = clicked_row['longitude']
    elif isinstance(triggered_id, dict) and triggered_id['type'] == 'card' and card_clicks:
        valid_clicks = [c for c in card_clicks if c is not None]
        if valid_clicks:
            clicked_card_index_in_list = card_clicks.index(max(valid_clicks))
            clicked_card_id_str = card_ids[clicked_card_index_in_list]['index']
            clicked_index = int(clicked_card_id_str)
            clicked_location_name = df_sorted.iloc[clicked_index]['A Location']

    if clicked_index is not None:
        clicked_row_from_index = df_sorted.iloc[clicked_index]
        clicked_lat = clicked_row_from_index['latitude']
        clicked_lon = clicked_row_from_index['longitude']

        # Highlight the corresponding card
        for i, card in enumerate(updated_cards):
            card_index = int(card['props']['id']['index'])
            if card_index == clicked_index:
                new_card = card.copy()
                new_card['props']['style'] = {'border': '2px solid red', 'zIndex': 1, 'fontFamily': 'Arial', 'marginBottom': '10px', 'padding': '10px'}
                updated_cards[i] = new_card
            elif 'style' not in updated_cards[i]['props'] or 'fontFamily' not in updated_cards[i]['props']['style']:
                updated_cards[i]['props']['style'] = {'fontFamily': 'Arial', 'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px'}

        # Update map center and marker color
        updated_figure['layout']['mapbox']['center'] = {'lat': clicked_lat, 'lon': clicked_lon}
        if 'data' in updated_figure and len(updated_figure['data']) > 0:
            updated_marker_colors = ['blue'] * len(df_sorted)
            for i, row in df_sorted.iterrows():
                if row['A Location'] == clicked_location_name:
                    updated_marker_colors[i] = 'red'
                    break
            updated_figure['data'][0]['marker']['color'] = updated_marker_colors

        # Reorder the cards to bring the selected one to the top
        selected_card = None
        other_cards = []
        for card in updated_cards:
            card_index = int(card['props']['id']['index'])
            if card_index == clicked_index:
                selected_card = card
            else:
                other_cards.append(card)
        if selected_card:
            updated_cards = [selected_card] + other_cards

    return updated_cards, updated_figure

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)