import json
from typing import List
from dash import dcc, html
from dash.dependencies import Input, Output, State
from app import dbc # https://dash-bootstrap-components.opensource.faculty.ai/docs/quickstart/
import plotly.express as px
from dash import dash_table, no_update, callback_context
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff, symbols
import os
from pandas import json_normalize
import pandas as pd
import uuid
from apps.constants import *
from flask import session
from apps.util import *
import requests
import dash_uploader as du
import numpy as np
from pathlib import Path
import jsonmerge
import typesense
import socket
import ast
import json
from datetime import datetime
from dateutil.parser import parse



# TODO Check if these functions are necessary else remove  
def generate_tabs(tabs_id, tab_labels, tab_values, tab_disabled):
    return dcc.Tabs(
        id=tabs_id,
        value=tab_values[0],
        children=[
            dcc.Tab(label=label, value=value, disabled=disabled) for label, value, disabled in zip(tab_labels, tab_values, tab_disabled)
        ],
    )
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
def display_metadata(dataset, id, disabled=True, height='750px'):
    features = {f['name']:f['datatype'] for f in dataset['features']}
    options_datatype = [{'label': d, 'value': d} for d in DATATYPE_LIST]
    return (html.Div([
            # html.Div([
            #     dbc.InputGroup([
            #         dbc.InputGroupText("Dataset ID", style={'width':'25%', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'10px'}),
            #         dbc.Input(disabled=True, value=dataset['id'], style={'width':'70%', 'font-size': '12px', 'text-align':'center'}),
            #         dbc.InputGroup([
            #             dbc.InputGroupText("Features", style={'width':'25%', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'10px'}),
            #             dbc.Input(disabled=True, value=0, style={'width':'25%', 'font-size': '12px', 'text-align':'center'}),
            #             dbc.InputGroupText("Samples", style={'width':'25%', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'10px'}),
            #             dbc.Input(disabled=True, value=0, style={'width':'25%', 'font-size': '12px', 'text-align':'center'}),
            #         ]),
            #     ], className="mb-3 lg"),
            # ]),
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
                        html.Td(dbc.Button(' X ', id={'type':id('col_button_remove_feature'), 'index': i}, color='danger', outline=True, n_clicks=0), style={'display': 'none' if disabled else 'block'}),
                    ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(features.items())
                ],
            className='metadata_table')
        ], style={'overflow-x':'auto', 'overflow-y':'auto', 'height':height}))
def generate_radio(id, options, label, default_value=0, inline=False):
    return (dbc.Label(label),
            dbc.RadioItems(
                options=[{'label': o, 'value': o} for o in options],                 
                value=options[default_value],
                id=id,
                inline=inline,
            )
    )
def generate_slider(component_id, min=None, max=None, step=None, value=None):
    if value == None: value = 0
    return dcc.Slider(
        id=component_id,
        min=min,
        max=max,
        step=step,
        value=value
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
def get_data(path):
    data = {}
    for file in os.listdir(path):
        full_filename = "%s/%s" % (path, file)
        with open(full_filename,'r') as f:
            data[file] = json.load(f)
    
    return data
# --------------------------------------------------------------------------------

# Unique ID
def id_factory(page: str):
    def func(_id: str):
        return f"{page}-{_id}"
    return func


# Actions
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
def flatten_json(data):
    if type(data) == list:
        for i in range(len(data)):
            data[i] = flatten(data[i])
    elif type(data) == dict:
        data = flatten(data)
    return data
# --------------------------------------------------------------------------------


# Datatable
def generate_datatable(component_id, data=[], columns=[], height='450px',
                        cell_editable=False,
                        row_deletable=False, row_selectable=False,
                        col_selectable=False,
                        style_data_conditional=None,
                        sort_action='none',
                        filter_action='none',
                        dropdown={}, dropdown_data=[]):
    # Datatable
    selectable = True if col_selectable is not False else False

    if style_data_conditional is None:
        style_data_conditional = [
            {
                "if": {"state": "active"},
                "backgroundColor": "rgba(150, 180, 225, 0.2)",
                "border": "1px solid blue",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(0, 116, 217, .03)",
                "border": "1px solid blue",
            },
        ]
    datatable = dash_table.DataTable(
        id=component_id,
        data=data,
        columns=columns,
        editable=cell_editable,
        filter_action=filter_action,
        filter_query='',
        sort_action=sort_action,
        sort_by=[],
        # sort_mode="multi",
        column_selectable=col_selectable,
        row_selectable=row_selectable,
        row_deletable=row_deletable,
        selected_columns=[],
        selected_rows=[],
        page_size= 100,
        dropdown=dropdown,
        dropdown_data=dropdown_data,
        style_table={'height': height, 'overflowY': 'auto'},
        style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white',
            'fontWeight': 'bold',
            'text-align':'center'
        },
        style_filter={
            'text-align':'center'
        },
        style_data={
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white',
            'whiteSpace': 'normal',
            'text-align':'center'
        },
        # css=[{
        #     'selector': '.dash-spreadsheet td div',
        #     'rule': '''
        #         line-height: 15px;
        #         max-height: 30px; min-height: 30px; height: 30px;
        #         display: block;
        #         overflow-y: hidden;
        #     '''
        # }],
        style_data_conditional=style_data_conditional,
    ),

    return datatable
