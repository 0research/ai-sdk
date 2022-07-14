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



event = {"event": "contextmenu", "props": ["target"]}

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
    html.Div('', id="log")

])



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


