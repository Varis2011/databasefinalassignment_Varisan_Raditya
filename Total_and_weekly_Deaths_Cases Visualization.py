import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
from urllib.request import urlopen
import json


total_cases = pd.read_csv("total_cases.csv")
total_deaths = pd.read_csv("total_deaths.csv")
weekly_cases = pd.read_csv("weekly_cases.csv")
weekly_deaths = pd.read_csv("weekly_deaths.csv")


with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
    world_map_data = json.load(response)


app = dash.Dash(__name__)


app.layout = html.Div([
    html.H1("COVID-19 Dashboard", style={'textAlign': 'center'}),

    dcc.RangeSlider(
        id='date-slider',
        marks={i: {'label': date} for i, date in enumerate(total_cases['date'].unique())},
        min=0,
        max=len(total_cases['date'].unique()) - 1,
        step=1,
        value=[0, len(total_cases['date'].unique()) - 1],
        tooltip={'placement': 'bottom'},
    ),

    html.Div([
        dcc.Graph(id='world-map'),
        html.Div(id='date-info', style={'margin-top': '20px'}),
    ], style={'width': '60%', 'display': 'inline-block'}),

    html.Div([
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': country, 'value': country} for country in total_cases.columns[2:]],
            multi=True,
            value=['World'],
        ),
        dcc.Graph(id='case-graph'),
        dcc.Graph(id='death-graph'),
    ], style={'width': '39%', 'display': 'inline-block', 'float': 'right'}),

    html.Div(id='world-cases-data', style={'display': 'none'}),
    html.Div(id='world-deaths-data', style={'display': 'none'}),

    html.Div([
        dcc.Graph(id='weekly-cases-graph'),
        dcc.Graph(id='weekly-deaths-graph'),
    ], style={'width': '60%', 'display': 'inline-block', 'margin-top': '20px'}),

    html.Div(id='weekly-cases-data', style={'display': 'none'}),
    html.Div(id='weekly-deaths-data', style={'display': 'none'})
])

@app.callback(
    [Output('world-map', 'figure'),
     Output('date-info', 'children'),
     Output('world-cases-data', 'children'),
     Output('world-deaths-data', 'children')],
    [Input('date-slider', 'value'),
     Input('country-dropdown', 'value')],
    [State('world-cases-data', 'children'),
     State('world-deaths-data', 'children')]
)
def update_map(selected_dates, selected_countries, world_cases_data_json, world_deaths_data_json):
    filtered_cases = total_cases[(total_cases['date'] >= total_cases['date'].unique()[selected_dates[0]]) &
                                 (total_cases['date'] <= total_cases['date'].unique()[selected_dates[1]])]

    date_info = f"Selected Date Range: {total_cases['date'].unique()[selected_dates[0]]} to {total_cases['date'].unique()[selected_dates[1]]}"

    if 'World' in selected_countries:
        fig = px.choropleth_mapbox(filtered_cases,
                                   geojson=world_map_data,
                                   locations='World',
                                   color='World',
                                   color_continuous_scale='Viridis',
                                   mapbox_style="carto-positron",
                                   zoom=2,
                                   opacity=0.5,
                                   center={'lat': 30, 'lon': 0})
    else:
        fig = px.choropleth_mapbox(filtered_cases.melt(id_vars=['date'], value_vars=selected_countries + ['World']),
                                   geojson=world_map_data,
                                   locations='variable',
                                   featureidkey="properties.name",
                                   color='value',
                                   color_continuous_scale='Viridis',
                                   mapbox_style="carto-positron",
                                   zoom=2,
                                   opacity=0.5,
                                   center={'lat': 30, 'lon': 0},
                                   labels={'value': 'Total Cases'})

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    world_cases_data = filtered_cases[['date', 'World']].to_dict(orient='records')
    world_cases_data_json = json.dumps(world_cases_data)

    world_deaths_data = total_deaths[['date', 'World']].to_dict(orient='records')
    world_deaths_data_json = json.dumps(world_deaths_data)

    return fig, date_info, world_cases_data_json, world_deaths_data_json

