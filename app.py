import pandas as pd
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.express as px
from dash import callback_context
from datetime import datetime

# More Comprehensive Dummy Data
data = {
    'A Location': ['Dublin 1', 'Cork City', 'Galway Bay', 'Limerick郊外', 'Waterford Port', 'Sligo Town', 'Killarney National Park'],
    'B Energy Storage Capacity (MWh)': [20, 50, 15, 30, 40, 25, 10],
    'C Power (MWh)': [18, 45, 12, 28, 35, 22, 8],
    'Battery Manufacturer': ['LG Chem', 'Tesla', 'BYD', 'Samsung SDI', 'LG Chem', 'CATL', 'Tesla'],
    'Integrator': ['ESB', 'SSE Renewables', 'Gaelectric', 'Neoen', 'Statkraft', 'Bord na Móna', 'Enercon'],
    'Application': ['Grid Services', 'Commercial Backup', 'Renewable Integration', 'Industrial Use', 'Port Operations', 'Remote Power', 'Park Microgrid'],
    'Installation Location Characteristics': ['Urban Substation', 'Industrial Estate', 'Coastal Wind Farm', 'Manufacturing Plant', 'Harbor Facility', 'Rural Grid Edge', 'Protected Area'],
    'Enclosure Type': ['Containerized', 'Building Integration', 'Outdoor Rack', 'Containerized', 'Building Integration', 'Outdoor Rack', 'Containerized'],
    'Event data dd/mm/yyyy': ['15/03/2023', '28/11/2024', '05/07/2022', '10/01/2025', '22/09/2023', '18/05/2024', '01/04/2021'],
    'system age (yrs)': [2.5, 0.8, 4.1, 1.2, 3.0, 1.5, 5.2],
    'Cause ( a long description of likely cause of event)': [
        'Thermal runaway due to cell defect',
        'Overcharging caused by faulty BMS',
        'External fire spread to battery enclosure',
        'Internal short circuit triggered by mechanical stress',
        'Cooling system malfunction leading to overheating',
        'Arc fault in power conversion system',
        'Lightning strike affecting control electronics'
    ],
    'Extent of damage': ['Minor, contained within module', 'Significant, enclosure breached', 'Severe, system failure', 'Moderate, some modules affected', 'Limited, no major damage', 'Considerable, partial shutdown', 'Extensive, complete loss'],
    'State of Battery at time of Accident': ['Charging', 'Idle', 'Discharging', 'Charging', 'Standby', 'Discharging', 'Idle'],
    'Description of the event': [
        'Smoke detected in one battery module, automatic shutdown initiated.',
        'Loud explosion followed by fire, emergency responders on site.',
        'Vegetation fire spread to the battery container, causing thermal damage.',
        'Sudden power loss and internal sparking observed, system isolated.',
        'High temperature alarms triggered, cooling system found to be non-operational.',
        'Brief power surge followed by smoke and electrical smell.',
        'Control system failure after a nearby lightning strike, potential overvoltage.'
    ],
    'Source of information': ['Internal Monitoring System', 'Local News Report', 'Fire Brigade Report', 'Company Investigation', 'Maintenance Logs', 'Witness Account', 'Environmental Agency'],
    'Custom Location (Lat,Lon)': ['53.3498, -6.2603', '51.8968, -8.4863', '53.2707, -9.0569', '52.6692, -8.6301', '52.2617, -7.1135', '54.2705, -8.4842', '52.0533, -9.5067'],
    'Root Cause': ['Cell Defect', 'BMS Failure', 'External Fire', 'Mechanical Stress', 'Cooling Failure', 'Arc Fault', 'Lightning'],
    'Failed Element': ['Battery Module', 'Battery Management System', 'Enclosure', 'Internal Cell Connection', 'Cooling Pump', 'Power Inverter', 'Control Unit'],
    'Source URL 1': ['https://en.wikipedia.org/wiki/Battery_fire', 'https://www.nytimes.com/topic/subject/fires', 'https://www.theguardian.com/environment/renewable-energy', 'https://en.wikipedia.org/wiki/Explosion', 'https://www.irishtimes.com/news/environment', 'https://www.bbc.com/news/science_and_environment', 'https://en.wikipedia.org/wiki/Lightning'],
    'Source URL 2': ['https://www.safetyandhealthmagazine.com/topics/138-electrical-safety', 'https://www.nfpa.org/Public-Education/By-topic/Electrical-safety', 'https://www.wind-watch.org/news/2023/01/15/fire-at-a-battery-storage-site-in-australia/', 'https://www.hse.gov.uk/electricity/index.htm', 'https://www.marineinsight.com/ports-terminals/safety-in-ports-identifying-assessing-and-managing-risks/', 'https://www.gov.ie/en/policy-areas/energy/', 'https://www.met.ie/warnings/'],
    'Source URL 3': ['https://www.energy-storage.news/', 'https://www.reuters.com/news/archive/energy', 'https://cleantechnica.com/category/energy-storage/', 'https://electrek.co/category/energy-storage/', 'https://www.worldoil.com/news/2024/10/27/fire-at-lng-terminal-in-texas-forces-facility-shutdown/', 'https://www.independent.ie/climate-change/', 'https://www.nationalgeographic.com/environment/article/lightning-facts'],
}
df = pd.DataFrame(data)

