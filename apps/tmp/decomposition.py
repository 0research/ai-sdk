from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
from app import app
import collections
import json
from pprint import pprint
from jsondiff import diff
from dash import no_update
from apps.util import *
from app import dbc



layout = html.Div([
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    html.H1('Decomposition', style={"textAlign": "center"}),
    
    html.P([], id='output'),
    dbc.Button('button1', id="b1"),
    dbc.Button('button2', id='b2'),

    dbc.Button('print', id='print'),
])


@app.callback(Output('output', 'children'), 
                Input('b1', 'n_clicks'),
                prevent_initial_call=True)
def button1(n_clicks):
    if n_clicks is None: return no_update
    store_session('project_id', '1')
    return ''


@app.callback(Output('output', 'children'), 
                Input('b2', 'n_clicks'),
                prevent_initial_call=True)
def button2(n_clicks):
    if n_clicks is None: return no_update
    store_session('project_id', '2')
    return ''


@app.callback(Output('output', 'children'), 
                Input('print', 'n_clicks'),
                prevent_initial_call=True)
def button2(n_clicks):
    if n_clicks is None: return no_update
    print(get_session('project'))
    return ''