def generate_datatable_data(df, features, show_datatype_dropdown=False, renamable=False):
    dropdown_data = []
    
    # Add First Row for Datatype Dropdown
    df.loc[-1] = {f['id']: f['datatype'] for f in features}
    df.index += 1
    df.sort_index(inplace=True)

    # Get Datatable Columns
    columns = [{'id':'no.', 'name':'no.', 'selectable':False}]
    columns += [{"id": f['id'], "name": f['name'], "selectable": True, 'presentation': 'dropdown', 'renamable': renamable} for f in features]

    # Add Index Column to df
    df.reset_index(inplace=True)
    df.rename(columns = {'index': index_col_name}, inplace=True)
    df.iloc[0,0] = ''

    # Get Dropdown Data
    if show_datatype_dropdown:
        dropdown_data = [ {f['id']: {'options': [{'label': datatype, 'value': datatype} for datatype in DATATYPE_LIST], 'clearable': False} for f in features}]

    return df, columns, dropdown_data
# --------------------------------------------------------------------------------

# Dataset 
def process_fileupload(upload_id, filename):
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
def process_restapi(method, url, header, param, body):
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
    timestamp = str(datetime.now())
    df['timestamp'] = timestamp
    details = details = {'method': method, 'url': url, 'header': header, 'param':param, 'body':body, 'timestamp': timestamp}

    return df, details
def get_upload_component(component_id, height='100%'):
    return du.Upload(
        id=component_id,
        max_file_size=1,  # 1 Mb
        filetypes=['csv', 'json', 'jsonl'],
        upload_id=uuid.uuid1(),  # Unique session id
        max_files=1,
        default_style={'height':height},
    )
def generate_manuafilelupload_details(id):
    return [
        html.Div(get_upload_component(component_id=id('browse_drag_drop')), style={'width':'100%', 'margin-bottom':'5px'}),
        html.P('File Formats Accepted: ', style={'text-align':'center', 'font-size':'11px', 'margin': '0px'}),
        html.Ol([
            html.Li('CSV'),
            html.Li('JSON'),
            html.Li('List of JSONs'),
        ], style={'text-align':'center', 'font-size':'11px', 'margin': '0px'})
        # html.Div(dcc.Dropdown(options=[], value=[], id=id('uploaded_files'), multi=True, clearable=True, placeholder=None, style={'height':'85px', 'overflow-y':'auto'}), style={'width':'100%'}),
    ]
