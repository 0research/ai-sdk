import pandas as pd
import dash_bootstrap_components as dbc
import json
from app import app
import dash_cytoscape as cyto
from dash import Dash, no_update, html, Input, Output, dash_table
from dash.exceptions import PreventUpdate
from dash_extensions import EventListener
from collections import OrderedDict
from apps.util import *
import plotly.graph_objects as go
from dash_extensions.enrich import Trigger

event = {"event": "contextmenu", "props": ["target"]}



df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2014_usa_states.csv')
fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[df.Rank, df.State, df.Postal, df.Population],
                fill_color='lavender',
                align='left'))
    ])

layout = html.Div([

    

    EventListener(
        cyto.Cytoscape(
            id='cytoscape',
            layout={'name': 'preset'},
            style={'width': '100%', 'height': '400px'},
            elements=[
                {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
                {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}, 'classes':'selected'},
                {'data': {'source': 'one', 'target': 'two'}}
            ],
            stylesheet= [{
                'selector': '.selected',
                'style': {
                    'background-color': '#000000',
                }
            }],
        ),
        events=[event], logging=True, id="el"
    ),
    html.Div('', id="log"),

    

    
    dcc.Graph(figure=fig, id='datatable1'),
    html.Button('button', id='button')
])

@app.callback(
    Trigger('button', 'n_clicks'),
    State('datatable1', 'figure'),
)
def test(figure):
    pprint(figure['data'][0]['header'])


app.clientside_callback(
    """
    function(n_events, e) {
        console.log('eeeeeee')
        console.log(e)
        return JSON.stringify(e)
    }
    """,
    Output("log", "children"),
    Input("el", "n_events"),
    State("el", "event"),
    prevent_initial_call=True
)
def click_event(n_events, e):
    if e is None:
        raise PreventUpdate()
    return ",".join(f"{prop} is '{e[prop]}' " for prop in event["props"]) + f" (number of clicks is {n_events})"


