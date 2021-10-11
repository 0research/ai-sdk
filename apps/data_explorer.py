from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
from dash import dash_table
from dash import no_update, callback_context
import json
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from pandas.io.json import json_normalize
from itertools import zip_longest
from datetime import datetime
import dash_cytoscape as cyto

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('data_explorer')

# Object declaration
basic_elements = [
    {
        'data': {'id': 'one', 'label': 'Dataset 1'},
        'position': {'x': 50, 'y': 50}
    },
    {
        'data': {'id': 'two', 'label': 'Dataset 2'},
        'position': {'x': 200, 'y': 200}
    },
    {
        'data': {'id': 'three', 'label': 'Dataset 3'},
        'position': {'x': 100, 'y': 150}
    },
    {
        'data': {'id': 'four', 'label': 'Dataset 4'},
        'position': {'x': 400, 'y': 50}
    },
    {
        'data': {'id': 'five', 'label': 'Dataset 5'},
        'position': {'x': 250, 'y': 100}
    },
    {
        'data': {'id': 'six', 'label': 'Dataset 6', 'parent': 'three'},
        'position': {'x': 150, 'y': 150}
    },
    {
        'data': {
            'id': 'one-two',
            'source': 'one',
            'target': 'two',
            'label': 'Edge from Dataset1 to Dataset2'
        }
    },
    {
        'data': {
            'id': 'one-five',
            'source': 'one',
            'target': 'five',
            'label': 'Edge from Dataset 1 to Dataset 5'
        }
    },
    {
        'data': {
            'id': 'two-four',
            'source': 'two',
            'target': 'four',
            'label': 'Edge from Dataset 2 to Dataset 4'
        }
    },
    {
        'data': {
            'id': 'three-five',
            'source': 'three',
            'target': 'five',
            'label': 'Edge from Dataset 3 to Dataset 5'
        }
    },
    {
        'data': {
            'id': 'three-two',
            'source': 'three',
            'target': 'two',
            'label': 'Edge from Dataset 3 to Dataset 2'
        }
    },
    {
        'data': {
            'id': 'four-four',
            'source': 'four',
            'target': 'four',
            'label': 'Edge from Dataset 4 to Dataset 4'
        }
    },
    {
        'data': {
            'id': 'four-six',
            'source': 'four',
            'target': 'six',
            'label': 'Edge from Dataset 4 to Dataset 6'
        }
    },
    {
        'data': {
            'id': 'five-one',
            'source': 'five',
            'target': 'one',
            'label': 'Edge from Dataset 5 to Dataset 1'
        }
    },
]

styles = {
    'json-output': {
        'overflow-y': 'scroll',
        'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
    'tab': {'height': 'calc(98vh - 115px)'}
}


tab_labels = ['About', 'Sample Data']
tab_values = [id('about'), id('sample_data')]


layout = html.Div([

    html.Div([
        dbc.Row(dbc.Col(html.H1('Data Explorer')), style={'text-align':'center'}),

        dbc.Row([
            dbc.Col([
                html.Button('Add Dataset', id('add_node')), 
                html.Button('Remove Dataset', id('remove_node')),
                cyto.Cytoscape(id=id('data_explorer'), elements=basic_elements, 
                                layout={'name': 'preset'},
                                style={'height': '1000px','width': '100%'})
            ], width=8),

            dbc.Col([
                dcc.Tabs(id='tabs', children=[
                    dcc.Tab(label='About', children=[
                        html.Div(style=styles['tab'], children=[
                            html.P('Columns'),
                            html.Pre(id='tap-node-json-output',style=styles['json-output']),
                            html.P('Difference'),
                            html.Pre(id='tap-edge-json-output', style=styles['json-output'])
                        ])
                    ]),

                    dcc.Tab(label='Sample Data', children=[
                        html.Div(style=styles['tab'], children=[
                            html.P('Data'),
                            html.Pre(id='tap-node-data-json-output',style={'overflow-y': 'scroll', 'height':'95%'}),
                        ])
                    ]),
                ]),
            ], width=4),
        ]),
    ], style={'width':'100%'}),
])


@app.callback(Output('tap-node-json-output', 'children'),
              [Input(id('data_explorer'), 'tapNode')])
def displayTapNode(data):
    return json.dumps(data, indent=2)


@app.callback(Output('tap-edge-json-output', 'children'),
              [Input(id('data_explorer'), 'tapEdge')])
def displayTapEdge(data):
    return json.dumps(data, indent=2)


@app.callback(Output('tap-node-data-json-output', 'children'),
              [Input(id('data_explorer'), 'tapNodeData')])
def displayTapNodeData(data):
    return json.dumps(data, indent=2)


@app.callback(Output(id('data_explorer'), 'elements'), 
            [Input(id('add_node'), 'n_clicks'), 
            State(id('data_explorer'), 'tapNodeData'),
            State(id('data_explorer'), 'elements'),
            ])
def add_node(n_clicks, tapNodeData, elements):
    if n_clicks is None: return no_update
    pprint(tapNodeData['id'])
    # pprint(elements)
    elements += [
        {
        'data': {'id': 'seven', 'label': 'Node 7'},
        'position': {'x': 150, 'y': 150}
        },
        {
            'data': {
                'id': tapNodeData['id'] + '-' + 'seven',
                'source': tapNodeData['id'],
                'target': 'seven',
                'label': 'Edge from Node1 to Node2'
            }
        }
    ]
    return elements