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

import time
import ast
from pathlib import Path
import uuid


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('upload')

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
    dbc.Container([
        dbc.Row(dbc.Col(html.H2('Create or Load Existing Dataset')), style={'text-align':'center'}),
        dbc.Row([
            dbc.Col([
                dbc.Input(id=id('input_project_id'), placeholder="Enter Dataset Name", size="lg", style={'text-align':'center'}),
                html.Div(generate_dropdown(id('dropdown_project_type'), dataset_type, value=dataset_type[0]['value'], placeholder='Select Type of Dataset'), style={'width':'100%', 'display':'inline-block'}),
                dbc.Button("Create Dataset", id=id('button_create_load_dataset'), size="lg"),
            ], width={"size": 6, "offset": 3})
        ], align="center", style={'height':'700px', 'text-align':'center'})
    ], fluid=True, id=id('content')),
])


# Check if Dataset Exist. Modify Button to "Create Dataset" or "Load Dataset"
@app.callback([Output(id('button_create_load_dataset'), "children"), 
                Output(id('button_create_load_dataset'), "color"),
                Output(id('dropdown_project_type'), "style")],
                Input(id('input_project_id'), "value"))
def check_if_dataset_name_exist(project_id):
    if project_id is None: return no_update
    
    project_id_list = [d['id'] for d in search_documents('project')]
    isDisabled = {'display': 'block'}

    if project_id in project_id_list:
        button_name = "Load Dataset"
        color = "success"
        isDisabled = {'display': 'none'}
    else: 
        button_name = "Create Dataset"
        color = "primary"

    return button_name, color, isDisabled



@app.callback([Output('url', "pathname"), 
                Output(id('input_project_id'), "invalid")],
                [Input(id('button_create_load_dataset'), "n_clicks"),
                State(id('input_project_id'), "value"),
                State(id('dropdown_project_type'), 'value')])
def button_create_load_dataset(n_clicks, project_id, project_type):
    if n_clicks is None: return no_update

    pathname = no_update
    invalid = False

    # Invalid Name or Datatype
    if (project_id is None) or (not project_id.isalnum()):
        print('Invalid File Name')
        invalid = True

    # If valid Project ID
    else:
        pathname = '/apps/data_lineage'
        project_list = search_documents('project')
        if project_id not in [d['id'] for d in project_list]: # Create Project if doesn't exist
            new_project(project_id, project_type)
        store_session('project_id', project_id)
        store_session('node_id', None)
            
    return pathname, invalid