def generate_pastetext(id):
    return [
        dbc.Textarea(size="lg", placeholder="Paste Text Here", style={'height':'200px', 'text-align':'center'}),
        dbc.InputGroup([
            dbc.InputGroupText('Delimiter', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
            dbc.Input(id=id('delimiter'), placeholder='Auto Detect', style={'text-align':'center'}),
        ]),
    ]
def generate_restapi_details(id, extra=True):
    options_restapi_method =[
        {'label': 'GET', 'value': 'get'},
        {'label': 'POST', 'value': 'post'},
    ]    
    return [
        # Inputs
        dbc.InputGroup([
            dbc.InputGroupText("Method", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
            dbc.Select(options=options_restapi_method, id=id('dropdown_method'), value=options_restapi_method[0]['value'], style={'text-align':'center'}, persistence=True, persistence_type='session'),
        ]),
        dbc.InputGroup([
            dbc.InputGroupText("URL", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
            dbc.Input(id=id('url'), placeholder='Enter URL', style={'text-align':'center'}, persistence=True, persistence_type='session'), 
        ]),
        # Header
        dbc.InputGroup([
            dbc.InputGroupText("Header", style={'width':'80%', 'font-weight':'bold', 'font-size': '12px', 'text-align':'center'}),
            dbc.Button(' - ', id=id('button_remove_header'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
            dbc.Button(' + ', id=id('button_add_header'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
        ]), 
        html.Div([], id=id('header_div')),
        # Param
        dbc.InputGroup([
            dbc.InputGroupText("Parameter", style={'width':'80%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
            dbc.Button(' - ', id=id('button_remove_param'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
            dbc.Button(' + ', id=id('button_add_param'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
        ]),
        html.Div([], id=id('param_div')),
        # Body
        dbc.InputGroup([
            dbc.InputGroupText("Body", style={'width':'80%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
            dbc.Button(' - ', id=id('button_remove_body'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
            dbc.Button(' + ', id=id('button_add_body'), color='light', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
        ]),
        html.Div([], id=id('body_div')),
    ]
def generate_restapi_options(id, option_type, index, key_val='', val_val=''):
    return [
        # Inputs
        dbc.InputGroup([
            dbc.Input(id={'type': id('{}_key'.format(option_type)), 'index': index}, value=key_val, placeholder='Enter Key', list=id('header_autocomplete'), style={'text-align':'center', 'height':'28px'}, persistence=True, persistence_type='session'),
            dbc.Input(id={'type': id('{}_value'.format(option_type)), 'index': index}, value=val_val, placeholder='Enter Value', style={'text-align':'center'}, persistence=True, persistence_type='session'),
            dbc.Button('Use Existing Dataset', id={'type': id('button_{}_value'.format(option_type)), 'index': index}, color='info', outline=True, n_clicks=None, style={'font-size':'10px', 'font-weight':'bold', 'width':'20%', 'height':'28px'}),
            dbc.Input(id={'type': id('{}_value_position'.format(option_type)), 'index': index}, style={'display':'none'}, persistence=True, persistence_type='session'),
        ], style={'text-align':'center'}),

        # Modal
        dbc.Modal([
            dbc.ModalHeader(
                dbc.InputGroup([
                    dbc.InputGroupText("Select a Data Source", style={'width':'30%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Select(id={'type': id('{}_datasource_list'.format(option_type)), 'index': index}, options=[], value='', placeholder='Select Data Source', style={'text-align':'center', 'color': 'black'})    
                ]),
            ),
            dbc.ModalBody(generate_datatable({'type': id('{}_value_datatable'.format(option_type)), 'index': index}, height='800px')),
        ], id={'type': id('{}_modal'.format(option_type)), 'index': index})
    ]
def generate_datacatalog_options(id):
    return [
        dbc.Input(type="search", id=id('search_datacatalog'), value='', debounce=False, autoFocus=True, placeholder="Search...", style={'text-align':'center', 'font-size':'15px'}),
        html.Table(html.Div(id=id('table_datacatalog'), style={'overflow-y': 'auto', 'height':'440px', 'width':'100%'}), style={'width':'100%'})
    ]
def generate_datacatalog_table(id, search_value):
    if search_value == '' or search_value is None:
        search_value = '*'
    query_by = 'name, description, details',
    # filter_by = 'type:=[raw_userinput, restapi, datacatalog]'
    search_parameters = {
        'q': search_value,
        'query_by'  : query_by,
        # 'filter_by' : filter_by,
        'per_page': 100,
    }
    dataset_list = search_documents('dataset', 100, search_parameters)

    if len(dataset_list) == 0:
        out = html.H6('No Datasets found for search keywords: "{}".'.format(search_value), style={'text-align':'center'})
    else:
        out = [
            html.Tr([
                html.Th('No.'),
                html.Th('Dataset'),
                # html.Th('Type'),
                html.Th(''),
            ])
        ] + [
            html.Tr([
                html.Td(dbc.Input(value=dataset['id'], id={'type':id('col_dataset_id'), 'index': i}), style={'display':'none'}),
                html.Td(i+1, style={'width':'5%'}),
                html.Td([
                    html.P(dataset['name'], id={'type':id('col_name'), 'index': i}, style={'font-weight':'bold'}),
                    html.P(dataset['description'], id={'type':id('col_description'), 'index': i}),
                    html.P(dataset['documentation']),
                    html.P(dataset['id']),
                ], style={'width':'75%'}),
                # html.Td(dataset['type'], id={'type':id('col_type'), 'index': i}, style={'width':'15%'}),
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button('Preview', value=dataset['id'], id={'type':id('col_button_preview'), 'index': i}, className='btn btn-info'),
                        dbc.Button('Add', value=dataset['id'], id={'type':id('col_button_add'), 'index': i}, className='btn btn-primary'),
                        # dbc.Button('Edit', id={'type':id('col_button_edit'), 'index': i}, className='btn btn-success'),
                        # dbc.Button(' X ', id={'type':id('col_button_remove'), 'index': i}, className='btn btn-danger'),

                        dbc.Tooltip('Preview Dataset Data', target={'type':id('col_button_preview'), 'index': i}),
                        dbc.Tooltip('Add Dataset to Current Project', target={'type':id('col_button_add'), 'index': i}),
                        # dbc.Tooltip('Edit Dataset Details', target={'type':id('col_button_edit'), 'index': i}),
                        # dbc.Tooltip('Remove Dataset', target={'type':id('col_button_remove'), 'index': i}),
                    ], vertical=True),
                ], style={'width':'20%'}),
            ], id={'type':id('row'), 'index': i}) for i, dataset in enumerate(dataset_list)
        ]

    return out
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
# --------------------------------------------------------------------------------

# Merge
def merge_metadata(dataset_id_list, merge_type='objectMerge'):
    dataset = get_document('dataset', dataset_id_list[0])
    dataset['details'] = ''
    features = dataset['features']
    for dataset_id in dataset_id_list[1:]:
        new_dataset = get_document('dataset', dataset_id)
        new_dataset['details'] = ''
        features += new_dataset['features']
        dataset = json_merge(dataset, new_dataset, merge_type)
    dataset['features'] = features
    return dataset
def merge_dataset_data(dataset_id_list, merge_type='objectMerge', idRef=None):
    try:
        # Merge
        data = get_dataset_data(dataset_id_list[0]).to_dict('records')
        if merge_type in ['objectMerge', 'overwrite']:
            for dataset_id in dataset_id_list[1:]:
                new_data = get_dataset_data(dataset_id).to_dict('records')
                data = [json_merge(row, row_new, merge_type) for row, row_new in zip(data, new_data)]

        elif merge_type == 'arrayMergeByIndex':
            schema = {"mergeStrategy": merge_type}
            for dataset_id in dataset_id_list[1:]:
                new_data = get_dataset_data(dataset_id).to_dict('records')
                data = jsonmerge.merge(data, new_data, schema)

        elif merge_type == 'arrayMergeById':
            schema = {"mergeStrategy": merge_type, "mergeOptions": {"idRef": idRef}}
            for dataset_id in dataset_id_list[1:]:
                new_data = get_dataset_data(dataset_id).to_dict('records')
                data = jsonmerge.merge(data, new_data, schema)

        # Remove NaN
        df = json_normalize(data).fillna('')

    except Exception as e:
        print(e, idRef)
        df = pd.DataFrame(columns=[])
    
    return df
def json_merge(base, new, merge_strategy):
    schema = {'mergeStrategy': merge_strategy}
    merger = Merger(schema)
    base = merger.merge(base, new)
    return base
# --------------------------------------------------------------------------------

# Graph
def generate_graph_inputs(id):
    return (
        dbc.Select(id=id('dropdown_graph_type'), options=options_graph, value=options_graph[0]['value'], persistence=True, style={'text-align':'center'}),

        # Line Plot
        html.Div([
            dbc.InputGroup([
                dbc.InputGroupText("X Axis", style={'width':'15%'}),
                dbc.Select(id=id('line_x'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                dbc.InputGroupText("Y Axis", style={'width':'15%'}),
                html.Div(dcc.Dropdown(id=id('line_y'), multi=True, options=[], value=None), style={'width':'85%', 'text-align': 'center'}),
            ]),
        ], style={'display': 'none'}, id=id('line_input_container')),

        # Bar Plot
        html.Div([
            dbc.InputGroup([
                dbc.InputGroupText("X Axis", style={'width':'15%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                dbc.Select(id=id('bar_x'), options=[], value=None, style={'width':'85%', 'text-align': 'center'}),
                dbc.InputGroupText("Y Axis", style={'width':'15%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                html.Div(dcc.Dropdown(id=id('bar_y'), multi=True, options=[], value=None), style={'width':'85%', 'text-align': 'center'}),
                dbc.InputGroupText("Mode", style={'width':'15%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                html.Div(
                    dbc.RadioItems(
                        options=[{"label": "Stack", "value": 'stack'}, {"label": "Group", "value": 'group'}, ],
                        value='stack',
                        id=id('bar_barmode'),
                        inline=True,
                    )
                )
            ]),
        ], style={'display': 'none'}, id=id('bar_input_container')),

        # Pie Plot
        html.Div([
            dbc.InputGroup([
                dbc.InputGroupText("Names", style={'width':'15%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                dbc.Select(id=id('pie_names'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                dbc.InputGroupText("Values", style={'width':'15%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                dbc.Select(id=id('pie_values'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
            ]),
        ], style={'display': 'none'}, id=id('pie_input_container')),

        # Scatter Plot
        html.Div([
            dbc.InputGroup([
                dbc.InputGroupText("X Axis", style={'width':'15%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                dbc.Select(id=id('scatter_x'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                dbc.InputGroupText("Y Axis", style={'width':'15%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                dbc.Select(id=id('scatter_y'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                dbc.InputGroupText("Color", style={'width':'15%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                dbc.Select(id=id('scatter_color'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
            ]),
        ], style={'display': 'none'}, id=id('scatter_input_container')),
    )
def graph_inputs_options_callback(dataset_id, graph_id=''):
    dataset = get_document('dataset', dataset_id)
    df = get_dataset_data(dataset_id)
    features = dataset['features']
    options = [{'label': f['name'], 'value': f['id']} for f in features]

    features_nonnumerical = [f for f in features if f['datatype'] in DATATYPE_NONNUMERICAL]
    features_numerical = [f for f in features if f['datatype'] in DATATYPE_NUMERICAL]

    options_nonnumerical =[{'label': f['name'], 'value': f['id']} for f in features_nonnumerical]
    options_numerical = [{'label': f['name'], 'value': f['id']} for f in features_numerical]

    default = features[0]['id'] if len(features) != 0 else None
    default_nonnumerical = features_nonnumerical[0]['id'] if len(features_nonnumerical) != 0 else None
    default_numerical = features_numerical[0]['id'] if len(features_numerical) != 0 else None

    columns = [{"id": f['id'], "name": f['name'], "deletable": False, "selectable": True} for f in features]

    # Display Clean Graph if no Graph ID exist else Display Selected Graph Values
    if graph_id == '':
        return (
            # Graph Type Dropdown
            no_update,
            # Line Inputs
            options, options, default, default,
            # Bar Inputs
            options_nonnumerical, options_numerical, default_nonnumerical, default_numerical, no_update,
            # Pie Inputs
            options_nonnumerical, options_numerical, default_nonnumerical, default_numerical,
            # Scatter Inputs
            options, options, options, default, default, default,
            # Datatable
            df.to_dict('records'), columns,
            # Graph Name & Description
            '', '',
        )
    else:
        graph = get_document('graph', graph_id)
        input1, input2, input3 = None, None, None
        if graph['type'] == 'line':
            input1 = graph['x']
            input2 = graph['y']
        elif graph['type'] == 'bar':
            input1 = graph['x']
            input2 = graph['y']
            input3 = graph['barmode']
        elif graph['type'] == 'pie':
            input1 = graph['names']
            input2 = graph['values']
        elif graph['type'] == 'scatter':
            input1 = graph['x']
            input2 = graph['y']
            input3 = graph['color']
        return (
            # Graph Type Dropdown
            graph['type'],
            # Line Inputs
            options, options, input1, input2,
            # Bar Inputs
            options, options, input1, input2, input3,
            # Pie Inputs
            options, options, input1, input2,
            # Scatter Inputs
            options, options, options, input1, input2, input3,
            # Datatable
            df.to_dict('records'), columns,
            # Graph Name & Description
            graph['name'], graph['description'],
        )
def graph_input_visibility_callback(graph_type):
    style1, style2, style3, style4 = {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, 
    if graph_type == 'line': style1 = {'display': 'block'}
    if graph_type == 'bar': style2 = {'display': 'block'}
    if graph_type == 'pie': style3 = {'display': 'block'}
    if graph_type == 'scatter': style4 = {'display': 'block'}
    return style1, style2, style3, style4
def get_line_figure(df, x, y, labels=None):
    fig = px.line(df, x=x, y=y, labels=labels)
    fig.update_layout(showlegend=False)
    return fig
def get_bar_figure(df, x, y, barmode, labels=None):
    fig = px.bar(df, x=y, y=x, barmode=barmode, labels=labels)
    fig.update_layout(showlegend=False)
    return fig
def get_pie_figure(df, names, values, labels=None):
    fig = px.pie(df, names=names, values=values, labels=labels)
    fig.update_layout(showlegend=False)
    return fig
def get_scatter_figure(df, x, y, color, labels=None):
    fig = px.scatter(df, x=x, y=y, color=color, labels=labels)
    fig.update_layout(showlegend=False)
    return fig
def upsert_graph(project_id, dataset_id, graph):
    project = get_document('project', project_id)

    if dataset_id in project['graph_dict']:
        if graph['id'] not in project['graph_dict'][dataset_id]:
            project['graph_dict'][dataset_id].append(graph['id'])
    else:
        project['graph_dict'][dataset_id] = [graph['id']]

    upsert('project', project)
    upsert('graph', graph)

# --------------------------------------------------------------------------------



# Logs
def update_logs(project_id, dataset_id, description, timestamp=None):
    project = get_document('project', project_id)
    log_id = str(uuid.uuid1())
    timestamp = str(datetime.now()) if timestamp is None else timestamp
    log = {
        'id': log_id,
        'timestamp': timestamp,
        'description': description,
    }
    if dataset_id in project['logs']: project['logs'][dataset_id].append(log_id)
    else: project['logs'][dataset_id] = [log_id]

    upsert('project', project)
    upsert('logs', log)
# --------------------------------------------------------------------------------

""" Typesense """
# Instantiate
def typesense_client(host, port, protocol, api_key, timeout=2):
    return typesense.Client({
        'nodes': [{
        'host': host, # For Typesense Cloud use xxx.a1.typesense.net
        'port': port,      # For Typesense Cloud use 443
        'protocol': protocol   # For Typesense Cloud use https
        }],
        'api_key': api_key,
        'connection_timeout_seconds': 2
    })
def generate_schema_auto(name):
    if name == 'dataset':
        out = {
            "name": name,
            "fields": [
                {"name": ".*", "type": "string*"},
                {"name": "type", "type": "string*", "facet": True},
            ]
        }
    else:
        out = {
            "name": name,
            "fields": [ {"name": ".*", "type": "string*" } ]
        }
        print(name, out)
    return out
def initialize_typesense():
    print('Initializing Typesense')
    
    if socket.gethostname() == 'DESKTOP-9IOI6RV':
        client = typesense_client('127.0.0.1', '8108', 'http', 'Hu52dwsas2AdxdE')
    else:
        client = typesense_client('39pfe1mawh8i0lx7p-1.a1.typesense.net', '443', 'https', 'ON8Qi0o4Fh8oDWQHVVPeRQx9Unh6VoR3') # Typesense Cloud
        # client = typesense_client('39pfe1mawh8i0lx7p-1.a1.typesense.net', '443', 'https', os.environ['TYPESENSE_API_KEY']) # Typesense Cloud

    
    collection_list = ['project', 'dataset', 'action', 'group', 'graph', 'logs', session_id]
    for name in collection_list:
        try:
            client.collections.create(generate_schema_auto(name))
            print('Create Typesense Collection: ', name)
        except typesense.exceptions.ObjectAlreadyExists:
            pass
            # print('Typesense Object Already Exist')
        except Exception as e:
            print('Initialize Typesense Failed: ', e)
    
    return client
# CRUD
def get_document(collection_id, document_id):
    doc = client.collections[collection_id].documents[document_id].retrieve()
    for k, v in doc.items():
        if len(v)>0:
            if (v[0] == '[' and v[-1] == ']') or (v[0] == '{' and v[-1] == '}'):
                try:
                    doc[k] = ast.literal_eval(v)
                except Exception as e: 
                    print(e)
    return doc
def create(collection_id, document):
    document = {k:str(v) for k, v in document.items()}
    client.collections[collection_id].documents.create(document)
def upsert(collection_id, document):
    document = {k:str(v) for k, v in document.items()}
    client.collections[collection_id].documents.upsert(document)
def search_documents(collection_id, per_page=250, search_parameters=None):
    if search_parameters is None:
        search_parameters = {
            'q': '*',
            'per_page': per_page,
        }
    if collection_id in [c['name'] for c in client.collections.retrieve()]:
        result = client.collections[collection_id].documents.search(search_parameters)
        result = [d['document'] for d in result['hits']]
    else:
        result = None
    return result
def get_dataset_data(dataset_id, features=None):
    dataset = get_document('dataset', dataset_id)
    feature_id_list = [f['id'] for f in dataset['features']] if features is None else features
    data = search_documents(dataset_id)
    df = json_normalize([])
    if data != None:
        df = json_normalize(data)[feature_id_list]
        datatypes = {f['id']: f['datatype'] for f in dataset['features']}
    
       # Convert dtypes
        for f_id, dtype in datatypes.items():
            if dtype == 'int64': 
                df[f_id] = df[f_id].astype(float).astype(datatypes[f_id])  # Pandas bug: require converting to float first

            if dtype == 'float64':
                condition = df[f_id].apply(lambda x: is_dollar(x))
                if (sum(condition) / len(condition)) >= THRESHOLD:
                    df[f_id] = df[f_id].str[1:].astype(float)
                
                df[f_id] = df[f_id].astype(datatypes[f_id])

            if 'datetime' in dtype:
                df[f_id] = pd.to_datetime(df[f_id], infer_datetime_format=True, format='%Y%m%d %H:%M:%S')
        
    return df
def new_project(project_id, project_type):
    project = Project(id=project_id, type=project_type)
    create('project', project)
def get_all_collections():
    return [c['name'] for c in client.collections.retrieve()]
def save_dataset(df, dataset_id, upload_method='', details=''):
    datatypes = get_datatypes(df)

    dataset = get_document('dataset', dataset_id)
    dataset['upload_method'] = upload_method 
    dataset['details'] = details
    dataset['features'] = [{
        'id': str(uuid.uuid1()),
        'name': name, 
        'datatype': dtype,
        'expectation': {},
    } for name, dtype in datatypes.items()]

    # Rename feature name to Unique ID
    mapper = {f['name']:f['id'] for f in dataset['features']}
    df.rename(columns=mapper, inplace=True)

    # Convert all columns to string
    df = df.astype(str)

    # Upload
    upsert('dataset', dataset)
    collection_name_list = [row['name'] for row in client.collections.retrieve()]
    if dataset_id in collection_name_list:
        client.collections[dataset_id].delete()
    client.collections.create(generate_schema_auto(dataset_id))
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
    r = client.collections[dataset_id].documents.import_(jsonl, {'action': 'create'})

# Session
def store_session(key, value):
    client.collections[session_id].documents.upsert({'id': key, 'value': str(value)})
def get_session(key):
    try:
        session_id = 'session1' # Currently all users will use same session. Replace when generate user/session ID
        session_value = client.collections[session_id].documents[key].retrieve()['value']
        session_value = session_value
    except Exception as e:
        # print(e)
        return None
    return session_value
# Cytoscape
def generate_cytoscape_elements(project_id):
    project = get_document('project', project_id)
    
    cDataset_list, cAction_list, cGroup_list, cEdge_list = [], [], [], []
    for d in project['dataset_list']:
        position = {'x': d['position']['x'], 'y': d['position']['y']}
        dataset = get_document('dataset', d['id'])
        cDataset_list.append(cDataset(dataset['id'], dataset['name'], dataset['upload_details'], position, '', dataset['is_source']))

    for a in project['action_list']:
        position = {'x': a['position']['x'], 'y': a['position']['y']}
        action = get_document('action', a['id'])
        cAction_list.append(cAction(action['id'], action['name'], action['state'][-1], position, ''))
        cEdge_list += [cEdge(inp, action['id']) for inp in action['inputs']]
        cEdge_list += [cEdge(action['id'], output) for output in action['outputs']]

    for g in project['group_list']:
        group = get_document('group', g['id'])
        # refer to https://dash.plotly.com/cytoscape/elements 
        # elements.append({'data': {'id': 'parent', 'label': 'Parent'}})
        # Add Upsert Group Node
        pass

    return cDataset_list + cAction_list + cGroup_list + cEdge_list
def add_dataset(project_id):
    project = get_document('project', project_id)
    dataset_id = str(uuid.uuid1())

    x, y = 0 ,0
    while True:
        for d in project['dataset_list']:
            pos_diff_x = abs(d['position']['x'] - x)
            pos_diff_y = abs(d['position']['y'] - y)
            if pos_diff_x < 5 and pos_diff_y < 5:
                x += 20
                y += 20
        break
    project['dataset_list'].append({'id': dataset_id, 'position': {'x': x, 'y': y}})
    dataset = Dataset(id=dataset_id, name='New', description='', is_source=True)
    
    # Upload to Typesense
    upsert('project', project)
    upsert('dataset', dataset)
def add_action(source_id_list):
    # Get Node Position
    default_action = 'transform' if len(source_id_list) == 1 else 'merge'
    project = get_document('project', get_session('project_id'))
    dataset_position_list = [d for d in project['dataset_list'] if d['id'] in source_id_list]
    x, y, num_sources = 0, [], len(source_id_list)
    for d in dataset_position_list:
        x += d['position']['x']
        y.append(d['position']['y'])
    x = x/num_sources
    y = max(y) + 100

    # Add to project, Generate Action & Dataset
    action_id = str(uuid.uuid1())
    dataset_id = str(uuid.uuid1())
    project['action_list'].append({'id': action_id, 'position': {'x': x, 'y': y}})
    project['dataset_list'].append({'id': dataset_id, 'position': {'x': x, 'y': y+100}})
    action = Action(id=action_id, name=default_action, inputs=source_id_list, outputs=[dataset_id])
    dataset = Dataset(id=dataset_id, name='New', description='')
    
    # Upload Changes
    upsert('project', project)
    upsert('action', action)
    upsert('dataset', dataset)
def add_edge(project_id, source_id, destination_id):
    project = get_document('project', project_id)
    edge = source_id + '_' + destination_id
    if edge in project['edge_list']:
        return
    else:
        project['edge_list'].append(edge)
        upsert('project', project)
def remove(project_id, selectedNodeData):
    project = get_document('project', project_id)
    
    for node in selectedNodeData:
        if node['type'] == 'dataset':
            # dataset = get_document('dataset', node['id'])
            if node['is_source'] == 'True':
                project['edge_list'] = [e for e in project['edge_list'] if node['id'] not in e]
                project['dataset_list'] = [a for a in project['dataset_list'] if node['id'] != a['id']]
            else:
                print('Unable to delete Output Node')

        elif node['type'] == 'action':
            action = get_document('action', node['id'])
            project['edge_list'] = [e for e in project['edge_list'] if node['id'] not in e]
            project['action_list'] = [a for a in project['action_list'] if node['id'] != a['id']]
            project['dataset_list'] = [d for d in project['dataset_list'] if d['id'] not in action['outputs']]

            # for e in project['edge_list']:
            #     if node['id'] in e:
            #         project['edge_list'].remove(e)
            #     if e.split('_')[1]

        elif node['type'] == 'group':
            # group = get_document('group', node['id'])
            # del project['group_list'][node['id']]
            pass

        # dataset_id = node['id']
        # edge_list = project['edge_list'].copy()
        # # Debugging
        # if node['type'] == 'processed':
        #     for edge in edge_list:
        #         if dataset_id in edge:
        #             return
        #     project['node_list'] = [node for node in project['node_list'] if node['id'] != dataset_id]

        # # Remove Action or '' (for debugging)
        # elif node['type'] == 'action' or node['type'] == '':
        #     destination_dataset_id_list = [edge.split('_')[1] for edge in edge_list if edge.startswith(dataset_id)]

        #     project['node_list'] = [node for node in project['node_list'] if node['id'] != dataset_id]
        #     for edge in edge_list:
        #         if dataset_id in edge:
        #             project['edge_list'].remove(edge)
        #         if dataset_id == edge.split('_')[0]:
        #             project['node_list'] = [node for node in project['node_list'] if node['id'] != edge.split('_')[1]]
        #         if any(edge.startswith(destination_dataset_id) for destination_dataset_id in destination_dataset_id_list):
        #             return
   
        # # Remove Raw Dataset
        # elif node['type'] == 'raw':
        #     dataset = get_document('dataset', dataset_id)
        #     if dataset['type'] == 'raw':
        #         if any(edge.startswith(dataset_id) for edge in edge_list):
        #             pass
        #         else:
        #             project['node_list'] = [d for d in project['node_list'] if d['id'] != dataset_id]
        #             for edge in [edge for edge in edge_list if edge.startswith(dataset_id)]:
        #                 project['edge_list'].remove(edge)
        # else:
        #     print('[Error] Unable to delete Node: ', dataset_id)
    
    upsert('project', project)
""" -------------------------------------------------------------------------------- """



""" Objects """
# Typesense
def Project(id, type, dataset_list=[], action_list=[], group_list=[], edge_list=[], graph_dict={}, logs={}):
    return {
        'id': id, 
        'type': type,
        'dataset_list': dataset_list,
        'action_list': action_list,
        'group_list': group_list,
        'edge_list': edge_list,
        'graph_dict': graph_dict,
        'logs': logs,
    }
def Dataset(id, name, description='', documentation='', features={}, upload_details={}, is_source='False'):
    return {'id':id, 'name':name, 'description':description, 'documentation':documentation, 'features':features, 'upload_details':upload_details, 'is_source': is_source}
def Action(id, name, description='', state=['amber', 'amber'], details={}, inputs=[], outputs=[]):
    return {'id':id, 'name':name, 'description':description, 'state':state, 'details':details, 'inputs':inputs, 'outputs':outputs}
def Group(id, name, node_list):
    return {'id':id, 'name':name, 'node_list':node_list}
# Cytoscape
def cDataset(id, name='', upload_details={}, position={'x': 0, 'y': 0}, classes='', is_source='False'):
    return {
        'data': {'id': id, 'type': 'dataset', 'name': name, 'upload_details': upload_details, 'is_source': is_source},
        'position': position,
        'classes': classes,
    }
def cAction(id, name, state, position={'x': 0, 'y': 0}, classes=''):
    return {
        'data': {'id': id, 'type': 'action', 'name':name,'state': state},
        'position': position,
        'classes': classes,
    }
def cGroup():
    return {
        
    }
def cEdge(source_id, destination_id, position=None, classes=''):
    return {
        'data': {
                'id': source_id + '_' + destination_id,
                'source': source_id,
                'target': destination_id,
            },
        'selectable': False,
        'position': position,
        'classes': classes,
    }
""" -------------------------------------------------------------------------------- """



def generate_transform_inputs(id):
    return [
        dbc.InputGroup([
            dbc.InputGroupText('Feature Name', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
            dbc.Input(id=id('feature_name'), style={'height':'40px', 'text-align':'center'}, persistence=True),
        ]),

        dbc.InputGroup([
            dbc.InputGroupText('Function Type', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
            dbc.Select(id=id('dropdown_function_type'), options=function_options, value=function_options[0]['value'], style={'height':'40px', 'text-align':'center'}, persistence=True),
        ]),
        
        # Arithmetic Functions
        dbc.InputGroup([
            dbc.InputGroupText('Feature', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Operator', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Feature', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.Select(id=id('dropdown_arithmeticfeature1'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
            dbc.Select(id=id('dropdown_arithmeticfunction'), options=arithmetic_options, value=arithmetic_options[0]['value'], style={'height':'40px', 'text-align':'center'}, persistence=True),
            dbc.Select(id=id('dropdown_arithmeticfeature2'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
        ], id=id('arithmetic_inputs'), style={'display': 'none'}),

        # Comparison Functions
        dbc.InputGroup([
            dbc.InputGroupText('Feature', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Operator', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Feature', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.Select(id=id('dropdown_comparisonfeature1'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
            dbc.Select(id=id('dropdown_comparisonfunction'), options=comparison_options, value=comparison_options[0]['value'], style={'height':'40px', 'text-align':'center'}, persistence=True),
            dbc.Select(id=id('dropdown_comparisonfeature2'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
        ], id=id('comparison_inputs'), style={'display': 'none'}),

        # Custom Input
        dbc.Input(id=id('custom_input'), style={'display':'none', 'height':'40px', 'text-align':'center', 'width':'33.3%', 'float':'right'}, persistence=True),

        # Aggregate Functions
        dbc.InputGroup([
            dbc.InputGroupText('Function', style={'width':'20%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Features', style={'width':'80%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.Select(id=id('dropdown_aggregate_function'), options=aggregate_options, value=aggregate_options[0]['value'], style={'text-align':'center', 'width':'20%'}, persistence=True),
            html.Div(dcc.Dropdown(id=id('dropdown_aggregatefeatures'), multi=True, options=[], value=None, persistence=True), style={'width':'50%'}),
            dbc.Button('Use Features', id=id('button_aggregate_use_features'), color='info', style={'width':'30%'}),
        ], id=id('aggregate_inputs'), style={'display': 'none'}),

        # Sliding Window Functions
        dbc.InputGroup([
            dbc.InputGroupText('Function', style={'width':'25%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Window Size', style={'width':'25%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Feature', style={'width':'50%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.Select(id=id('dropdown_slidingwindow_function'), options=slidingwindow_options, value=slidingwindow_options[0]['value'], style={'text-align':'center', 'width':'25%'}, persistence=True),
            dbc.Select(id=id('dropdown_slidingwindow_size'), options=[], value=None, style={'text-align':'center', 'width':'25%'}, persistence=True),
            dbc.Select(id=id('dropdown_slidingwindow_feature'), options=[], value=None, style={'width':'50%', 'text-align':'center'}, persistence=True),
        ], id=id('slidingwindow_inputs'), style={'display': 'none'}),

        # Format Date Functions
        dbc.InputGroup([
            dbc.InputGroupText('Feature', style={'width':'50%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Format', style={'width':'50%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.Select(id=id('dropdown_formatdatefeature'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
            dbc.Select(id=id('dropdown_dateformat'), options=dateformat_options, value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
        ], id=id('formatdate_inputs'), style={'display': 'none'}),

        # Cumulative Function
        dbc.InputGroup([
            dbc.InputGroupText('Feature', style={'width':'100%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.Select(id=id('dropdown_cumulativefeature'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
        ], id=id('cumulative_inputs'), style={'display': 'none'}),

        # Shift Function
        dbc.InputGroup([
            dbc.InputGroupText('Size', style={'width':'20%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.InputGroupText('Feature', style={'width':'80%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
            dbc.Select(id=id('dropdown_shift_size'), options=[], value=None, style={'text-align':'center', 'width':'20%'}, persistence=True),
            dbc.Select(id=id('dropdown_shift_feature'), options=[], value=None, persistence=True, style={'width':'80%'}),
        ], id=id('shift_inputs'), style={'display': 'none'}),

        # Conditions
        dbc.InputGroup([
            dbc.InputGroup([
                dbc.InputGroupText("Conditions", style={'width':'80%', 'font-weight':'bold', 'font-size': '13px', 'text-align':'center'}),
                dbc.Button(' - ', id=id('button_add_condition'), color='dark', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
                dbc.Button(' + ', id=id('button_remove_condition'), color='dark', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
                # dbc.Select(id=id('dropdown_conditionfeature1'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                # dbc.Select(id=id('dropdown_conditionfunction'), options=comparison_options, value=comparison_options[0]['value'], style={'height':'40px', 'text-align':'center'}, persistence=True),
                # dbc.Select(id=id('dropdown_conditionfeature2'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
            ]),
        ], id=id('condition'), style={'display': 'none'}),
    ]
def get_action_source(action_id, inputs=None, combine_method='join', join_method='left', join_keys=[], merge_type='arrayMergeByIndex', idRef=None, features=None):
    action = get_document('action', action_id)
    if inputs == None:
        inputs = action['inputs']
    else:
        inputs = [inputs] if type(inputs) == str else inputs

    # No Inputs
    if len(inputs) == 0:
        dataset = get_document('dataset', action_id)
        df = pd.DataFrame()

    # Single Source
    elif len(inputs) == 1:
        dataset = get_document('dataset', inputs[0])
        df = get_dataset_data(inputs[0])

    # Multiple Sources (Join/Merge)
    else:
        try:
            dataset = merge_metadata(inputs, 'objectMerge')
            if combine_method == 'join':
                f1_list = None
                f2_list = None
                # if features is not None:
                #     d1_list = [f['id'] for f in get_document('dataset', inputs[0])['features']]
                #     d2_list = [f['id'] for f in get_document('dataset', inputs[1])['features']]
                #     f1_list = [f for f in features if f['id'] in d1_list]
                #     f2_list = [f for f in features if f['id'] in d2_list]

                df1 = get_dataset_data(inputs[0], f1_list)
                df2 = get_dataset_data(inputs[1], f2_list)
                df = df1.merge(df2, how=join_method, left_on=join_keys[0], right_on=join_keys[1])
                for col in df:
                    if df[col].dtype in ['string', 'object']: df[col].fillna("", inplace=True)
                    else: df[col].fillna(0, inplace=True)
                    
            else:
                df = merge_dataset_data(inputs, merge_type, idRef)
                
        except Exception as e:
            df = pd.DataFrame([])
            print('Exception:', e)

    return dataset, df

def generate_options(label_list, input_list):
    return [
        (
            dbc.InputGroup([
                dbc.InputGroupText(label, style={'width':'25%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'10px'}), 
                inp
            ], className="mb-3 lg", style={'display': ('none' if label is None else 'flex')})
        ) for label, inp in zip(label_list, input_list)
    ]




""" Validation """
def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False
def is_dollar(string):
    return string[0] == '$'
""" -------------------------------------------------------------------------------- """


""" General """
def get_datatypes(df):
    datatypes = df.convert_dtypes().dtypes.apply(lambda x: x.name.lower()).to_dict()
    for f_id, dtype in datatypes.items():
        if dtype in ['string', 'object']:
            # Conditions
            condition1 = df[f_id].apply(lambda x: is_dollar(x))
            condition2 = df[f_id].apply(lambda x: is_date(x))

            # Dollar
            if (sum(condition1) / len(condition1)) >= THRESHOLD:
                datatypes[f_id] = 'float64'
            # Date
            elif (sum(condition2) / len(condition2)) >= THRESHOLD:
                datatypes[f_id] = 'datetime'

    return datatypes
""" -------------------------------------------------------------------------------- """

# Init Typesense
client = initialize_typesense()