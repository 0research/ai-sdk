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
    dcc.Store(id=id('index_col'), storage_type='session'),
    dcc.Store(id=id('target_col'), storage_type='session'),

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
    if node_id is None or node_id is '': return no_update

    node = get_document('node', node_id)
    datatype = node['datatype']
    datatype = {col: datatype[col] for col in node['columns']}

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
                html.Button('Index', id={'type':id('col_button_index'), 'index': i}, className=('btn btn-warning' if col in node['index'] else '')),
                html.Button('Target', id={'type':id('col_button_target'), 'index': i}, className=('btn btn-success' if col in node['target'] else '')),
                html.Button('Remove', id={'type':id('col_button_remove'), 'index': i}, style={'background-color':'white'})
            ]),
            ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(datatype.items())
        ] +
        [html.Tr([''])],
        style={'width':'100%', 'height':'800px'}, 
        id=id('table_data_profile')))



# Save Profile
@app.callback([Output({'type':id('col_button_index'), 'index': MATCH}, 'className'),
                Output({'type':id('col_button_target'), 'index': MATCH}, 'className'),
                Output({'type':id('row'), 'index': MATCH}, 'style')],
                [Input({'type':id('col_dropdown_datatype'), 'index': MATCH}, 'value'),
                Input({'type':id('col_button_index'), 'index': MATCH}, 'n_clicks'),
                Input({'type':id('col_button_target'), 'index': MATCH}, 'n_clicks'),
                Input({'type':id('col_button_remove'), 'index': MATCH}, 'n_clicks'),
                State({'type':id('col_column'), 'index': MATCH}, 'children'),
                State('current_node', 'data'),
                State({'type':id('col_button_index'), 'index': MATCH}, 'className'),
                State({'type':id('col_button_target'), 'index': MATCH}, 'className'),], 
                prevent_initial_call=True)
def update_output(datatype, n_click_index, n_click_target, n_click_remove, column, node_id, button_index_class, button_target_class):
    if node_id is None: return no_update
    if callback_context.triggered == [{'prop_id': '.', 'value': None}]: return no_update

    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    triggered = ast.literal_eval(triggered)
    ix = triggered['index']
    column = column['props']['children']

    print('trigg', triggered)

    # Initialize Output Variables
    # button_index_class = ''
    # button_target_class = ''
    row_style = {}
    
    # Retrieve and Update Node Metadata Document
    node = get_document('node', node_id)

    if triggered['type'] == id('col_dropdown_datatype'):
        node['datatype'][column] = datatype

    elif triggered['type'] == id('col_button_index'):
        if column not in node['index']: 
            node['index'].append(column)
            button_index_class = 'btn btn-warning'
        else: 
            node['index'].remove(column)
            button_index_class = ''

    elif triggered['type'] == id('col_button_target'):
        if column not in node['target']: 
            node['target'].append(column)
            button_target_class = 'btn btn-success'
        else: 
            node['target'].remove(column)
            button_target_class = ''

    elif triggered['type'] == id('col_button_remove'):
        node['columns'].remove(column)
        node['columns_deleted'].append(column)
        row_style = {'display': 'none'}

    # Update Typesense Node
    upsert('node', node)

    return button_index_class, button_target_class, row_style


