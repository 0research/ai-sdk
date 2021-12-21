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
import dash_uploader as du
import requests
import copy


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('new_dataset')





# Layout
layout = html.Div([
    dcc.Store(id=id('dataset_data_store'), storage_type='session'),
    html.Datalist([
        html.Option(value='Content-Type'),
        html.Option(value='Accept'),
        html.Option(value='Cookie'),
    ], id=id('headers_autocomplete')),

    dbc.Container([
        # Left Panel
        html.Div([
            dbc.Row([
                # Top Container
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6('New Dataset')),
                        dbc.CardBody([
                            dbc.ButtonGroup([
                                dbc.Button("User Input", id=id('type1'), outline=True, color="success"),
                                dbc.Button("REST API", id=id('type2'), outline=True, color="primary"),
                            ], style={'margin': '10px 5px 5px 10px', 'display':'flex', 'width':'100%'})
                        ]),
                        dbc.CardBody(id=id('dataset_details'), style={'height': '700px', 'overflow-y':'auto'}),

                        dbc.CardFooter([], id=id('footer')),
                    ])
                ], width=12, style={'float':'left'}),

            ], className='bg-white text-dark text-center'),
        ], style={'width':'59%', 'float':'left'}),
        
        # Right Panel
        html.Div([
            dbc.Tabs([], id=id("tabs_node")), 
            dbc.Card([
                dbc.CardHeader([ html.P(id=id('node_name_list'), style={'text-align':'center', 'font-size':'20px', 'font-weight':'bold', 'float':'left', 'width':'100%'}) ]),
                dbc.CardBody(html.Div(id=id('node_content'), style={'min-height': '800px'})),
            ], className='bg-primary', inverse=True),
        ], style={'width':'40%', 'float':'right', 'margin-left': '5px', 'text-align':'center'})
        
    ], fluid=True),
])



@app.callback(
    Output(id('dataset_details'), 'children'),
    Output(id('footer'), 'children'),
    Input(id('type1'), 'n_clicks'),
    Input(id('type2'), 'n_clicks'),
    State(id('dataset_details'), 'children'),
    prevent_initial_call=True
)
def generate_dataset_details(n_clicks_type1, n_clicks_type2, dataset_details):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if dataset_details is None: dataset_details = []
    
    dataset_details, buttons = generate_new_dataset_inputs(id, triggered, extra=True)
        
    return dataset_details, buttons



# Button Preview/Add
@app.callback(
    Output(id('button_preview'), 'n_clicks'),
    Input({'type': id('browse_drag_drop'), 'index': ALL}, 'isCompleted'),
    State(id('button_preview'), 'n_clicks'),
)
def drag_drop(isCompleted, n_clicks):
    if len(isCompleted) == 0: return no_update
    if isCompleted[0] is True:
        # if n_clicks is None: n_clicks = 0
        return 1

