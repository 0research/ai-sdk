import json
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
    return html.Pre(json.dumps(dataset_data, indent=2), style={'height': '750px', 'font-size':'12px', 'text-align':'left', 'overflow-y':'auto', 'overflow-x':'scroll'})

def display_metadata(dataset):
    columns = [col for col, show in dataset['column'].items() if show == True]
    datatype = {col:dtype for col, dtype in dataset['datatype'].items() if col in columns}
    return (
        html.Div([
            html.Div([
                dbc.InputGroup([
                    dbc.InputGroupText("Dataset ID", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Input(disabled=True, value=dataset['id'], style={'font-size': '12px', 'text-align':'center'}),
                ], className="mb-3 lg"),
                dbc.InputGroup([
                    dbc.InputGroupText("Index Column", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Input(disabled=True, value=dataset['index'], style={'font-size': '12px', 'text-align':'center'}),
                ], className="mb-3 lg"),
                dbc.InputGroup([
                    dbc.InputGroupText("Target Column", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Input(disabled=True, value=dataset['target'], style={'font-size': '12px', 'text-align':'center'}),
                ], className="mb-3 lg"),
            ]),
            html.Table(
                [
                    html.Tr([
                        html.Th('Column'),
                        html.Th('Datatype'),
                        html.Th('Invalid (%)'),
                        html.Th('Result'),
                    ])
                ] + 
                [
                    html.Tr([
                        html.Td(html.P(col), id={'type':id('col_column'), 'index': i}),
                        html.Td(html.P(dtype)),
                        html.Td(html.P('%', id={'type':id('col_invalid'), 'index': i})),
                        html.Td(html.P('-', id={'type':id('col_result'), 'index': i})),
                    ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(datatype.items())
                ],
            )
        ], style={'overflow-x':'scroll', 'overflow-y':'auto'})
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
                dbc.InputGroupText("Action Details", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Textarea(disabled=True, value=str(action['action_details']), style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
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




