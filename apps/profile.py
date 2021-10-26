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


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('profile')

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
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    dcc.Store(id=id('test'), storage_type='session'),

    dbc.Row(dbc.Col(html.H5('Set Data Profile'), width=12)),
    # TODO node_id, description, 
    dbc.Row(dbc.Col(html.Div(id=id('data_profile'), style={'overflow-y': 'auto', 'overflow-x': 'hidden', 'height':'800px'}), width=12)),
    # html.Div(id=id('data_profile')),
    # html.Div(html.Button('Next Step', className='btn btn-primary', id=id('next_button_2')), className='text-center'),
    html.P('hello', id='test1'),
    html.Div(id='nothing'),
    html.Button('one', id='button1'),
    html.Button('two', id='button2'),
])

@app.callback(Output('test1', 'children'), Input('button1', 'n_clicks'))
def one(n_clicks):
    return 'ONE'

@app.callback(Output('test1', 'children'), Input('button2', 'n_clicks'))
def one(n_clicks):
    return 'TWO'

# @app.callback(Output('nothing', 'children'), Input('button3', 'n_clicks'), State('current_dataset', 'data'))
# def one(n_clicks, current_dataset):
#     print(current_dataset)
#     return no_update


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
