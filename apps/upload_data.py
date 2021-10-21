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
    )


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
UPLOAD_FOLDER_ROOT = r"C:\tmp\Uploads"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)
id = id_factory((__file__).rsplit("\\", 1)[1].split('.')[0]) # Prepend filename to id
tab_labels = ['Step 1: Create or Load Dataset', 'Step 2: Upload API', 'Step 2: Set API Profile', 'Step 3: Review API']
tab_values = [id('create_load_dataset'), id('upload_api'), id('set_data_profile'), id('review_data')]
datatype_list = ['object', 'Int64', 'float64', 'bool', 'datetime64', 'category']

dataset_type = [
    {'label': 'Numerical', 'value': 'numerical'},
    {'label': 'Categorical', 'value': 'categorical'},
    {'label': 'Hybrid', 'value': 'hybrid'},
    {'label': 'Time Series', 'value': 'time_series'},
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
    dcc.Store(id=id('api_list'), storage_type='memory'),
    dcc.Store(id='dataset_metadata', storage_type='session'),
    dcc.Store(id='dataset_profile', storage_type='session'),
    dcc.Store(id=id('remove_list'), storage_type='session'),

    generate_tabs(id('tabs_content'), tab_labels, tab_values),
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
                    html.Div(generate_dropdown(id('dropdown_file_type'), dataset_type, placeholder='Select Type of Dataset'), style={'width':'100%', 'display':'inline-block'}),
                    dbc.Button("Create Dataset", id=id('button_create_load_dataset'), size="lg"),
                ], width={"size": 6, "offset": 3})
            ], align="center", style={'height':'700px', 'text-align':'center'})
        ])

    if active_tab == id('upload_api'):
        content = html.Div([
            # Datatable
            dbc.Row([
                dbc.Col([
                    dbc.Col(html.H5('API Data', style={'text-align':'center'})),
                    dbc.Col(html.Div(generate_datatable(id('input_datatable_sample'), height='500px')), width=12),
                    html.Br(),
                ], width=12),
            ], className='bg-white text-dark'),

            # Settings & Drag and Drop
            dbc.Row([
                dbc.Col([
                    html.H5('Step 1.1: API Settings'),
                    html.Div('Name', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                    html.Div(dbc.Input(id=id('input_name'), placeholder="Enter Name of Dataset", type="text"), style={'width':'80%', 'display':'inline-block', 'margin':'0px 0px 2px 0px'}),

                    html.Div('Delimiter', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                    html.Div(generate_dropdown(id('dropdown_delimiter'), option_delimiter), style={'width':'80%', 'display':'inline-block'}),
        
                    dbc.Checklist(options=[
                        {"label": "Remove Spaces", "value": 'remove_space'},
                        {"label": "Remove Header", "value": 'remove_header'}
                    ], inline=False, switch=True, id=id('checklist_settings'), value=['remove_space'], labelStyle={'display':'block'}),
                ], width=6, className='rounded bg-info text-dark'),
                
                dbc.Col([
                    html.H5('Step 1.2: Upload Data (Smaller than 1MB)'),
                    get_upload_component(id=id('upload')),
                    # generate_upload('upload_json', "Drag and Drop or Click Here to Select Files"),
                ], className='text-center rounded bg-info text-dark', width=6),

            ], className='text-center', style={'margin': '1px'}),

            # List of Files in API
            dbc.Row([
                dbc.Col(html.H5('Files to be Uploaded'), width=12),
                dbc.Col(dcc.Dropdown(options=[], value=[], id=id('upload_api_list'), multi=True, clearable=True, placeholder=None), width=12),
            ], style={'text-align':'center'}),

            # Upload Button & Error Messages
            dbc.Row([
                dbc.Col([html.Button('Upload', id=id('button_upload'), className='btn btn-primary btn-block', style={'margin':'20px 0px 0px 0px', 'font-size': '13px', 'font-weight': 'bold'}),], width=12),
                dbc.Col(html.Hr(), width=12),
                dbc.Col(id=id('upload_error'), width=12),
            ]),
        ]),

    elif active_tab == id('set_data_profile'):
        content = html.Div([
            dbc.Row(dbc.Col(html.H5('Step 2: Set Data Profile'), width=12)),
            dbc.Row(dbc.Col(html.Div(id=id('data_profile'), style={'overflow-y': 'auto', 'overflow-x': 'hidden', 'height':'800px'}), width=12)),
            # html.Div(id=id('data_profile')),
            # html.Div(html.Button('Next Step', className='btn btn-primary', id=id('next_button_2')), className='text-center'),
        ], className='text-center', style={'margin': '3px'}),
        

    elif active_tab == id('review_data'):
        content = dbc.Row([
            dbc.Col(html.H5('Step 3: Preview Data'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),
            html.Br(),
            # dbc.Col(html.Div(html.Button('Upload Data', className='btn btn-primary', id=id('button_confirm')), className='text-center'), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '3px'}),

    return content


# Check if Dataset Exist. Modify Button to "Create Dataset" or "Load Dataset"
@app.callback([Output(id('button_create_load_dataset'), "children"), 
                Output(id('button_create_load_dataset'), "color")],
                [Input(id('input_dataset_name'), "value")])
def check_if_dataset_name_exist(value):
    if value is None: return no_update

    list_of_collections = [c['name'] for c in client.collections.retrieve()]
    dataset_name = "dataset_" + value

    if dataset_name in list_of_collections: 
        button_name = "Load Dataset"
        color = "success"
    else: 
        button_name = "Create Dataset"
        color = "primary"

    return button_name, color



@app.callback([Output(id('tabs_content'), "value"), 
                Output('dataset_metadata', "data"),
                Output(id('input_dataset_name'), "invalid"),
                Output(id('dropdown_file_type'), "style")],
                [Input(id('button_create_load_dataset'), "n_clicks"),
                State(id('input_dataset_name'), "value"),
                State(id('dropdown_file_type'), 'value')])
def on_create_load_dataset(n_clicks, name, dataset_type):
    if n_clicks is None: return no_update

    active_tab = no_update
    metadata = no_update
    invalid = False
    borderStyle = {}

    if (name is None) or (not name.isalnum()):
        print('Invalid File Name')
        invalid = True
    if dataset_type is None:
        print('Invalid Dataset Type')
        borderStyle = {'border': '1px solid red'}

    if (name is not None) and (name.isalnum()) and (dataset_type is not None):
        list_of_collections = [c['name'] for c in client.collections.retrieve()]
        name = "dataset_" + name
        active_tab = id('upload_api')
        metadata = {
            'name': name,               # Str
            'type': dataset_type,       # Str
            'node': [],                 # List of Str (Node Names)
        }

        # Upload Metadata
        if name not in list_of_collections: 
            client.collections.create(generate_schema_auto(name))

    print('Metadata: ' + str(metadata))

    return active_tab, metadata, invalid, borderStyle
    

# Drag and Drop Callback
@du.callback(output=[Output(id('upload_api_list'), 'options'),
                    Output(id('upload_api_list'), 'value')],
                id=id('upload'))
def get_a_list(filename):
    time.sleep(0.5)
    upload_id = filename[0].rsplit("\\", 2)[1]
    root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
    file_name_list = os.listdir(root_folder)
    file_name_list_full = [(root_folder / filename).as_posix() for filename in os.listdir(root_folder)]
    options = [{'label': filename, 'value': filename_full} for filename, filename_full in zip(file_name_list, file_name_list_full)]

    return options, file_name_list_full


# # Upload Button
# @app.callback([Output('dataset_metadata', 'data'),
#                 Output(id('upload_error'), 'children')], 
#                 [Input(id('button_upload'), 'n_clicks'),
#                 Input(id('dropdown_file_type'), 'value'),
#                 Input(id('dropdown_delimiter'), 'value'), 
#                 Input(id('checklist_settings'), 'value'),
#                 State(id('input_name'), 'value'),
#                 State(id('api_list'), 'data')])
# def upload(n_clicks, type, delimiter, checklist_settings, input_name, api_list):
#     if n_clicks is None: return no_update
#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
#     dataset_name = 'dataset_' + input_name

#     # If upload clicked
#     if triggered == id('button_upload'):
#         # Check invalid names
#         # if (name is None) or (not name.isalnum()):
#         #     print('Invalid File Name')
#         #     return no_update, html.Div('Invalid File Name', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger')
#         # Check if name exist
#         if dataset_name in [c['name'] for c in client.collections.retrieve()]:
#             print('File Name Exist')
#             return no_update, html.Div('File Name Exist', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger')
    
#     # # Upload Metadata
#     # metadata = {}
#     # metadata['name'] = input_name
#     # metadata['api'] = [dataset_name+'_api_'+str(num) for num in list(range(1, len(api_list)+1))]
#     # metadata['blob'] = []
#     # metadata['index'] = []
#     # metadata['datatype'] = {}
#     # metadata['expectation'] = []
#     # metadata['cytoscape_elements'] = []
#     # metadata['setting'] = {'type': type, 'delimiter': delimiter, 'checklist': checklist_settings}
#     # metadata2 = metadata.copy()
#     # for k, v in metadata2.items():
#     #     metadata2[k] = str(metadata2[k])
#     # client.collections.create(generate_schema_auto(dataset_name))
#     # client.collections[dataset_name].documents.create(metadata2)

#     # Upload File contents
#     for i, file_list in enumerate(api_list):
#         data = []
#         if all(f.endswith('.json') for f in file_list): # JSON Uploaded
#             for file in file_list:
#                 with open(file, 'r') as f:
#                     json_file = json.load(f)
#                 json_file = flatten(json_file)
#                 data.append(json_file)
#             df = json_normalize(data)

#         elif all(f.endswith('.csv') for f in file_list):
#             df = pd.read_csv(file_list[0]) # TODO for now Assume only 1 CSV uploaded

#         df.fillna('None', inplace=True) # Replace null with 'None
#         jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

#         client.collections.create(generate_schema_auto(metadata['api'][i]))
#         client.collections[metadata['api'][i]].documents.import_(jsonl, {'action': 'create'})
        
#     return metadata, html.Div('Successfully Uploaded', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-success') 
        


# # Update Sample Datatable 
# # @app.callback([Output(id('input_datatable_sample'), "data"), 
# #                 Output(id('input_datatable_sample'), 'columns'),
# #                 Output(id('input_datatable_sample'), 'style_data_conditional')],
# #                 [Input('dataset_metadata', "data")])
# # def update_data_table(settings):
# #     if settings is None or settings['name'] is None: return no_update

# #     # Get Data & Columns
# #     result = get_documents(settings['name'], 5)
# #     df = json_normalize(result)
# #     df.insert(0, column='index', value=range(1, len(df)+1))
# #     columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

# #     # Style datatable and manipulate df upon settings change
# #     style_data_conditional = []
# #     if 'remove_space' in settings['checklist']:
# #         df = whitespace_remover(df)
# #     if 'remove_header' in settings['checklist']:
# #         style_data_conditional.append({'if': {'row_index': 0}, 'backgroundColor': 'grey'})

# #     # if len(str(filename)) > 80:
# #     #     filename =str(filename)
# #     #     filename = filename[:20] + " ... " + filename[-20:]
# #     # options.append({'label': filename, 'value': })

# #     return df.to_dict('records'), columns, style_data_conditional, no_update




# def generate_expectations():
#     datatype = None # TODO get selected dropdown datatype from arg
#     expectation = html.Div()

#     if datatype == datatype_list[0]:  # Object
#         pass
#     elif datatype == datatype_list[1]:  # Int64
#         pass
#     elif datatype == datatype_list[2]:  # float64
#         pass
#     elif datatype == datatype_list[3]:  # bool
#         pass
#     elif datatype == datatype_list[4]:  # datetime64
#         pass
#     elif datatype == datatype_list[5]:  # category
#         pass

#     return [ 
#         html.Div([
#             expectation,
#             html.Div('Not Null Threshold', style={'width':'40%', 'display':'inline-block', 'vertical-align':'top'}),
#             html.Div(generate_slider(id('slider_not_null_threshold'), min=0, max=100, step=1, value=1), style={'width':'50%','display':'inline-block'}),
#             html.Div(style={'width':'40%', 'display':'inline-block', 'vertical-align':'top'}, id=id('val_not_null_threshold')),
#         ]),
#     ]
    

# @app.callback(Output(id('data_profile'), 'children'), 
#             [Input('dataset_metadata', 'data'),
#             Input('url', 'pathname')])
# def generate_profile(metadata, pathname):
#     if metadata is None or metadata['name'] is None: return no_update
    
#     result = get_documents('dataset_'+metadata['name'], 100)
#     df = json_normalize(result)
#     columns = list(df.columns)
#     detected_datatype_list = list(map(str, df.convert_dtypes().dtypes))

#     option_datatype = [
#         {'label': 'object', 'value': 'object'},
#         {'label': 'string', 'value': 'string'},
#         {'label': 'Int64', 'value': 'Int64'},
#         {'label': 'datetime64', 'value': 'datetime64'},
#         {'label': 'boolean', 'value': 'boolean'},
#         {'label': 'category', 'value': 'category'}
#     ]

#     return (html.Table(
#         [html.Tr([
#             html.Th('Column'),
#             html.Th('Datatype'),
#             html.Th('Invalid (%)'),
#             html.Th('Result'),
#             html.Th(''),
#         ])] + 
#         [html.Tr([
#             html.Td(html.H6(col), id={'type':id('col_column'), 'index': i}),
#             html.Td(generate_dropdown({'type':id('col_dropdown_datatype'), 'index': i}, option_datatype, value=dtype)),
#             html.Td(html.H6('%', id={'type':id('col_invalid'), 'index': i})),
#             html.Td(html.H6('-', id={'type':id('col_result'), 'index': i})),
#             html.Td(html.Button('Remove', id={'type':id('col_button_remove'), 'index': i}, style={'background-color':'white'})),
#             ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(zip(columns, detected_datatype_list))
#         ] +
#         [html.Tr([''])],
#         style={'width':'100%', 'height':'800px'}, 
#         id=id('table_data_profile')))


# # Style deleted row
# @app.callback(Output({'type':id('row'), 'index': MATCH}, 'style'), 
#             [Input({'type':id('col_button_remove'), 'index': MATCH}, 'n_clicks'),
#             State({'type':id('row'), 'index': MATCH}, 'style')])
# def style_row(n_clicks, style):
#     if n_clicks is None: return no_update

#     if style is None: newStyle = {'background-color':'grey'}
#     else: newStyle = None

#     return newStyle




# # Store profile
# @app.callback(Output('dataset_profile', 'data'),
#                 Output(id('remove_list'), 'data'),
#                 [Input(id("tabs_content"), "value"),
#                 Input({'type':id('col_dropdown_datatype'), 'index': ALL}, 'value'),
#                 Input({'type':id('col_button_remove'), 'index': ALL}, 'n_clicks'),
#                 State({'type':id('col_column'), 'index': ALL}, 'children')])
# def update_output(tab, datatype, remove_list_n_clicks, column):
#     if tab != id('set_data_profile'): return no_update

#     column = [c['props']['children'] for c in column]

#     # Profile
#     profile = {}
#     profile['datatype'] = dict(zip(column, datatype))
#     profile['index'] = '' # TODO Store index field 
#     profile['expectation'] = {} # TODO Store expectations 

#     # Remove Column List
#     remove_list = []
#     for n_clicks, c in zip(remove_list_n_clicks, column):
#         if (n_clicks is not None) and n_clicks%2 == 1:
#             remove_list.append(c)

#     return profile, remove_list


# # Update Datatable in "Review Data" Tab
# @app.callback([Output(id('input_datatable'), "data"), 
#                 Output(id('input_datatable'), 'columns')], 
#                 [Input(id("tabs_content"), "value"),
#                 State('dataset_metadata', "data"),
#                 State('dataset_profile', "data"),
#                 State(id('remove_list'), "data")])
# def update_data_table(tab, settings, profile, remove_list):
#     if settings is None or settings['name'] is None: return no_update
#     if tab != id('review_data'): return no_update
    
#     result = get_documents(settings['name'], 250)
#     df = json_normalize(result)
#     df.insert(0, column='index', value=range(1, len(df)+1))

#     # Remove Columns
#     df.drop(remove_list, axis=1, inplace=True)

#     # Settings
#     print(settings)

#     # Profile
#     # print(profile['datatype'])

#     columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]
    
#     return df.to_dict('records'), columns


# Update typesense dataset with settings/profile/columns to remove
# @app.callback(Output(id('????????'), "??????"), 
#                 [Input(id("button_confirm"), "n_clicks"),
#                 State('dataset_metadata', "data"),
#                 State('dataset_profile', "data")])
# def upload_data(n_clicks, setting, profile):
#     if n_clicks is None: return no_update

#     print(setting)
#     print(profile)

    # Update typesense dataset

    # Update typesense dataset profile

#     return no_update
