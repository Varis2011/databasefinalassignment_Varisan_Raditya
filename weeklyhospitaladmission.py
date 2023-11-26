import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from urllib.request import urlopen
import json


weekly_hospital_admissions = pd.read_csv("weekly-hospital-admissions-covid.csv")

with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
    world_map_data = json.load(response)


app = dash.Dash(__name__)


app.layout = html.Div([
    html.H1("Weekly Hospital Admissions for COVID-19", style={'textAlign': 'center'}),

    html.Div([
        dcc.Dropdown(
            id='country-dropdown-hospital',
            options=[{'label': country, 'value': country} for country in weekly_hospital_admissions['Entity'].unique()],
            multi=True,
            value=['World'],
        ),
        dcc.Graph(id='hospital-admissions-graph'),
    ], style={'width': '80%', 'margin': 'auto'}),

])


@app.callback(
    Output('hospital-admissions-graph', 'figure'),
    [Input('country-dropdown-hospital', 'value')]
)
def update_hospital_admissions_graph(selected_countries):
    if 'World' in selected_countries:
        selected_countries.remove('World')  
        selected_countries.append('World') 

    filtered_data = weekly_hospital_admissions[weekly_hospital_admissions['Entity'].isin(selected_countries)]

    fig = px.line(filtered_data, x='Day', y='Weekly new hospital admissions',
                  color='Entity', labels={'Weekly new hospital admissions': 'Weekly Admissions'},
                  title='Weekly Hospital Admissions for COVID-19')

    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
