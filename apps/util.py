import json
from typing import List
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

#import dash_bootstrap_components as dbc
from app import dbc # https://dash-bootstrap-components.opensource.faculty.ai/docs/quickstart/

import plotly.express as px

#from app import app # Not being used in utils

from collections import OrderedDict
from dash import dash_table, no_update, callback_context
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff
import os
from pandas import json_normalize
import pandas as pd
import uuid
from apps.constants import *
from apps.typesense_client import *
import requests
import dash_uploader as du
import numpy as np
from pathlib import Path

def id_factory(page: str):
    def func(_id: str):
        return f"{page}-{_id}"
    return func


def generate_tabs(tabs_id, tab_labels, tab_values, tab_disabled):
    return dcc.Tabs(
        id=tabs_id,
        value=tab_values[0],
        children=[
            dcc.Tab(label=label, value=value, disabled=disabled) for label, value, disabled in zip(tab_labels, tab_values, tab_disabled)
        ],
    )

def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True

def get_data(path):
    data = {}
    for file in os.listdir(path):
        full_filename = "%s/%s" % (path, file)
        with open(full_filename,'r') as f:
            data[file] = json.load(f)
    
    return data

def generate_upload(component_id, display_text=None, max_size=1000000):
    if display_text is not None:
        display_text = html.A(display_text)
    else:
        display_text = html.A('Drag and Drop or Click Here to Select Files')

    return dcc.Upload(
        id=component_id,
        children=html.Div([
            display_text
        ]),
        style={
            'width': '90%',
            'height': '120px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': 'auto',
        },
        multiple=True,
        max_size=max_size
    )

def generate_json_tree(component_id, data):
    return html.Div(children=[
        # html.Button('Submit', id='button'),
        # html.Div(dcc.Input(id='input-box', type='text')),
        json_dash.jsondash(
            id=component_id,
            json=data,
            height=800,
            width=600,
            selected_node='',
        ),
    ])

def filter_dict(json_dict, args):
    dict1 = json_dict[:]
    for i in range(len(args)):
        dict1 = dict1[args[i]]

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),
        html.P("Inset X axis data"),
        dcc.Dropdown(id='xaxis-data', options=[{'label': x, 'value': x} for x in df.columns], persistence=True),
        html.P("Inset Y axis data"),
        dcc.Dropdown(id='yaxis-data', options=[{'label': x, 'value': x} for x in df.columns], persistence=True),
        html.Button(id="submit-button", children="Create Graph"),
        html.Hr(),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=15
        ),
        dcc.Store(id='stored-data', data=df.to_dict('records')),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

def flatten_json(data):
    if type(data) == list:
        for i in range(len(data)):
            data[i] = flatten(data[i])
    elif type(data) == dict:
        data = flatten(data)
    return data

def generate_selection(index):
    index = str(index)
    id_select_button = 'select_list_merge_'+index
    id_selected_list = 'selected_list_merge_'+index
    id_button_clear = {'type': 'select_button_merge_'+index, 'index': -1}

    return [
        html.Div(id=id_selected_list, style={'border-style': 'outset', 'margin': '5px'}),
        html.Button('Clear Selection', id=id_button_clear, style={'width':'90%'}),
        html.Br(),
        html.Br(),
        dbc.ButtonGroup(id=id_select_button)]

def json_merge(base, new, merge_strategy):
    schema = {'mergeStrategy': merge_strategy}
    merger = Merger(schema)
    base = merger.merge(base, new)
    return base


def generate_dropdown(component_id, options, value=None, multi=False, placeholder=None, style=None):
    # if value == None: value = options[0]['value']
    return dcc.Dropdown(
        id=component_id,
        options=options,
        value=value,
        searchable=False,
        clearable=False,
        multi=multi,
        placeholder=placeholder,
        style=style,
    )

