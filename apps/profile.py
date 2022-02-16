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
from apps.constants import *

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('profile')

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
    dcc.Store(id=id('details_store'), storage_type='session'),

    dbc.Row(dbc.Col(html.H2('Set Profile'), width=12), style={'text-align':'center'}),
    dbc.Row(dbc.Col(html.Div(id=id('data_profile'), style={'overflow-y': 'auto', 'overflow-x': 'hidden', 'height':'800px'}), width=12)),
    dbc.Row([
        dbc.Col(html.H5('Changes (TODO)'), width=12, style={'text-align':'center'}),
        dbc.Col(html.Pre([], id=id('details'), style={'text-align':'left', 'height':'400px', 'background-color':'silver', 'overflow-y':'auto'}), width=12),
    ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
    dbc.Row([
        dbc.Col(dbc.Button(html.H6('Confirm'), className='btn-primary', id=id('button_confirm'), style={'width':'100%'}), width={'size':10, 'offset':1}),
    ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

])



def generate_expectations():
    datatype = None # TODO get selected dropdown datatype from arg
    expectation = html.Div()

    if datatype == DATATYPE_LIST[0]:  # Object
        pass
    elif datatype == DATATYPE_LIST[1]:  # Int64
        pass
    elif datatype == DATATYPE_LIST[2]:  # float64
        pass
    elif datatype == DATATYPE_LIST[3]:  # bool
        pass
    elif datatype == DATATYPE_LIST[4]:  # datetime64
        pass
    elif datatype == DATATYPE_LIST[5]:  # category
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
                Input('url', 'pathname'))
def generate_profile(pathname):
    if get_session('node_id') is None: return no_update

    dataset = get_document('node', get_session('node_id'))
    store_session('changed_dataset_profile', dataset) # Clear Changes Session on page load
    datatype = dataset['features']
    # datatype_deleted = {}
    # for col, val in dataset['datatype'].items():
    #     if dataset['features'][col] == True:
    #         datatype[col] = val
    #     else:
    #         datatype[col] = val
    # print(dataset['features'])
    # print(type(dataset['features']['convicts']))
    for col, dtype in datatype.items():
        print(col, dataset['features'][col])

    return (
        html.Table(
            [
                html.Tr([
                    html.Th('Column'),
                    html.Th('Datatype'),
                    html.Th('Invalid (%)'),
                    html.Th('Result'),
                    html.Th(''),
                ])
            ] + 
            [
                html.Tr([
                    html.Td(html.H6(col), id={'type':id('col_column'), 'index': i}),
                    html.Td(generate_dropdown({'type':id('col_dropdown_datatype'), 'index': i}, option_datatype, value=dtype)),
                    html.Td(html.H6('%', id={'type':id('col_invalid'), 'index': i})),
                    html.Td(html.H6('-', id={'type':id('col_result'), 'index': i})),
                    html.Td([
                        html.Button('Index', id={'type':id('col_button_index'), 'index': i}, className=('btn btn-warning' if col in dataset['index'] else '')),
                        html.Button('Target', id={'type':id('col_button_target'), 'index': i}, className=('btn btn-success' if col in dataset['target'] else '')),
                        html.Button('Remove', id={'type':id('col_button_remove'), 'index': i}, className=('btn btn-danger' if dataset['features'][col] == False else ''))
                    ]),
                ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(datatype.items())
            ],
            style={'width':'100%', 'height':'800px'}, id=id('table_data_profile')
        )
    )



# Save Changes
@app.callback(Output({'type':id('col_button_index'), 'index': MATCH}, 'className'),
                Output({'type':id('col_button_target'), 'index': MATCH}, 'className'),
                Output({'type':id('col_button_remove'), 'index': MATCH}, 'className'),
                Output({'type':id('row'), 'index': MATCH}, 'style'),
                Input({'type':id('col_dropdown_datatype'), 'index': MATCH}, 'value'),
                Input({'type':id('col_button_index'), 'index': MATCH}, 'n_clicks'),
                Input({'type':id('col_button_target'), 'index': MATCH}, 'n_clicks'),
                Input({'type':id('col_button_remove'), 'index': MATCH}, 'n_clicks'),
                State({'type':id('col_column'), 'index': MATCH}, 'children'),
                State({'type':id('col_button_index'), 'index': MATCH}, 'className'),
                State({'type':id('col_button_target'), 'index': MATCH}, 'className'),
                State({'type':id('col_button_remove'), 'index': MATCH}, 'className'),
                prevent_initial_call=True)
def update_output(datatype, n_click_index, n_click_target, n_click_remove, column, button_index_class, button_target_class, button_remove_class):
    if get_session('node_id') is None: return no_update
    if callback_context.triggered == [{'prop_id': '.', 'value': None}]: return no_update

    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    triggered = ast.literal_eval(triggered)
    column = column['props']['children']

    # Initialize Output Variables
    # button_index_class = ''
    # button_target_class = ''
    row_style = {}
    
    # Retrieve and Update Node Metadata Document
    if get_session('changed_dataset_profile') is not None:
        dataset = ast.literal_eval(get_session('changed_dataset_profile'))
    else:
        dataset = get_document('node', get_session('node_id'))

    if triggered['type'] == id('col_dropdown_datatype'):
        dataset['datatype'][column] = datatype

    elif triggered['type'] == id('col_button_index'):
        if column not in dataset['index']:
            dataset['index'].append(column)
            button_index_class = 'btn btn-warning'
        else:
            dataset['index'].remove(column)
            button_index_class = ''

    elif triggered['type'] == id('col_button_target'):
        if column not in dataset['target']: 
            dataset['target'].append(column)
            button_target_class = 'btn btn-success'
        else: 
            dataset['target'].remove(column)
            button_target_class = ''

    elif triggered['type'] == id('col_button_remove'):
        dataset['features'][column] = not dataset['features'][column]
        button_remove_class = '' if dataset['features'][column] else 'btn btn-danger'

    # Update Typesense Node
    store_session('changed_dataset_profile', dataset)

    return button_index_class, button_target_class, button_remove_class, row_style


@app.callback(Output(id('details'), 'children'),
                Output(id('details_store'), 'data'),
                Input({'type':id('col_dropdown_datatype'), 'index': ALL}, 'value'),
                Input({'type':id('col_button_index'), 'index': ALL}, 'n_clicks'),
                Input({'type':id('col_button_target'), 'index': ALL}, 'n_clicks'),
                Input({'type':id('col_button_remove'), 'index': ALL}, 'n_clicks'),
                prevent_initial_call=True)
def generate_details(_, _2, _3, _4):
    if get_session('changed_dataset_profile') is None: return no_update
    time.sleep(0.5)

    # Get changes in updated original vs dataset document in the relevant keys
    keys = ['column', 'datatype', 'expectation', 'index', 'target']

    dataset = get_document('node', get_session('node_id'))
    dataset = { k: dataset[k] for k in keys }
    changed_dataset = ast.literal_eval(get_session('changed_dataset_profile'))
    changed_dataset = { k: changed_dataset[k] for k in keys }

    details = diff(dataset, changed_dataset, syntax='symmetric', marshal=True)

    return json.dumps(details, indent=2), details



# Button Confirm
@app.callback(Output('url', 'pathname'),
                Output('modal', 'children'),
                Input(id('button_confirm'), 'n_clicks'),
                State(id('details_store'), 'data'))
def button_confirm(n_clicks, details):
    if n_clicks is None: return no_update
    
    # Unsuccessful
    if False:
        return no_update, 'Fail' 

    # Successful
    else: 
        changed_dataset = ast.literal_eval(get_session('changed_dataset_profile'))
        dataset_id = get_session('node_id')
        action(get_session('project_id'), dataset_id, 'profile', '', details, changed_dataset, search_documents(dataset_id))
        # action(project_id, source_id, action, description, dataset, dataset_data_store)

        return '/apps/data_lineage', 'Success'