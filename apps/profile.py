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

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('profile')

datatype_list = ['object', 'Int64', 'float64', 'bool', 'datetime64', 'category']
option_datatype = [
        {'label': 'object', 'value': 'object'},
        {'label': 'string', 'value': 'string'},
        {'label': 'Int64', 'value': 'Int64'},
        {'label': 'datetime64', 'value': 'datetime64'},
        {'label': 'boolean', 'value': 'boolean'},
        {'label': 'category', 'value': 'category'}
    ]


# Layout
layout = html.Div([
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    dcc.Store(id=id('tmp'), storage_type='session'),

    dbc.Row(dbc.Col(html.H2('Set Profile'), width=12), style={'text-align':'center'}),
    # TODO node_id, description, 
    dbc.Row(dbc.Col(html.Div(id=id('data_profile'), style={'overflow-y': 'auto', 'overflow-x': 'hidden', 'height':'800px'}), width=12)),
    # html.Div(html.Button('Update Profile', className='btn btn-primary', id=id('button_update_profile')), className='text-center'),

])



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
            [Input('current_node', 'data'),
            Input('url', 'pathname')])
def generate_profile(node_id, pathname):
    if node_id is None: return no_update

    node = client.collections['node'].documents[node_id].retrieve()
    node_data = get_documents(node['id'], 250)
    df = json_normalize(node_data)
    columns = list(df.columns)
    detected_datatype_list = list(map(str, df.convert_dtypes().dtypes))

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
            html.Td([
                html.Button('Index', id={'type':id('col_button_index'), 'index': i}, style={'background-color':'white'}),
                html.Button('Target', id={'type':id('col_button_target'), 'index': i}, style={'background-color':'white'}),
                html.Button('Remove', id={'type':id('col_button_remove'), 'index': i}, style={'background-color':'white'})
            ]),
            ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(zip(columns, detected_datatype_list))
        ] +
        [html.Tr([''])],
        style={'width':'100%', 'height':'800px'}, 
        id=id('table_data_profile')))


# Style Indexed Row
# @app.callback(Output({'type':id('row'), 'index': MATCH}, 'style'), 
#             [Input({'type':id('col_button_index'), 'index': MATCH}, 'n_clicks'),
#             State({'type':id('row'), 'index': MATCH}, 'style')])
# def style_row(n_clicks, style):
#     if n_clicks is None: return no_update

#     if style is None: newStyle = {'background-color':'grey'}
#     else: newStyle = None

#     return newStyle


# Save Profile
@app.callback([Output({'type':id('col_button_index'), 'index': MATCH}, 'style'),
                Output({'type':id('col_button_target'), 'index': MATCH}, 'style')],
                [Input({'type':id('col_dropdown_datatype'), 'index': MATCH}, 'value'),
                Input({'type':id('col_button_index'), 'index': MATCH}, 'n_clicks'),
                Input({'type':id('col_button_target'), 'index': MATCH}, 'n_clicks'),
                Input({'type':id('col_button_remove'), 'index': MATCH}, 'n_clicks'),
                State({'type':id('col_column'), 'index': MATCH}, 'children'),
                State('current_node', 'data')])
def update_output(datatype, n_click_index, n_click_target, n_click_remove, column, node_id):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '': return no_update
    triggered = ast.literal_eval(triggered)

    # Initialize Output Variables
    button_index_style = {}
    button_target_style = {}

    # Retrieve and Update Node Metadata Document
    node = client.collections['node'].documents[node_id].retrieve()
    datatype = ast.literal_eval(node['datatype'])
    datatype.append(node_id)
    node['datatype'] = str(datatype)

    if triggered['type'] == id('col_dropdown_datatype'):
        print(datatype)
    elif triggered['type'] == id('col_button_index'):
        pass
    elif triggered['type'] == id('col_button_target'):
        pass
    elif triggered['type'] == id('col_button_remove'):
        pass

    # print(triggered['type'], triggered['index'])

    return no_update

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
