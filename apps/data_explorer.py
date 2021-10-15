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
from pandas import json_normalize
from itertools import zip_longest
from datetime import datetime
import dash_cytoscape as cyto

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('data_explorer')

# Object declaration
basic_elements = [
    {
        'data': {'id': 'one', 'label': 'Table 1'},
        'position': {'x': 50, 'y': 50}
    },
    {
        'data': {'id': 'two', 'label': 'Table 2'},
        'position': {'x': 200, 'y': 200}
    },
    {
        'data': {'id': 'three', 'label': 'Table 3'},
        'position': {'x': 100, 'y': 150}
    },
    {
        'data': {'id': 'four', 'label': 'Table 4'},
        'position': {'x': 400, 'y': 50}
    },
    {
        'data': {'id': 'five', 'label': 'Table 5'},
        'position': {'x': 250, 'y': 100}
    },
    {
        'data': {'id': 'six', 'label': 'Table 6', 'parent': 'three'},
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
            'label': 'Edge from Table 1 to Table 5',
            'extra_data': 'hello'
        }
    },
    {
        'data': {
            'id': 'two-four',
            'source': 'two',
            'target': 'four',
            'label': 'Edge from Table 2 to Table 4'
        }
    },
    {
        'data': {
            'id': 'three-five',
            'source': 'three',
            'target': 'five',
            'label': 'Edge from Table 3 to Table 5'
        }
    },
    {
        'data': {
            'id': 'three-two',
            'source': 'three',
            'target': 'two',
            'label': 'Edge from Table 3 to Table 2'
        }
    },
    {
        'data': {
            'id': 'four-four',
            'source': 'four',
            'target': 'four',
            'label': 'Edge from Table 4 to Table 4'
        }
    },
    {
        'data': {
            'id': 'four-six',
            'source': 'four',
            'target': 'six',
            'label': 'Edge from Table 4 to Table 6'
        }
    },
    {
        'data': {
            'id': 'five-one',
            'source': 'five',
            'target': 'one',
            'label': 'Edge from Table 5 to Table 1'
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



layout = html.Div([
    html.Div([
        # dbc.Row(dbc.Col(html.H1('Data Explorer')), style={'text-align':'center'}),

        dbc.Row([
            dbc.Col([
                html.H1('Data Lineage (Experiments)', style={'text-align':'center'}),
                html.Button('Add Table', id('button_add'), className='btn btn-primary btn-lg', style={'margin-right':'3px'}), 
                html.Button('Merge Tables', id('button_merge'), className='btn btn-warning btn-lg', style={'margin-right':'3px'}),
                html.Button('Remove Table', id('button_remove'), className='btn btn-danger btn-lg', style={'margin-right':'3px'}),
                html.H5('Selected: None', id=id('selected_table'), style={'text-align':'center', 'background-color': 'silver'}),
                cyto.Cytoscape(id=id('data_explorer'), elements=basic_elements, 
                                layout={'name': 'preset'},
                                style={'height': '1000px','width': '100%'})
            ], width=8),

            dbc.Col([
                dcc.Tabs(id='tabs', children=[
                    dcc.Tab(label='Data', children=[
                        html.Div(style=styles['tab'], children=[
                            html.Pre(id=id('data_output'),style={'overflow-y': 'scroll', 'height':'95%'}),
                        ])
                    ], id=id('tab_1')),

                    dcc.Tab(label='Profile', children=[
                        html.Div(style=styles['tab'], children=[
                            html.P('Data'),
                            html.Pre(id=id('profile_output'),style={'overflow-y': 'scroll', 'height':'95%'}),
                        ])
                    ]),
                ]),

            ], width=4),
        ]),
    ], style={'width':'100%'}),
])


# Display Selected Table Name
@app.callback(Output(id('selected_table'), 'children'), 
                Input(id('data_explorer'), 'selectedNodeData'))
def display_selected_table(selected_node_list):
    if selected_node_list is None or len(selected_node_list) == 0: return 'Selected: None'
    node_list = [node['label'] for node in selected_node_list]
    return 'Selected: ' + ', '.join(node_list)


# Display Table Data & Difference
@app.callback(Output(id('tab_1'), 'label'),
                Output(id('data_output'), 'children'),
                [Input(id('data_explorer'), 'tapNodeData'),
                Input(id('data_explorer'), 'selectedNodeData'),
                Input(id('data_explorer'), 'tapEdgeData')])
def displayTapNode(node_data, selectedNodeData, edge_data):
    triggered = callback_context.triggered[0]['prop_id']
    if triggered == '.': return no_update
    triggered = triggered.rsplit('.', 1)[1]

    if triggered == 'tapNodeData':
        label = 'Table Data'
        data = node_data

    elif triggered == 'selectedNodeData':
        label = '?'
        data = selectedNodeData

    elif triggered == 'tapEdgeData':
        label = 'Difference'
        data = edge_data

    print(triggered)

    return triggered, json.dumps(data, indent=2)


# @app.callback(Output(id('profile_output'), 'children'),
#               [Input(id('data_explorer'), 'tapNodeData')])
# def displayTapNodeData(data):
#     return json.dumps(data, indent=2)





# Add & TODO Delete & Merge Tables
@app.callback(Output(id('data_explorer'), 'elements'), 
                [Input(id('button_add'), 'n_clicks'), 
                State(id('data_explorer'), 'tapNodeData'),
                State(id('data_explorer'), 'elements'),
                ])
def add_table(n_clicks, tapNodeData, elements):
    if n_clicks is None: return no_update
    if tapNodeData is None: return no_update

    # triggered = callback_context.triggered[0]['prop_id']
    # if triggered == '.': return no_update
    # triggered = triggered.rsplit('.', 1)[1]

    new_table_id = str(len(elements)//2)
    elements += [
        {
        'data': {'id': new_table_id, 'label': 'Table '+str(new_table_id)},
        # 'position': {'x': 150, 'y': 150}
        },
        {
            'data': {
                'id': tapNodeData['id'] + '_' + new_table_id,
                'source': tapNodeData['id'],
                'target': new_table_id,
                'label': 'Edge from ' + str(tapNodeData['id']) + ' to ' + str(new_table_id)
            }
        }
    ]
    return elements


