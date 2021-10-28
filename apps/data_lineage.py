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
from apps.typesense_client import *

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('data_lineage')

# Object declaration
basic_elements = [
    {
        'data': {'id': 'one', 'label': 'Version 1'},
        'position': {'x': 50, 'y': 50},
        'classes':'api',
    },
    {
        'data': {'id': 'two', 'label': 'Version 2'},
        'position': {'x': 200, 'y': 200},
        'classes':'api',
    },
    {
        'data': {
            'id': 'one-five',
            'source': 'one',
            'target': 'five',
            'label': 'Edge from Version 1 to Version 5',
            'extra_data': 'hello'
        }
    }
]

styles = {
    'json-output': {
        'overflow-y': 'scroll',
        'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
    'tab': {'height': 'calc(98vh - 115px)'}
}


# Creating styles
stylesheet = [
    # Node
    {
        'selector': 'node',
        'style': {
            'label': 'data(id)',
            'background-color': 'white',
        }
    },
    # Edge
    {
        'selector': 'edge',
        'style': {
            'label': 'data(id)',
            'source-arrow-shape': 'triangle',
        }
    },
    # API Node
    {
        'selector': '.api',
        'style': {
            'width': 25,
            'height': 25,
            'background-fit': 'cover',
            'background-image': "/assets/static/api.png"
        }
    },
    # CSV Node
    {
        'selector': '.csv',
        'style': {
            'width': 25,
            'height': 25,
            'background-fit': 'cover',
            'background-image': "/assets/static/csv.png"
        }
    },
    # JSON Node
    {
        'selector': '.json',
        'style': {
            'width': 25,
            'height': 25,
            'background-fit': 'cover',
            'background-image': "/assets/static/json.JPG"
        }
    },

    # BLOB Node
    {
        'selector': '.blob',
        'style': {
            'width': 30,
            'height': 30,
            'background-fit': 'cover',
            'background-image': "/assets/static/database.png"
        }
    },
]

# Action Dropdown Options
option_list = []
# [ for nav in sidebar_2_list]
dropdown_merge_strategy = dbc.DropdownMenu(label='Merge Strategy', children=[
        dbc.DropdownMenuItem("First"),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem("Second"),
], direction='end')

for nav in sidebar_2_list:
    if nav['label'] == 'Merge Strategy':
        option_list.append(dbc.DropdownMenuItem(dropdown_merge_strategy, id=id(nav['label'])))
    else:
        option_list.append(dbc.DropdownMenuItem(nav['label'], id=id(nav['label'])))


layout = html.Div([
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    dcc.Store(id='isUploadAPI', storage_type='memory'),
    dcc.Interval(id=id('interval'), interval=1000, n_intervals=0),

    html.Div([
        # dbc.Row(dbc.Col(html.H1('Data Explorer')), style={'text-align':'center'}),

        dbc.Row([
            dbc.Col([
                html.H1('Data Lineage (Data Flow Experiments)', style={'text-align':'center'}),

                dbc.Col(dbc.DropdownMenu(option_list, label="Action", style={'float':'left', 'width': '200px'}), width={"size": 2, "order": "1"}),
    
                dbc.Col(html.Button('Modify Profile', id=id('modify_profile'), className='btn btn-warning btn-lg'), style={'float':'right', 'margin-right':'3px'}), 
                dbc.Col(html.Button('Remove Node', id=id('remove_node'), className='btn btn-danger btn-lg'), style={'float':'right', 'margin-right':'3px'}),
                dbc.Col(html.Button('Inspect', id=id('inspect'), className='btn btn-info btn-lg'), style={'float':'right', 'margin-right':'3px'}), 
                dbc.Col(html.Button('Add API', id=id('button_add_api'), className='btn btn-success btn-lg'), style={'float':'right', 'margin-right':'3px'}), 
                # html.Button('Merge Versions', id('button_merge'), className='btn btn-warning btn-lg', style={'margin-right':'3px'}),
                # html.Button('Remove Version', id('button_remove'), className='btn btn-danger btn-lg', style={'margin-right':'3px'}),

                dbc.Col(html.H5('Selected(temporary): None', id=id('selected_version')), style={'text-align':'center', 'background-color': 'silver'}),
                cyto.Cytoscape(id=id('data_explorer'), elements=[], 
                                layout={'name': 'preset'},
                                style={'height': '1000px','width': '100%'},
                                stylesheet=stylesheet)
            ], width=9),

            dbc.Col([
                html.Div([
                    html.H5('Experiments', style={'text-align':'center'}),
                    html.Div(id=id('experiments')),
                    
                ]),
                # dcc.Tabs(id='tabs', children=[
                #     dcc.Tab(label='Data', children=[
                #         html.Div(style=styles['tab'], children=[
                #             html.Pre(id=id('data_output'),style={'overflow-y': 'scroll', 'height':'95%'}),
                #         ])
                #     ], id=id('tab_1')),

                #     dcc.Tab(label='Profile', children=[
                #         html.Div(style=styles['tab'], children=[
                #             html.P('Data'),
                #             html.Pre(id=id('profile_output'),style={'overflow-y': 'scroll', 'height':'95%'}),
                #         ])
                #     ]),
                # ]),

            ], width=3),
        ]),
    ], style={'width':'100%'}),
])


@app.callback(Output(id('data_explorer'), 'elements'), 
                Input(id('interval'), 'n_intervals'),
                State('current_dataset', 'data'))
def generate_cytoscape(n_intervals, dataset_id):
    if dataset_id is None or dataset_id == '': return no_update
    dataset = get_document('dataset', dataset_id)
    # print('start NODE', n_intervals)
    # pprint(dataset['cytoscape_node'])
    # print('start EDGE')
    # pprint(dataset['cytoscape_edge'])
    return (dataset['cytoscape_node'] + dataset['cytoscape_edge'])


# @app.callback(Output(id('experiments'), 'children'),
#                 Input('url', 'pathname'),
#                 State('current_dataset', 'data'))
# def generate_experiments(pathname, dataset_id):
#     if dataset_id is None or dataset_id == '': return no_update
#     dataset = get_document('dataset', dataset_id)

#     return [dbc.Card(children=(dbc.CardHeader(experiment['name']), dbc.CardBody(experiment['description'])), color="info", inverse=True) for experiment in dataset['experiment']]


# Select API
@app.callback(Output('display_current_node', 'value'), 
                Input(id('data_explorer'), 'tapNodeData'))
def add_api(tapNodeData):
    if tapNodeData is None: return no_update
    pprint(tapNodeData)
    return no_update

# Add API
@app.callback(Output('url', 'pathname'),
                Input(id('button_add_api'), 'n_clicks'))
def add_api(n_clicks):
    if n_clicks is None: return no_update
    return '/apps/upload/step=2'


# Load, Add, Delete, Merge
# @app.callback(Output(id('data_explorer'), 'elements'), 
#                 [Input('url', 'pathname'),
#                 Input(id('button_add_api'), 'n_clicks'), 
#                 State(id('data_explorer'), 'tapNodeData'),
#                 State(id('data_explorer'), 'elements'),
#                 State('dataset_metadata', 'data'),])
# def add_version(pathname, n_clicks, tapNodeData, elements, metadata):
#     triggered = callback_context.triggered[0]['prop_id']

#      # On Page Load
#     if triggered == '.':
#         data = []
#         # for api in metadata['api']:
#         #     pass
       
#     if n_clicks is None: return no_update
#     if tapNodeData is None: return no_update

#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

#     if triggered == id('button_add_api'):
#         new_version_id = str(len(elements)//2)
#         elements += [
#             {
#             'data': {'id': new_version_id, 'label': 'Version '+str(new_version_id)},
#             # 'position': {'x': 150, 'y': 150}
#             },
#             {
#                 'data': {
#                     'id': tapNodeData['id'] + '_' + new_version_id,
#                     'source': tapNodeData['id'],
#                     'target': new_version_id,
#                     'label': 'Edge from ' + str(tapNodeData['id']) + ' to ' + str(new_version_id)
#                 },
#                 # 'classes': 'blob'
#             }
#         ]
#     elif triggered == id('button_remove'):
#         pass

#     return elements



# # Display Selected Version Name
# @app.callback(Output(id('selected_version'), 'children'), 
#                 Input(id('data_explorer'), 'selectedNodeData'))
# def display_selected_version(selected_node_list):
#     if selected_node_list is None or len(selected_node_list) == 0: return 'Selected: None'
#     node_list = [node['label'] for node in selected_node_list]
#     return 'Selected(temporary): ' + ', '.join(node_list)


# # Display Version Data & Difference
# @app.callback(Output(id('tab_1'), 'label'),
#                 Output(id('data_output'), 'children'),
#                 [Input(id('data_explorer'), 'tapNodeData'),
#                 Input(id('data_explorer'), 'selectedNodeData'),
#                 Input(id('data_explorer'), 'tapEdgeData')])
# def displayTapNode(node_data, selectedNodeData, edge_data):
#     triggered = callback_context.triggered[0]['prop_id']
#     if triggered == '.': return no_update
#     triggered = triggered.rsplit('.', 1)[1]

#     if triggered == 'tapNodeData':
#         label = 'Version Data'
#         data = node_data

#     elif triggered == 'selectedNodeData':
#         label = '?'
#         data = selectedNodeData

#     elif triggered == 'tapEdgeData':
#         label = 'Difference'
#         data = edge_data

#     print(triggered)

#     return triggered, json.dumps(data, indent=2)


# @app.callback(Output(id('profile_output'), 'children'),
#               [Input(id('data_explorer'), 'tapNodeData')])
# def displayTapNodeData(data):
#     return json.dumps(data, indent=2)