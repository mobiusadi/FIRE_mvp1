import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.express as px
from dash import callback_context

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

# Convert 'Event data' to datetime objects and extract year
df['event_datetime'] = pd.to_datetime(df['Event data dd/mm/yyyy'], format='%d/%m/%Y')
df['year'] = df['event_datetime'].dt.year.astype('Int64')

app = dash.Dash(__name__)

app.layout = html.Div(
    style={'display': 'flex', 'flexDirection': 'column', 'height': '100vh', 'fontFamily': 'Arial', 'padding': '20px'},
    children=[
        html.Div(
            style={'marginBottom': '20px', 'display': 'flex', 'flexDirection': 'row', 'gap': '20px'},
            children=[
                html.Div(
                    children=[
                        html.H3("Sort by Power:"),
                        dcc.Dropdown(
                            id='power-sort-dropdown',
                            options=[
                                {'label': 'Power (High to Low)', 'value': 'power_desc'},
                                {'label': 'Power (Low to High)', 'value': 'power_asc'}
                            ],
                            value=None,
                            placeholder="Select Power Sort Order"
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.H3("Filter by Year:"),
                        dcc.Dropdown(
                            id='year-filter-dropdown',
                            options=[{'label': str(int(year)), 'value': int(year)} for year in sorted(df['year'].dropna().unique())],
                            value=None,
                            multi=True,
                            placeholder="Select Year(s)"
                        ),
                    ]
                ),
            ]
        ),
         html.Div(
            style={'display': 'flex', 'flexDirection': 'row', 'flexGrow': 1},
            children=[
                html.Div(
                    id="cards-container",
                    style={
                        'flex': '0 0 40%',
                        'overflowY': 'auto',
                        'paddingRight': '20px'
                    }
                ),
                html.Div(
                    dcc.Graph(
                        id='incident-map',
                        style={'flex': '1 1 auto', 'height': 'calc(100vh - 120px)', 'width': '100%'},
                        config={'scrollZoom': True}
                    ),
                    style={'width': '100%', 'height': '100%'} # Added style to the container div
                )
            ]
        ),
    ]
)

@app.callback(
    Output('cards-container', 'children'),
    Output('incident-map', 'figure'),
    Input('power-sort-dropdown', 'value'),
    Input('year-filter-dropdown', 'value')
)
def update_content(power_sort, selected_years):
    dff = df.copy().dropna(subset=['latitude', 'longitude'])

    # Filter by year
    if selected_years:
        dff = dff[dff['year'].isin(selected_years)]

    # Sort by power
    if power_sort == 'power_desc':
        dff = dff.sort_values(by='C Power (MWh)', ascending=False)
    elif power_sort == 'power_asc':
        dff = dff.sort_values(by='C Power (MWh)', ascending=True)

    df_sorted = dff.reset_index(drop=True)

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
                  if col not in ['latitude', 'longitude', 'event_datetime', 'year', 'A Location',
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

    fig = px.scatter_map(df_sorted,
                         lat="latitude",
                         lon="longitude",
                         hover_name="A Location",
                         size="C Power (MWh)",
                         size_max=30,
                         zoom=4,
                         height=600,
                         center={'lat': df_sorted['latitude'].mean(), 'lon': df_sorted['longitude'].mean()})

    return cards, fig
@app.callback(
    Output('cards-container', 'children', allow_duplicate=True),
    Output('incident-map', 'figure', allow_duplicate=True),
    Input('incident-map', 'clickData'),
    Input({'type': 'card', 'index': dash.ALL}, 'n_clicks'),
    State('power-sort-dropdown', 'value'),
    State('year-filter-dropdown', 'value'),
    State('cards-container', 'children'),
    State('incident-map', 'figure'),
    State({'type': 'card', 'index': dash.ALL}, 'id'),
    prevent_initial_call=True
)
def update_on_click(map_click_data, card_clicks, power_sort, selected_years, current_cards, current_figure, card_ids):
    dff = df.copy().dropna(subset=['latitude', 'longitude'])

    # Apply current filters and sorting
    if selected_years:
        dff = dff[dff['year'].isin(selected_years)]
    if power_sort == 'power_desc':
        dff = dff.sort_values(by='C Power (MWh)', ascending=False)
    elif power_sort == 'power_asc':
        dff = dff.sort_values(by='C Power (MWh)', ascending=True)

    df_sorted = dff.reset_index(drop=True)

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