# Button Preview
@app.callback(
    Output(id('dataset_data_store'), 'data'),
    Output(id('tabs_node'), 'children'),
    Output(id('tabs_node'), 'active_tab'),
    Input(id('button_preview'), 'n_clicks'),
    State(id('button_preview'), 'value'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'isCompleted'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'upload_id'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'fileNames'),
    State({'type': id('dropdown_method'), 'index': ALL}, 'value'),
    State({'type': id('url'), 'index': ALL}, 'value'),
    State({'type': id('header_key'), 'index': ALL}, 'value'),
    State({'type': id('header_value'), 'index': ALL}, 'value'),
    State({'type': id('param_key'), 'index': ALL}, 'value'),
    State({'type': id('param_value'), 'index': ALL}, 'value'),
    State({'type': id('body_key'), 'index': ALL}, 'value'),
    State({'type': id('body_value'), 'index': ALL}, 'value'),
    State(id('tabs_node'), 'active_tab'),
    prevent_initial_call=True
)
def store_api(n_clicks, dataset_type,
                isCompleted_list, upload_id_list, fileNames_list,                                               # Tabular / JSON 
                method_list, url_list, header_key_list, header_value_list, param_key_list, param_value_list, body_key_list, body_value_list,     # REST API
                active_tab):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '': return no_update
    out = no_update
    tab1_disabled, tab2_disabled = True, True

    # Preview Button Clicked
    if triggered == id('button_preview') and n_clicks is not None:
        tab1_disabled, tab2_disabled = False, False
        active_tab = 'tab1' if active_tab is None else active_tab

        # User Input
        if dataset_type == id('type1') and fileNames_list[0] is not None and isCompleted_list[0] is True: 
            upload_id = upload_id_list[0]
            filename = fileNames_list[0][0]
            root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
            file = (root_folder / filename).as_posix()

            if filename.endswith('.json'):
                file_str = open(file,"r").read().replace('None', '""')
                json_file = json.loads(file_str)
                data = []
                if type(json_file) == list:
                    for i in range(len(json_file)):
                        json_file[i] = flatten(json_file[i])
                    data = json_file
                elif type(json_file) == dict:
                    json_file = flatten(json_file)
                    data.append(json_file)
                df = json_normalize(data)
                
            elif filename.endswith('.csv'):
                df = pd.read_csv(file, sep=',')

            out = df.to_dict('records')

        # Rest API
        elif dataset_type == id('type2'):
            df, details = process_restapi(method_list[0], url_list[0], header_key_list, header_value_list, param_key_list, param_value_list, body_key_list, body_value_list)
            out = df.to_dict('records')

            

    # Enable Tabs
    tab_list = [
        dbc.Tab(label="Data", tab_id="tab1", disabled=tab1_disabled),
        dbc.Tab(label="Metadata", tab_id="tab2", disabled=tab2_disabled),
    ]

    return out, tab_list, active_tab



# Add/Remove Headers
@app.callback(
    Output(id('header_div'), 'children'),
    Input(id('button_add_header'), 'n_clicks'),
    Input(id('button_remove_header'), 'n_clicks'),
    State(id('header_div'), 'children'),
)
def button_add_header(n_clicks_add, n_clicks_remove, header_div):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    
    if triggered == id('button_add_header'):
        new = copy.deepcopy(header_div[-1])
        new['props']['children'][0]['props']['id']['index'] = len(header_div)
        new['props']['children'][1]['props']['id']['index'] = len(header_div)
        new['props']['children'][2]['props']['id']['index'] = len(header_div)
        new['props']['children'][0]['props']['value'] = ''
        new['props']['children'][1]['props']['value'] = ''
        return header_div + [new]

    elif triggered == id('button_remove_header'):
        if len(header_div) <= 1: return no_update
        else: return header_div[:-1]

    else:
        return no_update
# Add/Remove Params
@app.callback(
    Output(id('params_div'), 'children'),
    Input(id('button_add_param'), 'n_clicks'),
    Input(id('button_remove_param'), 'n_clicks'),
    State(id('params_div'), 'children'),
)
def button_add_param(n_clicks_add, n_clicks_remove, params_div):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    
    if triggered == id('button_add_param'):
        new = copy.deepcopy(params_div[-1])
        new['props']['children'][0]['props']['id']['index'] = len(params_div)
        new['props']['children'][1]['props']['id']['index'] = len(params_div)
        new['props']['children'][2]['props']['id']['index'] = len(params_div)
        new['props']['children'][0]['props']['value'] = ''
        new['props']['children'][1]['props']['value'] = ''
        return params_div + [new]

    elif triggered == id('button_remove_param'):
        if len(params_div) <= 1: return no_update
        else: return params_div[:-1]

    else:
        return no_update
# Add/Remove Body
@app.callback(
    Output(id('body_div'), 'children'),
    Input(id('button_add_body'), 'n_clicks'),
    Input(id('button_remove_body'), 'n_clicks'),
    State(id('body_div'), 'children'),
)
def button_add_body(n_clicks_add, n_clicks_remove, body_div):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    
    if triggered == id('button_add_body'):
        new = copy.deepcopy(body_div[-1])
        new['props']['children'][0]['props']['id']['index'] = len(body_div)
        new['props']['children'][1]['props']['id']['index'] = len(body_div)
        new['props']['children'][2]['props']['id']['index'] = len(body_div)
        new['props']['children'][0]['props']['value'] = ''
        new['props']['children'][1]['props']['value'] = ''
        return body_div + [new]

    elif triggered == id('button_remove_body'):
        if len(body_div) <= 1: return no_update
        else: return body_div[:-1]

    else:
        return no_update
   


