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
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype
from dash_extensions import EventListener

id = id_factory('feature_engineering')
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True




# Layout
layout = html.Div([
    dbc.Container([
        # Datatable
        dbc.Row([
            # dbc.Col(html.H5('Step 1: Select Column'), width=12),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Dataset', style={'text-align':'center', 'margin':'1px'})),
                    dbc.CardBody([
                        EventListener(
                            id=id('el_datatable'),
                            events=[{"event": "click", "props": ["srcElement.className", "srcElement.innerText"]}],
                            logging=True,
                            children=generate_datatable(id('datatable'), col_selectable="multi", height='320px', metadata_id=id('metadata'), selected_column_id=id('selected_columns')),
                        )
                    ])
                ])
                
            ], width=9),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Metadata', style={'text-align':'center', 'margin':'1px'})),
                    dbc.CardBody([html.Div(id=id('metadata'))]),
                ])
            ]),
        ], style={'height':'320px'}),
        # Body
        dbc.Row([
            dbc.CardHeader(html.H5('Step 2: Select Function')),
            html.Hr(),
            dbc.Col(dcc.Dropdown(options=[], id=id('dropdown_function'), value=None, multi=False, clearable=False, style={'font-size': '20px', 'width':'100%'}), width={'size':10, 'offset':1}),
            html.Hr(),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Before', style={'text-align':'center', 'margin':'1px'})),
                    dbc.CardBody(html.Div(generate_datatable(id('datatable2'), height='380px')), id=id('before'), style={'min-height':'300px'}),
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('After', style={'text-align':'center', 'margin':'1px'})),
                    dbc.CardBody(html.Div(generate_datatable(id('datatable3'), height='380px')), style={'min-height':'300px'}),
                ])
            ], width=6),
            html.Hr(),
            dbc.Col(dbc.Button('Add', className='btn-primary', id=id('button_confirm'), style={'width':'100%'}), width={'size':10, 'offset':1}),
        ], className='text-center bg-light'),

        # Changes 
        dbc.Row([
            dbc.Col(html.H5('Changes (TODO)'), width=12, style={'text-align':'center'}),
            dbc.Col(html.Pre([], id=id('details'), style={'text-align':'left', 'height':'400px', 'background-color':'silver', 'overflow-y':'auto'}), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

        # Confirm Button
        dbc.Row([
            dbc.Col(dbc.Button(html.H6('Confirm'), className='btn-primary', id=id('button_confirm'), style={'width':'100%'}), width={'size':10, 'offset':1}),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
    ], fluid=True, id=id('content')),
])



# dash_extensions Event Listener for datatable (if needed)
# @app.callback(
#     Output("modal", "children"),
#     Input(id('el_datatable'), "event"),
#     Input(id('el_datatable'), "n_events"),
# )
# def click_event(event, n_events):
#     print(n_events, event)
#     return no_update
#     # Check if the click is on the active cell.
#     if not event or "cell--selected" not in event["srcElement.className"]:
#         return no_update
#     # Return the content of the cell.
#     return f"Cell content is {event['srcElement.innerText']}, number of clicks in {n_events}"

# Datatable
@app.callback(Output(id('datatable'), "data"),
                Output(id('datatable'), 'columns'),
                Input('url', 'pathname'))
def generate_datatable(pathname):
    dataset_id = get_session('node_id')
    df = get_dataset_data(dataset_id)
    columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]
    
    return df.to_dict('records'), columns


@app.callback(
    Output(id('datatable'), "style_data_conditional"),
    Output(id('datatable'), "selected_columns"),
    Input(id('datatable'), "active_cell"),
    State(id('datatable'), "style_data_conditional"),
    State(id('datatable'), "selected_columns"),
)
def update_selected_column(active, current_style, selected_columns):
    if active:
        tmp = [row['if'] == {'column_id': active['column_id']} for row in current_style]
        # Remove Column
        if any(tmp):
            del current_style[tmp.index(True)]
            selected_columns.remove(active["column_id"])

        # Select Column
        else:
            current_style.append(
                {
                    "if": {"column_id": active["column_id"]},
                    "backgroundColor": "rgba(150, 180, 225, 0.2)",
                    "border": "1px solid blue",
                },
            )
            selected_columns.append(active["column_id"])
            
    return current_style, selected_columns


@app.callback(
    Output(id('metadata'), 'children'),
    Input('url', 'pathname')
)
def update_metadata(pathname):
    dataset_id = get_session('node_id')
    dataset = get_document('node', dataset_id)
    return display_metadata(dataset, id, disabled=True, height='300px')


# Generate Functions
@app.callback(
    Output(id('dropdown_function'), "options"),
    Output(id('dropdown_function'), "value"),
    Input(id('datatable'), "selected_columns")
)
def generate_functions(selected_columns):
    options_number_functions = [
        {'label': 'Average', 'value':'avg'},
        {'label': 'Sum', 'value':'sum'},
        {'label': 'Maximum', 'value':'max'},
        {'label': 'Minimum', 'value':'min'},
        {'label': 'Count', 'value':'count'},
        {'label': 'Distinct', 'value':'distinct'},
        {'label': 'Normalize', 'value':'normalize', 'disabled':True},
        {'label': 'Low-pass Filter', 'value':'lpf', 'disabled':True},
        {'label': 'High-pass Filter', 'value':'hpf', 'disabled':True},
        {'label': 'Binning', 'value':'binning', 'disabled':True},
        {'label': 'Encode', 'value':'encode', 'disabled':True},
        {'label': 'Fourier Transform', 'value':'fourier_transform', 'disabled':True},
    ]
    options_string_functions = [
        {'label': 'Split by Character', 'value':'split'},
    ]
    options_datetime_functions = [
        {'label': 'None', 'value':'none'},
    ]

    dataset_id = get_session('node_id')
    dataset = get_document('node', dataset_id)
    if len(selected_columns) == 1:
        print(selected_columns[0], dataset['features'][selected_columns[0]])
    elif len(selected_columns) > 1:
        pass

    print(selected_columns)
    return options_number_functions, options_number_functions[0]['value']


# # Select Column 
# @app.callback(Output(id('datatable'), "data"),
#                 Output(id('datatable'), 'columns'),
#                 Output(id('dropdown_selected_columns'), "options"), 
#                 Input('url', 'pathname'))
# def generate_datatable(pathname):
#     return no_update


# # Datatable
@app.callback(Output(id('datatable2'), "data"),
                Output(id('datatable2'), 'columns'),
                Output(id('datatable3'), "data"),
                Output(id('datatable3'), 'columns'),
                Input(id('datatable'), "selected_columns"),
                Input(id('dropdown_function'), "value"))
def generate_datatable(selected_columns, func):
    print(selected_columns, func)
    dataset_id = get_session('node_id')
    df = get_dataset_data(dataset_id)
    columns = [{"name": i, "id": i, "deletable": False, "selectable": False} for i in df.columns]
    options = [{'label':c, 'value':c} for c in df.columns]

    return df.to_dict('records'), columns, df.to_dict('records'), columns