@app.callback(
    Output('case-graph', 'figure'),
    [Input('date-slider', 'value'),
     Input('country-dropdown', 'value'),
     Input('world-cases-data', 'children')]
)
def update_case_graph(selected_dates, selected_countries, world_cases_data_json):
    filtered_cases = total_cases[(total_cases['date'] >= total_cases['date'].unique()[selected_dates[0]]) &
                                 (total_cases['date'] <= total_cases['date'].unique()[selected_dates[1]])]

    world_cases_data = pd.read_json(world_cases_data_json)

    if 'World' in selected_countries:
        selected_countries.remove('World')  
        selected_countries.append('World') 

    fig = px.line(filtered_cases, x='date', y=selected_countries,
                  labels={'value': 'Total Cases'}, title='COVID-19 Cases Over Time')

    fig.add_trace(px.line(world_cases_data, x='date', y='World', line_dash_sequence=['dash']).data[0])

    return fig

@app.callback(
    Output('death-graph', 'figure'),
    [Input('date-slider', 'value'),
     Input('country-dropdown', 'value'),
     Input('world-deaths-data', 'children')]
)
def update_death_graph(selected_dates, selected_countries, world_deaths_data_json):
    filtered_deaths = total_deaths[(total_deaths['date'] >= total_deaths['date'].unique()[selected_dates[0]]) &
                                   (total_deaths['date'] <= total_deaths['date'].unique()[selected_dates[1]])]

    world_deaths_data = pd.read_json(world_deaths_data_json)

    if 'World' in selected_countries:
        selected_countries.remove('World')  
        selected_countries.append('World')  

    fig = px.line(filtered_deaths, x='date', y=selected_countries,
                  labels={'value': 'Total Deaths'}, title='COVID-19 Deaths Over Time')


    fig.add_trace(px.line(world_deaths_data, x='date', y='World', line_dash_sequence=['dash']).data[0])

    return fig

@app.callback(
    Output('weekly-cases-graph', 'figure'),
    [Input('date-slider', 'value'),
     Input('country-dropdown', 'value'),
     Input('weekly-cases-data', 'children')]
)
def update_weekly_cases_graph(selected_dates, selected_countries, weekly_cases_data_json):
    filtered_weekly_cases = weekly_cases[
        (weekly_cases['date'] >= weekly_cases['date'].unique()[selected_dates[0]]) &
        (weekly_cases['date'] <= weekly_cases['date'].unique()[selected_dates[1]])]

    if 'World' in selected_countries:
        selected_countries.remove('World')  
        selected_countries.append('World')  

    fig = px.line(filtered_weekly_cases, x='date', y=selected_countries,
                  labels={'value': 'Weekly Cases'}, title='COVID-19 Weekly Cases Over Time')

    fig.update_layout(height=300)

    return fig


@app.callback(
    Output('weekly-deaths-graph', 'figure'),
    [Input('date-slider', 'value'),
     Input('country-dropdown', 'value'),
     Input('weekly-deaths-data', 'children')]
)
def update_weekly_deaths_graph(selected_dates, selected_countries, weekly_deaths_data_json):
    filtered_weekly_deaths = weekly_deaths[
        (weekly_deaths['date'] >= weekly_deaths['date'].unique()[selected_dates[0]]) &
        (weekly_deaths['date'] <= weekly_deaths['date'].unique()[selected_dates[1]])]

    if 'World' in selected_countries:
        selected_countries.remove('World')  
        selected_countries.append('World')  

    fig = px.line(filtered_weekly_deaths, x='date', y=selected_countries,
                  labels={'value': 'Weekly Deaths'}, title='COVID-19 Weekly Deaths Over Time')

    fig.update_layout(height=300)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
