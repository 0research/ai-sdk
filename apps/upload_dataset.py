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
    dbc.Container([
        # Settings & Drag and Drop
        dbc.Row([
            dbc.Col([
                html.H5('Step 1: Dataset Description'),
                dbc.InputGroup([
                    dbc.InputGroupText("Project ID", style={'width':'120px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'30px'}), 
                    dbc.Input(id=id('project_id'), disabled=True, style={'font-size': '12px', 'text-align':'center'})
                ], className="mb-3 lg"),
                dbc.InputGroup([
                    dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Textarea(id=id('dataset_description'), placeholder='Enter Dataset Description (Optional)', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                ], className="mb-3 lg"),
            ], width={'size':8, 'offset':2}, className='rounded bg-info text-dark'),
            dbc.Col(html.Hr(style={'border': '1px dotted black', 'margin': '30px 0px 30px 0px'}), width=12),
        ], className='text-center', style={'margin': '1px'}),
        
        dbc.Row([
            dbc.Col([
                html.H5('Step 2: Select Files'),
                html.Div(get_upload_component(id=id('browse_drag_drop'))),
            ], width={'size':4, 'offset':0}),
            dbc.Col([
                html.H5('Step 3: Review Selected Files'),
                dcc.Dropdown(options=[], value=[], id=id('files_selected'), multi=True, clearable=True, placeholder=None, style={'height':'150px', 'overflow-y':'auto'})
            ], width={'size':4, 'offset':0}),
            dbc.Col([
                html.H5('Step 4: Set Settings'),
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
                dbc.Col(html.H5('Step 5: Review & Upload Data', style={'text-align':'center'})),
                dbc.Col(html.Div(generate_datatable(id('datatable'), height='500px')), width=12),
                html.Br(),
            ], width=12),
        ], className='bg-white text-dark'),

        # Upload Button & Error Messages
        dbc.Row([
            dbc.Col(html.Button('Upload', id=id('button_upload'), className='btn btn-primary btn-block', style={'margin':'20px 0px 0px 0px', 'font-size': '13px', 'font-weight': 'bold'}), width={'size':10, 'offset':1}),
            dbc.Col(id=id('upload_error'), width=12),
        ]),
    ], fluid=True, id=id('content')),
])

#Load Project ID
@app.callback(Output(id('project_id'), 'value'),
                Input('url', 'pathname'))
def load_project_id(pathname):
    return get_session('project_id')




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
    datatable_data = []
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
                file_str = open(file,"r").read().replace('None', '""')
                json_file = json.loads(file_str)
                json_file = flatten(json_file)
                data.append(json_file)
                df = json_normalize(data)
                
            elif file.endswith('.csv'):
                df = pd.read_csv(file_name_list_full[0], sep=dropdown_delimiter['value']) # Assume only 1 CSV uploaded, TODO combine if CSV and JSON uploaded together?

        if len(file_name_list) > 0:
            df.fillna('None', inplace=True) # Remove Null with 'None'
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
@app.callback(Output('url', 'pathname'),
                Input(id('button_upload'), 'n_clicks'),
                State(id('dataset_description'), 'value'),
                State(id('dropdown_delimiter'), 'value'),
                State(id('checklist_settings'), 'value'),
                State(id('datatable'), 'data'))
def upload(n_clicks, dataset_description, dropdown_delimiter, checklist_settings, datatable_data):
    if n_clicks is None: return no_update

    pathname = '/apps/data_lineage'
    dataset_id = str(uuid.uuid1())
    project_id = get_session('project_id')
    remove_space = 'remove_space' in checklist_settings
    remove_header = 'remove_header' in checklist_settings
    upload_dataset(project_id, dataset_id, datatable_data, dataset_description, '', 
                    dropdown_delimiter, remove_space, remove_header)
    # store_session('dataset_id', dataset_id)

    return pathname