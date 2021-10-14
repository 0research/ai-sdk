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


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('upload_data')
tab_labels = ['Step 1: Upload Data', 'Step 2: Set Data Profile', 'Step 3: Review Data']
tab_values = [id('upload_data'), id('set_data_profile'), id('review_data')]
datatype_list = ['object', 'Int64', 'float64', 'bool', 'datetime64', 'category']
option_filetype = [
    {'label': 'JSON', 'value': 'json'},
    {'label': 'CSV', 'value': 'csv'},
]
option_data_nature = [
    {'label': 'Numerical', 'value': 'numerical'},
    {'label': 'Categorical', 'value': 'categorical'},
    {'label': 'Hybrid', 'value': 'hybrid'},
    {'label': 'Time Series', 'value': 'time_series'},
    {'label': 'Geo Spatial', 'value': 'geo_spatial'},
]
option_delimiter = [
    {'label': 'Comma (,)', 'value': ','},
    {'label': 'Tab', 'value': r"\t"},
    {'label': 'Space', 'value': r"\s+"},
    {'label': 'Pipe (|)', 'value': '|'},
    {'label': 'Semi-Colon (;)', 'value': ';'},
    {'label': 'Colon (:)', 'value': ':'},
]


# Layout
layout = html.Div([
    dcc.Store(id='dataset_setting', storage_type='session'),
    dcc.Store(id='dataset_profile', storage_type='session'),
    dcc.Store(id=id('remove_list'), storage_type='session'),

    generate_tabs(id('tabs_content'), tab_labels, tab_values),
    dbc.Container([], fluid=True, id=id('content')),
    html.Div(id='test1'),
])


