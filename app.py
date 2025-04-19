import pandas as pd
import dash
from dash import dcc
from dash import html
import plotly.express as px

# Dummy Data
data = {'incident': [1, 2, 3],
        'location': ['53.3498, -6.2603', '53.3550, -6.2700', '53.3400, -6.2550']}
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
            html.P(f"Location: {row['location']}")
        ],
        className="incident-card",  # Add a CSS class for styling later
        id=f"card-{row['incident']}" # Add a unique ID for potential callbacks
    )
    for index, row in df.iterrows()
]

# App Layout with cards and map
app.layout = html.Div([
    html.H1("Fire Incident MVP"),
    html.Div(cards, className="card-container"),  # Container for the cards
    dcc.Graph(
        id='incident-map',
        figure=px.scatter_map(df,
                                lat="latitude",
                                lon="longitude",
                                hover_name="incident",
                                zoom=10,
                                height=600,
                                center={'lat': df['latitude'].mean(), 'lon': df['longitude'].mean()}),
        config={'scrollZoom': True}
    )
])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)