# Function to extract latitude and longitude
def get_lat_lon(location_str):
    lat, lon = map(float, location_str.split(','))
    return lat, lon

# Apply the function to create separate lat and lon columns
df[['latitude', 'longitude']] = df['Custom Location (Lat,Lon)'].apply(get_lat_lon).tolist()

# Convert 'Event data' to datetime objects and extract year for sorting
df['event_datetime'] = pd.to_datetime(df['Event data dd/mm/yyyy'], format='%d/%m/%Y')
df_sorted = df.sort_values(by='event_datetime', ascending=False).reset_index(drop=True)

# Dash App Initialization
app = dash.Dash(__name__)

# Create card components
cards = [
    html.Div(
        [
            html.H6(f"{row['A Location']}", style={'fontFamily': 'Arial'}),
            html.P(f"Date: {row['Event data dd/mm/yyyy']}", style={'fontFamily': 'Arial'}),
            html.P(
                html.Span(f"{row['C Power (MWh)']}MW", style={'color': 'red', 'fontSize': '1.5em', 'fontFamily': 'Arial'})
            ),
            html.P(f"Cause: {row['Cause ( a long description of likely cause of event)']}", style={'fontFamily': 'Arial', 'fontSize': '0.9em'}),
            html.A(f"Read More", href=row['Source URL 1'], target="_blank", style={'fontFamily': 'Arial', 'fontSize': '0.8em'})
        ],
        className="incident-card",
        id={'type': 'card', 'index': str(index)}, # Changed ID to be the index as a string
        style={'fontFamily': 'Arial', 'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px'}
    )
    for index, row in df_sorted.iterrows()
]

# App Layout with cards and map
app.layout = html.Div([
    html.H1("Battery Energy Storage Incidents", style={'fontFamily': 'Arial'}),
    html.Div(cards, id="cards-container", className="card-container"),
    dcc.Graph(
        id='incident-map',
        figure=px.scatter_map(df_sorted,
                             lat="latitude",
                             lon="longitude",
                             hover_name="A Location",
                             zoom=4,
                             height=600,
                             center={'lat': df_sorted['latitude'].mean(), 'lon': df_sorted['longitude'].mean()}),
        config={'scrollZoom': True},
    ),
    # Hidden div to store the ID of the clicked card (optional)
    html.Div(id='clicked-card-id', style={'display': 'none'})
], style={'fontFamily': 'Arial'})

# Combined callback for map marker click and card click
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

    updated_cards = list(current_cards) # Create a mutable copy
    updated_figure = current_figure.copy()

    # Reset styles for all cards (except font)
    for i in range(len(updated_cards)):
        if 'style' in updated_cards[i]['props'] and 'fontFamily' in updated_cards[i]['props']['style']:
            updated_cards[i]['props']['style'] = {'fontFamily': 'Arial', 'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px'}
        elif 'style' in updated_cards[i]['props']:
            updated_cards[i]['props']['style'] = {'fontFamily': 'Arial', 'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px'}
        else:
            updated_cards[i]['props']['style'] = {'fontFamily': 'Arial', 'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px'}

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

        # Highlight the corresponding card and bring to top
        selected_card = None
        other_cards = []
        for i, card in enumerate(updated_cards):
            card_index = int(card['props']['id']['index'])
            if card_index == clicked_index:
                new_card = card.copy()
                new_card['props']['style'] = {'border': '2px solid red', 'zIndex': 1, 'fontFamily': 'Arial', 'marginBottom': '10px', 'padding': '10px'}
                selected_card = new_card
            else:
                new_card = card.copy()
                if 'style' not in new_card['props']:
                    new_card['props']['style'] = {'fontFamily': 'Arial', 'marginBottom': '10px', 'border': '1px solid #ddd', 'padding': '10px'}
                elif 'fontFamily' not in new_card['props']['style']:
                    new_card['props']['style']['fontFamily'] = 'Arial'
                other_cards.append(new_card)

        if selected_card:
            updated_cards = [selected_card] + other_cards

        # Update map center and marker color
        updated_figure['layout']['mapbox']['center'] = {'lat': clicked_lat, 'lon': clicked_lon}
        if 'data' in updated_figure and len(updated_figure['data']) > 0:
            updated_marker_colors = ['blue'] * len(df_sorted)
            for i, row in df_sorted.iterrows():
                if row['A Location'] == clicked_location_name:
                    updated_marker_colors[i] = 'red'
                    break
            updated_figure['data'][0]['marker']['color'] = updated_marker_colors

    return updated_cards, updated_figure

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)