# Tab Content
@app.callback(Output(id("content"), "children"), [Input(id("tabs_content"), "value")])
def generate_tab_content(active_tab):
    content = None
    if active_tab == id('upload_data'):
        content = dbc.Row([
            dbc.Col([
                html.H5('Step 1.1: Dataset Settings'),
                html.Div('Name', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                html.Div(dbc.Input(id=id('input_name'), placeholder="Enter Name of Dataset", type="text"), style={'width':'80%', 'display':'inline-block', 'margin':'0px 0px 2px 0px'}),

                html.Div('Type', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                html.Div(generate_dropdown(id('dropdown_file_type'), option_data_nature), style={'width':'80%', 'display':'inline-block'}),

                html.Div('Delimiter', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                html.Div(generate_dropdown(id('dropdown_delimiter'), option_delimiter), style={'width':'80%', 'display':'inline-block'}),
    
                dbc.Checklist(options=[
                    {"label": "Remove Spaces", "value": 'remove_space'},
                    {"label": "Remove Header", "value": 'remove_header'}
                ], inline=False, switch=True, id=id('checklist_settings'), value=['remove_space'], labelStyle={'display':'block'}),
            ], width=6),

            dbc.Col([
                html.H5('Step 1.2: Upload Data (Smaller than 1MB)'),
                html.Div(id='callback-output'),
                generate_upload('upload_json', "Drag and Drop or Click Here to Select Files"),
                html.Div(id=id('upload_text')),
                html.Button('Upload', id=id('button_upload'), className='btn btn-primary btn-block', style={'margin':'20px 0px 0px 0px', 'font-size': '13px', 'font-weight': 'bold'}),
            ], className='text-center', width=6),

            dbc.Col(html.Hr(), width=12),

            dbc.Col([
                dbc.Col(html.H5('Sample Data', style={'text-align':'center'})),
                dbc.Col(html.Div(generate_datatable(id('input_datatable_sample'), height='300px')), width=12),
                html.Br(),
            ], width=12),

            dbc.Col(id=id('upload_error'), width=12),

            dbc.Col([
                html.Br(),
                # html.Div(html.Button('Next Step', className='btn btn-primary', id=id('next_button_1')), className='text-center'),
            ]),
        ], className='text-center', style={'margin': '3px'}),


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

@app.callback(Output(id('upload_text'), 'children'),
                Input('upload_json', 'filename'))
def generate_selected_files(filename):
    if filename is None: return no_update
    if len(str(filename)) > 80:
        filename =str(filename)
        filename = filename[:20] + " ... " + filename[-20:]
    return filename


# Save Uploaded data & Settings
@app.callback([Output('dataset_setting', 'data'), 
                Output(id('upload_error'), 'children')],
                [Input(id('button_upload'), 'n_clicks'),  
                Input(id('dropdown_file_type'), 'value'), 
                Input(id('dropdown_delimiter'), 'value'), 
                Input(id('checklist_settings'), 'value'),
                State('upload_json', 'contents'), 
                State(id('input_name'), 'value'),
                State('upload_json', 'filename'), 
                State('upload_json', 'last_modified')])
def save_settings_dataset(n_clicks, type, delimiter, checklist_settings, contents, input_name, filename, last_modified):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

    # Save Settings
    settings = {}
    settings['name'] = input_name
    settings['type'] = type
    settings['delimiter'] = delimiter
    settings['checklist'] = checklist_settings

    # If upload clicked.
    if triggered == id('button_upload'):
        # Check invalid names
        if input_name == None or (' ' in input_name): 
            print('Invalid File Name')
            return no_update, html.Div('Invalid File Name', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger')
        # Check if name exist
        for c in client.collections.retrieve():
            if c['name'] == input_name:
                print('File Name Exist')
                return no_update, html.Div('File Name Exist', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger')

        # JSON Uploaded
        if all(f.endswith('.json') for f in filename):
            data = []
            try:
                for filename, content in zip(filename, contents):
                    content_type, content_string = content.split(',')
                    decoded = base64.b64decode(content_string)
                    decoded = json.loads(decoded.decode('utf-8'))
                    decoded = flatten(decoded)
                    data.append(decoded)
            except Exception as e:
                print(e)

            df = json_normalize(data)


        # CSV Uploaded
        elif len(filename) == 1 and filename[0].endswith('csv'):
            content_type, content_string = contents[0].split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=delimiter, header=0)

        # Replace null with 'None'
        df.fillna('None', inplace=True)

        # Convert to jsonl
        jsonl = df.to_json(orient='records', lines=True)

        # Check if exceed size
        if sys.getsizeof(jsonl) > 1000000:
            print('Filesize: ', sys.getsizeof(jsonl))
            return no_update, html.Div('File size too large!', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-danger') 

        # Upload to typesense
        schema = generate_schema_auto(input_name)
        client.collections.create(schema)
        client.collections[input_name].documents.import_(jsonl, {'action': 'create'})

        return settings, html.Div('Successfully Uploaded', style={'text-align':'center', 'width':'100%', 'color':'white'}, className='bg-success') 

    else:
        return settings, ''


# Update Sample Datatable 
@app.callback([Output(id('input_datatable_sample'), "data"), 
                Output(id('input_datatable_sample'), 'columns'),
                Output(id('input_datatable_sample'), 'style_data_conditional')], 
                Input('dataset_setting', "data"))
def update_data_table(settings):
    if settings is None or settings['name'] is None: return no_update

    # Get Data & Columns
    result = get_documents(settings['name'], 5)
    df = json_normalize(result)
    df.insert(0, column='index', value=range(1, len(df)+1))
    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    # Style datatable and manipulate df upon settings change
    style_data_conditional = []
    if 'remove_space' in settings['checklist']:
        df = whitespace_remover(df)
    if 'remove_header' in settings['checklist']:
        style_data_conditional.append({'if': {'row_index': 0}, 'backgroundColor': 'grey'})

    return df.to_dict('records'), columns, style_data_conditional




def generate_expectations():
    datatype = None # TODO get selected dropdown datatype from arg
    expectation = html.Div()

    if datatype == datatype_list[0]:  # Object
        pass
    elif datatype == datatype_list[1]:  # Int64
        pass
    elif datatype == datatype_list[2]:  # float64
        pass
    elif datatype == datatype_list[3]:  # bool
        pass
    elif datatype == datatype_list[4]:  # datetime64
        pass
    elif datatype == datatype_list[5]:  # category
        pass

    return [ 
        html.Div([
            expectation,
            html.Div('Not Null Threshold', style={'width':'40%', 'display':'inline-block', 'vertical-align':'top'}),
            html.Div(generate_slider(id('slider_not_null_threshold'), min=0, max=100, step=1, value=1), style={'width':'50%','display':'inline-block'}),
            html.Div(style={'width':'40%', 'display':'inline-block', 'vertical-align':'top'}, id=id('val_not_null_threshold')),
        ]),
    ]
    

@app.callback(Output(id('data_profile'), 'children'), 
            [Input('dataset_setting', 'data'),
            Input(id('button_upload'), 'n_clicks'),
            Input('url', 'pathname')])
def generate_profile(settings, n_clicks, pathname):
    if settings is None or settings['name'] is None: return no_update
    
    result = get_documents(settings['name'], 100)
    df = json_normalize(result)
    columns = list(df.columns)
    detected_datatype_list = list(map(str, df.convert_dtypes().dtypes))

    option_datatype = [
        {'label': 'object', 'value': 'object'},
        {'label': 'string', 'value': 'string'},
        {'label': 'Int64', 'value': 'Int64'},
        {'label': 'datetime64', 'value': 'datetime64'},
        {'label': 'boolean', 'value': 'boolean'},
        {'label': 'category', 'value': 'category'}
    ]

    return (html.Table(
        [html.Tr([
            html.Th('Column'),
            html.Th('Datatype'),
            html.Th('Invalid (%)'),
            html.Th('Result'),
            html.Th(''),
        ])] + 
        [html.Tr([
            html.Td(html.H6(col), id={'type':id('col_column'), 'index': i}),
            html.Td(generate_dropdown({'type':id('col_dropdown_datatype'), 'index': i}, option_datatype, value=dtype)),
            html.Td(html.H6('%', id={'type':id('col_invalid'), 'index': i})),
            html.Td(html.H6('-', id={'type':id('col_result'), 'index': i})),
            html.Td(html.Button('Remove', id={'type':id('col_button_remove'), 'index': i}, style={'background-color':'white'})),
            ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(zip(columns, detected_datatype_list))
        ] +
        [html.Tr([''])],
        style={'width':'100%', 'height':'800px'}, 
        id=id('table_data_profile')))


# Style deleted row
@app.callback(Output({'type':id('row'), 'index': MATCH}, 'style'), 
            [Input({'type':id('col_button_remove'), 'index': MATCH}, 'n_clicks'),
            State({'type':id('row'), 'index': MATCH}, 'style')])
def style_row(n_clicks, style):
    if n_clicks is None: return no_update

    if style is None: newStyle = {'background-color':'grey'}
    else: newStyle = None

    return newStyle




# Store profile
@app.callback(Output('dataset_profile', 'data'),
                Output(id('remove_list'), 'data'),
                [Input(id("tabs_content"), "value"),
                Input({'type':id('col_dropdown_datatype'), 'index': ALL}, 'value'),
                Input({'type':id('col_button_remove'), 'index': ALL}, 'n_clicks'),
                State({'type':id('col_column'), 'index': ALL}, 'children')])
def update_output(tab, datatype, remove_list_n_clicks, column):
    if tab != id('set_data_profile'): return no_update

    column = [c['props']['children'] for c in column]

    # Profile
    profile = {}
    profile['datatype'] = dict(zip(column, datatype))
    profile['expectation'] = {} # TODO Store expectations 

    # Remove Column List
    remove_list = []
    for n_clicks, c in zip(remove_list_n_clicks, column):
        if (n_clicks is not None) and n_clicks%2 == 1:
            remove_list.append(c)

    return profile, remove_list


# Update Datatable in "Review Data" Tab
@app.callback([Output(id('input_datatable'), "data"), 
                Output(id('input_datatable'), 'columns')], 
                [Input(id("tabs_content"), "value"),
                State('dataset_setting', "data"),
                State('dataset_profile', "data"),
                State(id('remove_list'), "data")])
def update_data_table(tab, settings, profile, remove_list):
    if settings is None or settings['name'] is None: return no_update
    if tab != id('review_data'): return no_update
    
    result = get_documents(settings['name'], 250)
    df = json_normalize(result)
    df.insert(0, column='index', value=range(1, len(df)+1))

    # Remove Columns
    df.drop(remove_list, axis=1, inplace=True)

    # Settings
    print(settings)

    # Profile
    # print(profile['datatype'])

    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]
    
    return df.to_dict('records'), columns


# Update typesense dataset with settings/profile/columns to remove
# @app.callback(Output(id('????????'), "??????"), 
#                 [Input(id("button_confirm"), "n_clicks"),
#                 State('dataset_setting', "data"),
#                 State('dataset_profile', "data")])
# def upload_data(n_clicks, setting, profile):
#     if n_clicks is None: return no_update

#     print(setting)
#     print(profile)

    # Update typesense dataset

    # Update typesense dataset profile

#     return no_update
