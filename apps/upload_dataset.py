from dash import dcc, html, dash_table, no_update, callback_context
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
import json
import io
import sys
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from itertools import zip_longest
from datetime import datetime
from pandas import json_normalize
from pathlib import Path
from apps.typesense_client import *
import time
import ast
from pathlib import Path
import uuid


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('upload')
datatype_list = ['object', 'Int64', 'float64', 'bool', 'datetime64', 'category']

dataset_type = [
    {'label': 'Categorical', 'value': 'categorical'},
    {'label': 'Time Series', 'value': 'time_series'},
    {'label': 'Hybrid', 'value': 'hybrid'},
    {'label': 'Geo Spatial', 'value': 'geo_spatial'},
]
option_delimiter = [
    {'label': 'Comma (,)', 'value': ','},
    {'label': 'Tab', 'value': "\\t"},
    {'label': 'Space', 'value': "\\s+"},
    {'label': 'Pipe (|)', 'value': '|'},
    {'label': 'Semi-Colon (;)', 'value': ';'},
    {'label': 'Colon (:)', 'value': ':'},
]


# Layout
layout = html.Div([
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    dcc.Store(id='isUploadAPI', storage_type='memory'),

    dbc.Container([
        dbc.Row(dbc.Col(html.H2('Create or Load Existing Dataset')), style={'text-align':'center'}),
        dbc.Row([
            dbc.Col([
                dbc.Input(id=id('input_dataset_name'), placeholder="Enter Dataset Name", size="lg", style={'text-align':'center'}),
                html.Div(generate_dropdown(id('dropdown_dataset_type'), dataset_type, value=dataset_type[0]['value'], placeholder='Select Type of Dataset'), style={'width':'100%', 'display':'inline-block'}),
                dbc.Button("Create Dataset", id=id('button_create_load_dataset'), size="lg"),
            ], width={"size": 6, "offset": 3})
        ], align="center", style={'height':'700px', 'text-align':'center'})
    ], fluid=True, id=id('content')),
    html.Div(id='test1'),
])


dropdown_menu_items = [
    dbc.DropdownMenuItem("Deep thought", id="dropdown-menu-item-1"),
    dbc.DropdownMenuItem("Hal", id="dropdown-menu-item-2"),
    dbc.DropdownMenuItem(divider=True),
    dbc.DropdownMenuItem("Clear", id="dropdown-menu-item-clear"),
]



# Generate New Node ID or Load Node ID
# @app.callback(Output(id('node_id'), "value"),
#                 [Input('current_dataset', "data"),
#                 Input('current_node', 'data'),])
# def generate_load_node_id(metadata, selected_node):
#     # If New Dataset, Generate random Node number
#     if (metadata['node']) == 0:
#         return 123
#     else:
#         return selected_node


# Check if Dataset Exist. Modify Button to "Create Dataset" or "Load Dataset"
@app.callback([Output(id('button_create_load_dataset'), "children"), 
                Output(id('button_create_load_dataset'), "color"),
                Output(id('dropdown_dataset_type'), "disabled")],
                [Input(id('input_dataset_name'), "value")])
def check_if_dataset_name_exist(dataset_id):
    if dataset_id is None: return no_update
    
    list_of_dataset_id = [d['id'] for d in search_documents('dataset', 250)]
    isDisabled = False

    if dataset_id in list_of_dataset_id:
        button_name = "Load Dataset"
        color = "success"
        isDisabled = True
    else: 
        button_name = "Create Dataset"
        color = "primary"

    return button_name, color, isDisabled



@app.callback([Output('url', "pathname"), 
                Output('dropdown_current_dataset', "value"),
                Output('dropdown_current_dataset', "options"),
                Output(id('input_dataset_name'), "invalid"),
                Output(id('dropdown_dataset_type'), "style")],
                [Input(id('button_create_load_dataset'), "n_clicks"),
                State(id('input_dataset_name'), "value"),
                State(id('dropdown_dataset_type'), 'value')])
def button_create_load_dataset(n_clicks, dataset_id, dataset_type):
    if n_clicks is None: return no_update

    pathname = '/apps/data_lineage'
    invalid = False
    borderStyle = {}

    # Invalid Name or Datatype
    if (dataset_id is None) or (not dataset_id.isalnum()):
        print('Invalid File Name')
        invalid = True
    # if dataset_type is None:
    #     print('Invalid Dataset Type')
    #     borderStyle = {'border': '1px solid red'}

    # Get Existing Datasets & Initialize new dataset object
    dataset_list = search_documents('dataset', 250)
    dataset_options = [{'label': d['id'], 'value': d['id']} for d in dataset_list]
    
    
    # If valid Dataset ID
    if (dataset_id is not None) and (dataset_id.isalnum()):
        # Load Dataset
        if dataset_id in [d['id'] for d in dataset_list]:
            for dataset in dataset_list:
                if dataset_id == dataset['id']:
                    selected = dataset['id']
        # Create Dataset
        else:
            document = {
                'id': dataset_id, 
                'type': dataset_type, 
                'node': str([]),
                'cytoscape_node': str([]),
                'cytoscape_edge': str([])
            }
            create('dataset', document)
            # client.collections['dataset'].documents.create(document)
            dataset_options.append({'label':document['id'], 'value': document['id']})
            selected = document['id']

    return pathname, selected, dataset_options, invalid, borderStyle


