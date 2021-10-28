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
import dash_uploader as du



def get_upload_component(id):
    return du.Upload(
        id=id,
        max_file_size=1,  # 1 Mb
        filetypes=['csv', 'json', 'jsonl'],
        upload_id=uuid.uuid1(),  # Unique session id
        max_files=100,
        default_style={'height':'150px'},
    )


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
UPLOAD_FOLDER_ROOT = r"C:\tmp\Uploads"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)
id = id_factory('upload')
tab_labels = ['Step 1: Create or Load Dataset', 'Step 2: Upload API']
tab_values = [id('create_load_dataset'), id('upload_api')]
tab_disabled = [False, True]
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

    generate_tabs(id('tabs_content'), tab_labels, tab_values, tab_disabled),
    dbc.Container([], fluid=True, id=id('content')),
    html.Div(id='test1'),
])


dropdown_menu_items = [
    dbc.DropdownMenuItem("Deep thought", id="dropdown-menu-item-1"),
    dbc.DropdownMenuItem("Hal", id="dropdown-menu-item-2"),
    dbc.DropdownMenuItem(divider=True),
    dbc.DropdownMenuItem("Clear", id="dropdown-menu-item-clear"),
]

# Tab Content
@app.callback(Output(id("content"), "children"), [Input('url', 'pathname'), Input(id("tabs_content"), "value")])
def generate_tab_content(pathname, active_tab):
    content = None
    if active_tab == id('create_load_dataset'):
        content = html.Div([
            dbc.Row(dbc.Col(html.H2('Step 1: Create or Load Existing Dataset')), style={'text-align':'center'}),
            dbc.Row([
                dbc.Col([
                    dbc.Input(id=id('input_dataset_name'), placeholder="Enter Dataset Name", size="lg", style={'text-align':'center'}),
                    html.Div(generate_dropdown(id('dropdown_dataset_type'), dataset_type, value=dataset_type[0]['value'], placeholder='Select Type of Dataset'), style={'width':'100%', 'display':'inline-block'}),
                    dbc.Button("Create Dataset", id=id('button_create_load_dataset'), size="lg"),
                ], width={"size": 6, "offset": 3})
            ], align="center", style={'height':'700px', 'text-align':'center'})
        ])

    if active_tab == id('upload_api'):
        content = html.Div([
            # Settings & Drag and Drop
            dbc.Row([
                dbc.Col([
                    html.H5('Step 1.1: API Description'),
                    dbc.InputGroup([
                        dbc.InputGroupText("Dataset ID", style={'width':'120px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'30px'}), 
                        dbc.Input(id=id('dataset_id'), disabled=True, style={'font-size': '12px', 'text-align':'center'})
                    ], className="mb-3 lg"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Node ID", style={'width':'120px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'30px'}), 
                        dbc.Input(id=id('node_id'), disabled=True, style={'font-size': '12px', 'text-align':'center'})
                    ], className="mb-3 lg"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                        dbc.Textarea(id=id('node_description'), placeholder='Enter API Description (Optional)', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                    ], className="mb-3 lg"),
                ], width={'size':8, 'offset':2}, className='rounded bg-info text-dark'),
                dbc.Col(html.Hr(style={'border': '1px dotted black', 'margin': '30px 0px 30px 0px'}), width=12),
            ], className='text-center', style={'margin': '1px'}),
            
            dbc.Row([
                dbc.Col([
                    html.H5('Step 1.2: Select Files'),
                    html.Div(get_upload_component(id=id('browse_drag_drop'))),
                ], width={'size':4, 'offset':0}),
                dbc.Col([
                    html.H5('Step 1.3: Review Selected Files'),
                    dcc.Dropdown(options=[], value=[], id=id('files_selected'), multi=True, clearable=True, placeholder=None, style={'height':'150px', 'overflow-y':'auto'})
                ], width={'size':4, 'offset':0}),
                dbc.Col([
                    html.H5('Step 1.4: Set Settings'),
                    dbc.InputGroup([
                        dbc.InputGroupText("Delimiter", style={'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                        dbc.Select(options=option_delimiter, id=id('dropdown_delimiter'), value=option_delimiter[0], style={'font-size': '12px'}),
                    ]),
                    dbc.Checklist(options=[
                        {"label": "Remove Spaces", "value": 'remove_space'},
                        {"label": "Remove Header", "value": 'remove_header'}
                    ], inline=False, switch=True, id=id('checklist_settings'), value=['remove_space'], labelStyle={'display':'block'}),
                ], width={'size':4, 'offset':0}),
                dbc.Col(html.Hr(style={'border': '1px dotted black', 'margin': '30px 0px 30px 0px'}), width=12),
            ], style={'text-align':'center'}),
            
            # Datatable
            dbc.Row([
                dbc.Col([
                    dbc.Col(html.H5('Review & Upload Data', style={'text-align':'center'})),
                    dbc.Col(html.Div(generate_datatable(id('datatable'), height='500px')), width=12),
                    html.Br(),
                ], width=12),
            ], className='bg-white text-dark'),

            # Upload Button & Error Messages
            dbc.Row([
                dbc.Col(html.Button('Upload', id=id('button_upload'), className='btn btn-primary btn-block', style={'margin':'20px 0px 0px 0px', 'font-size': '13px', 'font-weight': 'bold'}), width={'size':10, 'offset':1}),
                dbc.Col(id=id('upload_error'), width=12),
            ]),
        ]),
    return content


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



@app.callback([Output(id('tabs_content'), "value"), 
                Output('dropdown_current_dataset', "value"),
                Output('dropdown_current_dataset', "options"),
                Output(id('input_dataset_name'), "invalid"),
                Output(id('dropdown_dataset_type'), "style")],
                [Input(id('button_create_load_dataset'), "n_clicks"),
                State(id('input_dataset_name'), "value"),
                State(id('dropdown_dataset_type'), 'value')])
def button_create_load_dataset(n_clicks, dataset_id, dataset_type):
    if n_clicks is None: return no_update

    active_tab = no_update
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
        active_tab = id('upload_api')
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
            client.collections['dataset'].documents.create(document)
            dataset_options.append({'label':document['id'], 'value': document['id']})
            selected = document['id']

    return active_tab, selected, dataset_options, invalid, borderStyle


# Load Dataset ID and Node ID
@app.callback([Output(id('dataset_id'), 'value'),
                Output(id('node_id'), 'value')],
                [Input(id('tabs_content'), "value"),
                State('current_dataset', 'data')])
def load_nodeID_datasetID(tab, dataset_id):
    if tab != id('upload_api'): return no_update
    return dataset_id, str(uuid.uuid1())




# Browse Drag&Drop Files, Display File Selection, Settings, Update Datatable 
@app.callback([Output(id('files_selected'), 'value'),
                Output(id('files_selected'), 'options'),
                Output(id('dropdown_delimiter'), 'disabled'),
                Output(id('datatable'), "data"), 
                Output(id('datatable'), 'columns'),
                Output(id('datatable'), 'style_data_conditional'),],
                [Input(id('browse_drag_drop'), 'isCompleted'),
                Input(id('files_selected'), 'value'),
                Input(id('dropdown_delimiter'), 'value'),
                Input(id('checklist_settings'), 'value'),
                State(id('browse_drag_drop'), 'upload_id'),
                State(id('datatable'), 'data')])
def browse_drag_drop_files(isCompleted, files_selected, dropdown_delimiter, checklist_settings, upload_id, datatable_data):
    time.sleep(0.5)
    if not isCompleted: return no_update
    # Initialize Default Outputs
    files_selected_options = []
    dropdown_delimiter_disabled = True
    # datatable_data = {}
    datatable_columns = []
    style_data_conditional = []
    
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
    file_name_list = os.listdir(root_folder)
    file_name_list_full = [(root_folder / filename).as_posix() for filename in os.listdir(root_folder)]

    # Drag & Drop or Delete Files or Change Delimiter
    if triggered == id('browse_drag_drop') or triggered == id('files_selected') or triggered == id('dropdown_delimiter'):

        if triggered == id('browse_drag_drop'):
            files_selected_options = [{'label': filename, 'value': filename_full} for filename, filename_full in zip(file_name_list, file_name_list_full)]
            file_extensions = [name.rsplit('.', 1)[1] for name in file_name_list]
            if 'csv' in file_extensions: 
                dropdown_delimiter_disabled = False

        elif triggered == id('files_selected'):
            files_to_remove = set(file_name_list_full) - set(files_selected)
            try:
                for file in files_to_remove:
                    os.remove(file)
            except Exception as e:
                print(e)
            file_name_list = os.listdir(root_folder)
            file_name_list_full = [(root_folder / filename).as_posix() for filename in os.listdir(root_folder)]
            files_selected_options = [{'label': filename, 'value': filename_full} for filename, filename_full in zip(file_name_list, file_name_list_full)]

        data = []
        for file in file_name_list_full:
            if file.endswith('.json'):
                with open(file, 'r') as f:
                    json_file = json.load(f)
                json_file = flatten(json_file)
                data.append(json_file)
                df = json_normalize(data)
                
            elif file.endswith('.csv'):
                df = pd.read_csv(file_name_list_full[0], sep=dropdown_delimiter['value']) # Assume only 1 CSV uploaded, TODO combine if CSV and JSON uploaded together?

        # Remove Null with 'None'
        df.fillna('None', inplace=True)

        datatable_data = df.to_dict('records')
        datatable_columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    # Select Checklist
    if triggered == id('checklist_settings'):
        df = json_normalize(datatable_data)
        if 'remove_space' in checklist_settings:
            df = whitespace_remover(df)
        if 'remove_header' in checklist_settings:
            style_data_conditional = [{'if': {'row_index': 0}, 'backgroundColor': 'grey'}]
    
    return file_name_list_full, files_selected_options, dropdown_delimiter_disabled, datatable_data, datatable_columns, style_data_conditional


# Upload Button
@app.callback([Output('display_current_node', 'value'), 
                Output('url', 'pathname')],
                [Input(id('button_upload'), 'n_clicks'),
                State('current_dataset', 'data'),
                State(id('node_id'), 'value'),
                State(id('node_description'), 'value'),
                State(id('dropdown_delimiter'), 'value'),
                State(id('checklist_settings'), 'value'),
                State(id('datatable'), 'data')])
def upload(n_clicks, current_dataset, node_id, node_description, dropdown_delimiter, checklist_settings, datatable_data):
    if n_clicks is None: return no_update

    remove_space, remove_header = False, False
    if 'remove_space' in checklist_settings: remove_space = True
    if 'remove_header' in checklist_settings: remove_header = False

    # Retrieve and Append Dataset Metadata Document
    dataset = get_document('dataset', current_dataset)
    dataset['node'].append(node_id)
    from random import randint
    dataset['cytoscape_node'].append({
        'data': {'id': node_id, 'label': node_id},
        'position': {'x': randint(1, 100), 'y': randint(1, 100)},
        'classes': 'api',
    })

    # Form Node Data Collection
    df = json_normalize(datatable_data)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

    # Create Node Metadata Document
    node = {
        'id': node_id,
        'description': node_description, 
        'source': [], # TODO add filename uploaded?
        'delimiter': dropdown_delimiter, 
        'remove_space': remove_space,
        'remove_header': remove_header,
        'type': 'api', 
        'datatype': {col:str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)},
        'isDeletedStatus': {col:False for col in df.columns},
        'expectation': {col:None for col in df.columns},
        'index': [], 
        'target': [],
    }
    
    # Upload to Typesense
    upsert('dataset', dataset)
    upsert('node', node)
    client.collections.create(generate_schema_auto(node_id))
    client.collections[node_id].documents.import_(jsonl, {'action': 'create'})
    
    return node_id, '/apps/data_lineage'