def display_dataset_data(dataset_data):
    return html.Pre(json.dumps(dataset_data, indent=2), style={'height': '730px', 'font-size':'12px', 'text-align':'left', 'overflow-y':'auto', 'overflow-x':'scroll'})

def display_metadata(dataset, id, disabled=True):
    features = dataset['features']
    options_datatype = [{'label': d, 'value': d} for d in DATATYPE_LIST]
    return (
        html.Div([
            html.Div([
                dbc.InputGroup([
                    dbc.InputGroupText("Dataset ID", style={'width':'30%', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Input(disabled=True, value=dataset['id'], style={'width':'70%', 'font-size': '12px', 'text-align':'center'}),
                ], className="mb-3 lg"),
            ]),
            html.Table(
                [
                    html.Tr([
                        html.Th('Feature', style={'width':'70%'}),
                        html.Th('Datatype', style={'width':'15%'}),
                        html.Th('Invalid', style={'width':'5%'}),
                        html.Th('Result', style={'width':'5%'}),
                        html.Th('', style={'width':'5%'}),
                    ])
                ] + 
                [
                    html.Tr([
                        html.Td(dbc.Input(value=col, disabled=disabled, id={'type':id('col_feature_hidden'), 'index': i}, style={'height':'40px'}), style={'display':'none'}),
                        html.Td(dbc.Input(value=col, disabled=disabled, id={'type':id('col_feature'), 'index': i}, style={'height':'40px'})),
                        html.Td(dbc.Select(options=options_datatype, value=dtype, disabled=disabled, id={'type':id('col_datatype'), 'index': i}, style={'height':'40px'})),
                        html.Td(html.P('%', id={'type':id('col_invalid'), 'index': i})),
                        html.Td(html.P('-', id={'type':id('col_result'), 'index': i})),
                        html.Td(dbc.Button(' X ', id={'type':id('col_button_remove_feature'), 'index': i}, n_clicks=0), style={'display': 'none' if disabled else 'block'}),
                    ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(features.items())
                ],
            className='metadata_table')
        ], style={'overflow-x':'scroll', 'overflow-y':'auto', 'height':'750px'})
    )

def display_action(action):
    return (
        html.Div([
            dbc.InputGroup([
                dbc.InputGroupText("Action ID", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Input(disabled=True, value=action['id'], style={'font-size': '12px', 'text-align':'center'}),
            ], className="mb-3 lg"),
            dbc.InputGroup([
                dbc.InputGroupText("Action", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Input(disabled=True, value=action['action'], style={'font-size': '12px', 'text-align':'center'}),
            ], className="mb-3 lg"),
            dbc.InputGroup([
                dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Textarea(disabled=True, value=action['description'], style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
            ], className="mb-3 lg"),
            dbc.InputGroup([
                dbc.InputGroupText("Changes", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Textarea(disabled=True, value=str(action['changes']), style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
            ], className="mb-3 lg"),
        ])
    )

def generate_options(label_list, input_list):
    return [
        (
            dbc.InputGroup([
                dbc.InputGroupText(label, style={'width':'25%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'10px'}), 
                inp
            ], className="mb-3 lg", style={'display': ('none' if label is None else 'flex')})
        ) for label, inp in zip(label_list, input_list)
    ]

def generate_datatable(component_id, data=[], columns=[], height='450px',
                        metadata_id = None, 
                        cell_editable=False,
                        row_deletable=False, row_selectable=False, selected_row_id = None,
                        col_selectable=False, col_deletable=False, selected_column_id = None,):
    # Datatable            
    datatable_columns = [{"name": c, "id": c, "deletable": col_deletable, "selectable": col_selectable} for c in columns]
    datatable = dash_table.DataTable(
        id=component_id,
        data=data,
        columns=datatable_columns,
        editable=cell_editable,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable=col_selectable,
        row_selectable=row_selectable,
        row_deletable=row_deletable,
        selected_columns=[],
        selected_rows=[],
        page_size= 100,
        style_table={'height': height, 'overflowY': 'auto'},
        style_data={
            'whiteSpace': 'normal',
        },
        css=[{
            'selector': '.dash-spreadsheet td div',
            'rule': '''
                line-height: 15px;
                max-height: 30px; min-height: 30px; height: 30px;
                display: block;
                overflow-y: hidden;
            '''
        }],
        style_data_conditional=style_data_conditional,
    ),

    # Metadata
    if metadata_id is not None:
        metadata = dbc.Card([
            dbc.CardHeader('Metadata'),
            dbc.CardBody('Body')
        ], style={'height': '100%', 'overflow-y': 'auto'})
        width = (9, 3)
    else:
        metadata = html.Div()
        width = (12, 0)

    return dbc.Row([
        dbc.Col(datatable, width=width[0]),
        dbc.Col(metadata, width=width[1]),
    ])


def generate_radio(id, options, label, default_value=0, inline=False):
    return (dbc.Label(label),
            dbc.RadioItems(
                options=[{'label': o, 'value': o} for o in options],                 
                value=options[default_value],
                id=id,
                inline=inline,
            )
    )

def generate_checklist(id, options, label, default_value=0):
    return dbc.FormGroup([
        dbc.Label(label),
        dbc.Checklist(
            options=[{'label': o, 'value': o} for o in options],                 
            value=[options[default_value]],
            id=id,
        )]
    )

def generate_slider(component_id, min=None, max=None, step=None, value=None):
    if value == None: value = 0
    return dcc.Slider(
        id=component_id,
        min=min,
        max=max,
        step=step,
        value=value
    ),

def generate_range_slider(component_id, min=None, max=None, step=None, value=None):
    if value == None: value = [0, 0]
    return dcc.RangeSlider(
        id=component_id,
        min=min,
        max=max,
        step=step,
        value=value
    ),

def generate_difference_history(json_history_1, json_history_2):
    if json_history_1 is None or json_history_2 is None: return []
    if len(json_history_1) < 1  or len(json_history_2) < 1: return []

    # difference_history option 1
    difference, difference_history = None, []
    for i in range(max(len(json_history_1), len(json_history_2))):
        ix1 = min(i, len(json_history_1)-1)
        ix2 = min(i, len(json_history_2)-1)
        difference = diff(json_history_1[ix1], json_history_2[ix2], syntax='symmetric', marshal=True)
        difference_history.append(difference)

    return  difference_history

def generate_number_changes(difference_history):
    num_changes = {}
    for difference in difference_history:
        if type(difference) is list:
            continue
        
        for key in difference.keys():
            if key in num_changes:
                num_changes[key] +=1 
            else:
                num_changes[key] = 1
    return num_changes

def whitespace_remover(df):
    for i in df.columns:
        if df[i].dtype == 'object':
            df[i] = df[i].map(str.strip)
    return df





# New Dataset Inputs
def get_upload_component(component_id, height='100%'):
    return du.Upload(
        id=component_id,
        max_file_size=1,  # 1 Mb
        filetypes=['csv', 'json', 'jsonl'],
        upload_id=uuid.uuid1(),  # Unique session id
        max_files=1,
        default_style={'height':height},
    )

def generate_tabularjson_details(id):
    return [
        html.Div(get_upload_component(component_id={'type': id('browse_drag_drop'), 'index': 0}), style={'width':'100%', 'margin-bottom':'5px'}),
        html.P('File Formats Accepted: ', style={'text-align':'center', 'font-size':'11px', 'margin': '0px'}),
        html.Ol([
            html.Li('CSV'),
            html.Li('JSON'),
            html.Li('List of JSONs'),
        ], style={'text-align':'center', 'font-size':'11px', 'margin': '0px'})
        # html.Div(dcc.Dropdown(options=[], value=[], id=id('uploaded_files'), multi=True, clearable=True, placeholder=None, style={'height':'85px', 'overflow-y':'auto'}), style={'width':'100%'}),
    ]

options_restapi_method =[
    {'label': 'GET', 'value': 'get'},
    {'label': 'POST', 'value': 'post'},
]
def generate_restapi_details(id, extra=True):
    return [
        dbc.InputGroup([
            dbc.InputGroupText("Method", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
            dbc.Select(options=options_restapi_method, id={'type': id('dropdown_method'), 'index': 0}, value=options_restapi_method[0]['value'], style={'text-align':'center'}, persistence=True, persistence_type='session'),
        ]),
        dbc.InputGroup([
            dbc.InputGroupText("URL", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
            dbc.Input(id={'type': id('url'), 'index': 0}, placeholder='Enter URL', style={'text-align':'center'}, persistence=True, persistence_type='session'), 
        ]),

        # Header
        dbc.InputGroup([
            dbc.InputGroupText("Header", style={'width':'80%', 'font-weight':'bold', 'font-size': '12px', 'text-align':'center'}),
            dbc.Button(' - ', id=id('button_remove_header'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
            dbc.Button(' + ', id=id('button_add_header'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
        ]),
        html.Div([
            dbc.InputGroup([
                dbc.Input(id={'type': id('header_key'), 'index': 0}, placeholder='Enter Key', list=id('header_autocomplete'), style={'text-align':'center', 'height':'28px'}, persistence=True, persistence_type='session'),
                dbc.Input(id={'type': id('header_value'), 'index': 0}, placeholder='Enter Value', style={'text-align':'center'}, persistence=True, persistence_type='session'),
                dbc.Button('Use Existing Dataset', id={'type': id('button_header_value'), 'index': 0}, color='info', outline=True, style={'font-size':'10px', 'font-weight':'bold', 'width':'20%', 'height':'28px'}) if extra else "",
                dbc.Input(id={'type': id('header_value_position'), 'index': 0}, style={'display':'none'}, persistence=True, persistence_type='session'),
            ], style={'text-align':'center'}),
        ], id=id('header_div')),

        # Param
        dbc.InputGroup([
            dbc.InputGroupText("Parameter", style={'width':'80%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
            dbc.Button(' - ', id=id('button_remove_param'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
            dbc.Button(' + ', id=id('button_add_param'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
        ]),
        html.Div([
            dbc.InputGroup([
                dbc.Input(id={'type': id('param_key'), 'index': 0}, placeholder='Enter Key', style={'text-align':'center', 'height':'28px'}, persistence=True, persistence_type='session'),
                dbc.Input(id={'type': id('param_value'), 'index': 0}, placeholder='Enter Value', style={'text-align':'center'}, persistence=True, persistence_type='session'),
                dbc.Button('Use Existing Dataset', id={'type': id('button_param_value'), 'index': 0}, color='info', outline=True, style={'font-size':'10px', 'font-weight':'bold', 'width':'20%', 'height':'28px'}) if extra else "",
                dbc.Input(id={'type': id('param_value_position'), 'index': 0}, style={'display':'none'}, persistence=True, persistence_type='session'),
            ]),
        ], id=id('param_div')),

        # Body
        dbc.InputGroup([
            dbc.InputGroupText("Body", style={'width':'80%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
            dbc.Button(' - ', id=id('button_remove_body'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
            dbc.Button(' + ', id=id('button_add_body'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
        ]),
        html.Div([
            dbc.InputGroup([
                dbc.Input(id={'type': id('body_key'), 'index': 0}, placeholder='Enter Key', style={'text-align':'center', 'height':'28px'}, persistence=True, persistence_type='session'),
                dbc.Input(id={'type': id('body_value'), 'index': 0}, placeholder='Enter Value', style={'text-align':'center'}, persistence=True, persistence_type='session'), 
                dbc.Button('Use Existing Dataset', id={'type': id('button_body_value'), 'index': 0}, color='info', outline=True, style={'font-size':'10px', 'font-weight':'bold', 'width':'20%', 'height':'28px'}) if extra else "",
                dbc.Input(id={'type': id('body_value_position'), 'index': 0}, style={'display':'none'}, persistence=True, persistence_type='session'),
            ]),
        ], id=id('body_div')),
    ]


def generate_new_dataset_inputs(id, input_type, extra=False):
    if input_type == id('type1'):  dataset_details_2 = generate_tabularjson_details(id)
    elif input_type == id('type2'): dataset_details_2 = [html.Div(generate_restapi_details(id))]

    dataset_details = [
        dbc.Row([
            dbc.Col([
                dbc.Input(id={'type': id('name'), 'index': 0 }, placeholder='Enter Dataset Name', style={'height':'40px', 'min-width':'120px', 'text-align':'center', 'width':'100%'}, persistence=True, persistence_type='session'), 
                dbc.Textarea(id={'type': id('description'), 'index': 0 }, placeholder='Enter Dataset Description', style={'height':'130px', 'text-align':'center', 'width':'100%'}, persistence=True, persistence_type='session'),
                dbc.Input(id={'type': id('documentation'), 'index': 0 }, placeholder='Enter Documentation URL (Optional) ', style={'height':'40px', 'min-width':'120px', 'text-align':'center', 'width':'100%'}, persistence=True, persistence_type='session'),
            ], width=12),
            dbc.Col(html.Hr(), width=12),
            dbc.Col(dataset_details_2, width=12),
        ]),
    ]
    buttons = dbc.ButtonGroup([
        dbc.Button('Preview', color='success', outline=True, id={'type': id('button_preview'), 'index': 0}, value=input_type, style={'width':'49%'}),
        dbc.Button('Upload', color='warning', outline=True, id={'type': id('button_new_dataset'), 'index': 0}, style={'font-size': '13px', 'font-weight': 'bold', 'width':'49%'}),
    ], style={'width':'100%'})

    return dataset_details, buttons

def do_flatten(json_file):
    data = []
    if type(json_file) == list:
        for i in range(len(json_file)):
            json_file[i] = flatten(json_file[i])
        data = json_file
    elif type(json_file) == dict:
        json_file = flatten(json_file)
        data.append(json_file)
    return data


def process_userinput(upload_id, filename):
    root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
    file = (root_folder / filename).as_posix()
    details = {'filename': filename}
    
    if filename.endswith('.json'):
        json_file = pd.read_json(file).fillna('').to_dict('records')
        data = []
        if type(json_file) == list:
            for row in json_file:
                data.append(flatten(row))
            data = json_file
        elif type(json_file) == dict:
            json_file = flatten(json_file)
            data.append(json_file)
        df = json_normalize(data)
        
    elif filename.endswith('.csv'):
        df = pd.read_csv(file, sep=',')
    
    return df, details


def process_restapi(method, url, header_key_list, header_value_list, param_key_list, param_value_list, body_key_list, body_value_list):
    header = dict(zip(header_key_list, header_value_list))
    param = dict(zip(param_key_list, param_value_list))
    body = dict(zip(body_key_list, body_value_list))
    # Remove empty keys
    if '' in header: header.pop('') 
    if '' in param: param.pop('') 
    if '' in body: body.pop('')
    if None in header: header.pop(None)
    if None in param: param.pop(None) 
    if None in body: body.pop(None)
    
    if method == 'get': response = requests.get(url=url, headers=header, params=param, data=body)
    elif method == 'post': response = requests.post(url=url, headers=header, params=param, data=body)

    result = response.text 
    # CSV
    if result.startswith('[\'') or result.startswith('[\"'):
        result = ast.literal_eval(result)
        df = pd.DataFrame(result)
    # JSON
    else:
        result = do_flatten(json.loads(result))
        for row in result:
            for k, v in row.items():
                if row[k] == []:
                    row[k] = ''
        df = json_normalize(result)
    
    df = df.fillna('')
    details = details = {'method': method, 'url': url, 'header': header, 'param':param}

    return df, details