# Add/Remove Body
@app.callback(
    Output(id('body_div'), 'children'),
    Input(id('button_add_body'), 'n_clicks'),
    Input(id('button_remove_body'), 'n_clicks'),
    State(id('body_div'), 'children'),
)
def button_add_body(n_clicks_add, n_clicks_remove, body_div):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    
    if triggered == id('button_add_body'):
        new = copy.deepcopy(body_div[-1])
        new['props']['children'][0]['props']['id']['index'] = len(body_div)
        new['props']['children'][1]['props']['id']['index'] = len(body_div)
        new['props']['children'][0]['props']['value'] = ''
        new['props']['children'][1]['props']['value'] = ''
        return body_div + [new]

    elif triggered == id('button_remove_body'):
        if len(body_div) <= 1: return no_update
        else: return body_div[:-1]

    else:
        return no_update



# Button Preview
@app.callback(
    Output(id('node_content'), 'children'),
    Input(id('tabs_node'), 'active_tab'),
    Input(id('dataset_data_store'), 'data'),
)
def button_preview(active_tab, data):
    if data is None: return no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    out = no_update    

    if active_tab == 'tab1':
        out = display_dataset_data(data)

    elif active_tab == 'tab2':
        df = json_normalize(data)
        dataset = Dataset(
            id=None,
            name=None,
            description=None,
            documentation=None,
            type='raw_userinput',
            details=None, 
            features={col:str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)},
            expectation = {col:None for col in df.columns}, 
            index = [], 
            target = [],
            graphs = [],
        )
        out = display_metadata(dataset, id)

    return out

# Button Upload Dataset
@app.callback(
    Output('url', 'pathname'),
    Input(id('button_new_dataset'), 'n_clicks'),
    State(id('button_preview'), 'value'),
    State({'type': id('name'), 'index': ALL}, 'value'),
    State({'type': id('description'), 'index': ALL}, 'value'),
    State({'type': id('documentation'), 'index': ALL}, 'value'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'isCompleted'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'upload_id'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'fileNames'),
    State({'type': id('dropdown_method'), 'index': ALL}, 'value'),
    State({'type': id('url'), 'index': ALL}, 'value'),
    State({'type': id('header_key'), 'index': ALL}, 'value'),
    State({'type': id('header_value'), 'index': ALL}, 'value'),
    State({'type': id('param_key'), 'index': ALL}, 'value'),
    State({'type': id('param_value'), 'index': ALL}, 'value'),
    State({'type': id('body_key'), 'index': ALL}, 'value'),
    State({'type': id('body_value'), 'index': ALL}, 'value'),
    State(id('tabs_node'), 'active_tab'),
    prevent_initial_call=True
)
def button_new_dataset(n_clicks, dataset_type, name_list, description_list, documentation_list,
                isCompleted_list, upload_id_list, fileNames_list,               # Tabular / JSON 
                method_list, url_list, header_key_list, header_value_list, param_key_list, param_value_list, body_key_list, body_value_list,     # REST API
                active_tab):
    if n_clicks is None: return no_update
    # User Input
    if dataset_type == id('type1') and fileNames_list[0] is not None and isCompleted_list[0] is True:
        upload_id = upload_id_list[0]
        filename = fileNames_list[0][0]
        root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
        file = (root_folder / filename).as_posix()

        if filename.endswith('.json'):
            file_str = open(file,"r").read().replace('None', '""')
            json_file = json.loads(file_str)
            data = do_flatten(json_file)
            df = json_normalize(data)
            
        elif filename.endswith('.csv'):
            df = pd.read_csv(file, sep=',')

        out = df
        dataset_type = 'raw_userinput'
        details = {'filename': filename}

    # Rest API
    elif dataset_type == id('type2'):
        df, details = process_restapi(method_list[0], url_list[0], header_key_list, header_value_list, param_key_list, param_value_list, body_key_list, body_value_list)
        out = df
        dataset_type = 'raw_restapi'

    name = name_list[0]
    description = description_list[0]
    documentation = documentation_list[0]

    new_dataset(out, name, description, documentation, dataset_type, details)

    return '/apps/search'




