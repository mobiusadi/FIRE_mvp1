import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.express as px
from dash import callback_context

# Dummy Data
data = {'incident': [1, 2, 3],
        'location': ['53.3498, -6.2603', '53.3550, -6.2700', '53.3400, -6.2550'],
        'description': ['Minor fire in residential area', 'Commercial building smoke alarm', 'Brush fire near park']}
df = pd.DataFrame(data)

# Function to extract latitude and longitude
def get_lat_lon(location_str):
    lat, lon = map(float, location_str.split(','))
    return lat, lon

# Apply the function to create separate lat and lon columns
df[['latitude', 'longitude']] = df['location'].apply(get_lat_lon).tolist()

# Dash App Initialization
app = dash.Dash(__name__)

# Create card components
cards = [
    html.Div(
        [
            html.H6(f"Incident: {row['incident']}"),
            html.P(f"Description: {row['description']}"),
            html.P(f"Location: {row['location']}")
        ],
        className="incident-card",
        id={'type': 'card', 'index': f"card-{row['incident']}"}
    )
    for index, row in df.iterrows()
]

# App Layout with cards and map
app.layout = html.Div([
    html.H1("Fire Incident MVP"),
    html.Div(cards, id="cards-container", className="card-container"),
    dcc.Graph(
        id='incident-map',
        figure=px.scatter_map(df,
                             lat="latitude",
                             lon="longitude",
                             hover_name="incident",
                             zoom=10,
                             height=600,
                             center={'lat': df['latitude'].mean(), 'lon': df['longitude'].mean()}),
        config={'scrollZoom': True},
    ),
    # Hidden div to store the ID of the clicked card (optional)
    html.Div(id='clicked-card-id', style={'display': 'none'})
])

# Combined callback for map marker 
# 
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
    print(f"Triggered ID: {triggered_id}")

    updated_cards = list(current_cards) # Create a mutable copy
    updated_figure = current_figure.copy()

    # Reset styles for all cards
    for i in range(len(updated_cards)):
        if 'style' in updated_cards[i]['props']:
            del updated_cards[i]['props']['style']

    # Reset marker colors on the map
    if 'data' in updated_figure and len(updated_figure['data']) > 0 and 'marker' in updated_figure['data'][0]:
        updated_figure['data'][0]['marker']['color'] = ['blue'] * len(df) # Default color

    clicked_incident_num = None
    clicked_lat = None
    clicked_lon = None

    if triggered_id == 'incident-map' and map_click_data:
        clicked_incident_str = map_click_data['points'][0]['hovertext']
        clicked_incident_num = int(clicked_incident_str)
    elif isinstance(triggered_id, dict) and triggered_id['type'] == 'card' and card_clicks:
        valid_clicks = [c for c in card_clicks if c is not None]
        if valid_clicks:
            clicked_card_index = card_clicks.index(max(valid_clicks))
            clicked_card_id_str = card_ids[clicked_card_index]['index']
            clicked_incident_num = int(clicked_card_id_str.split('-')[1])
            print(f"Clicked Incident Num (from card): {clicked_incident_num}")

    if clicked_incident_num is not None:
        # Find the coordinates of the clicked incident
        clicked_row = df[df['incident'] == clicked_incident_num].iloc[0]
        clicked_lat = clicked_row['latitude']
        clicked_lon = clicked_row['longitude']

        # Highlight the corresponding card
        for i, card in enumerate(updated_cards):
            card_id_dict = card['props']['id']
            card_incident_num = int(card_id_dict['index'].split('-')[1])
            if card_incident_num == clicked_incident_num:
                updated_cards[i]['props']['style'] = {'border': '2px solid red', 'zIndex': 1}

        # Update map center and marker color
        updated_figure['layout']['mapbox']['center'] = {'lat': clicked_lat, 'lon': clicked_lon}
        if 'data' in updated_figure and len(updated_figure['data']) > 0:
            updated_figure['data'][0]['marker']['color'] = ['red' if name == str(clicked_incident_num) else 'blue' for name in updated_figure['data'][0]['hovertext']]

    return updated_cards, updated_figure

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)