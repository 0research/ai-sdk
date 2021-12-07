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
import dash_uploader as du
import requests



def get_upload_component(id):
    return du.Upload(
        id=id,
        max_file_size=1,  # 1 Mb
        filetypes=['csv', 'json', 'jsonl'],
        upload_id=uuid.uuid1(),  # Unique session id
        max_files=100,
        default_style={'height':'150px'},
    )


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('new_dataset')
UPLOAD_FOLDER_ROOT = r"C:\tmp\Uploads"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)


options_type = [
    {'label': 'Rest API', 'value':'rest'},
    {'label': 'Tabular', 'value':'tabular'},
]

tab_list = [
    dbc.Tab(label="Data", tab_id="tab1", disabled=True),
    dbc.Tab(label="Metadata", tab_id="tab2", disabled=True),
]


# Layout
layout = html.Div([
    dcc.Store(id=id('response_store'), storage_type='session'),
    dcc.Store(id=id('num_datasets'), storage_type='memory', data=0),

    dbc.Container([
        # Left Panel
        html.Div([
            dbc.Row([
                # Top Panel
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6('New Dataset')),
                        dbc.CardBody([
                            # dbc.InputGroup([
                            #     dbc.InputGroupText("Name", style={'width':'100px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            #     dbc.Input(id=id('input_name'), style={'min-width':'120px', 'text-align':'center'}), 
                            # ]),
                            # dbc.InputGroup([
                            #     dbc.InputGroupText("Description", style={'width':'100px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            #     dbc.Textarea(id=id('input_description'), style={'height':'80px', 'text-align':'center'}), 
                            # ]),
                            
                            dbc.ButtonGroup([
                                dbc.Button("Tabular / Json", id=id('type1'), outline=True, color="success"),
                                dbc.Button("REST API", id=id('type2'), outline=True, color="primary"),
                            ], style={'margin': '10px 5px 5px 10px', 'display':'flex', 'width':'100%'})
                            # dbc.Select(options=options_type, value=options_type[0]['value'], id=id('dropdown_type'), style={'min-width':'120px', 'text-align':'center'}),
                            
                        ]),
                        dbc.CardBody(html.Table([], id=id('dataset_details')), style={'height': '750px', 'overflow-y':'auto'}),

                        dbc.CardFooter([
                            # html.Button('Preview', id=id('button_preview'), className='btn btn-warning', style={'margin':'20px 10px 0px 0px', 'font-size': '13px', 'font-weight': 'bold', 'width':'49%'}),
                            html.Button('Add', id=id('button_add'), className='btn btn-primary', style={'margin':'20px 0px 0px 0px', 'font-size': '13px', 'font-weight': 'bold', 'width':'49%'})
                        ]),
                    ])
                ], width=12, style={'float':'left'}),

                # # Bottom Panel
                # dbc.Col([
                #     dbc.Card([
                #         dbc.CardHeader(html.H6('Datatable')),
                #         dbc.CardBody(generate_datatable(id('datatable'), height='400px')),
                #     ]),
                # ], width=12, style={'float':'left'}),

            ], className='bg-white text-dark text-center'),
        ], style={'width':'70%', 'float':'left'}),
        
        html.Div([
            dbc.Tabs(tab_list, active_tab=None, id=id("tabs_json")), 
            dbc.Card([
                dbc.CardHeader(html.H6('Json')),
                dbc.CardBody([], id=id('display_dataset_json'), style={'height':'850px'}),
            ]),
        ], style={'width':'29%', 'float':'right', 'margin-left': '5px', 'text-align':'center'})

    ], fluid=True),
])



def generate_tabularjson_details(index):
    return html.Tr([
        html.Td([html.Div(str(index+1), id={'type': id('dataset_index'), 'index': index})], style={'width':'5%'}),
        html.Td([
            dbc.Input(id={'type': id('name'), 'index': index}, placeholder='Enter Dataset Name', style={'height':'30px', 'min-width':'120px', 'text-align':'center', 'width':'250px'}), 
            dbc.Textarea(id={'type': id('description'), 'index': index}, placeholder='Enter Dataset Description', style={'height':'120px', 'text-align':'center', 'width':'250px'}), 
        ], style={'width':'25%'}),
        html.Td([
            html.Div(get_upload_component(id=id('browse_drag_drop')), style={'display':'inline-block', 'width':'49%'}),
            html.Div(dcc.Dropdown(options=[], value=[], id=id('uploaded_files'), multi=True, clearable=True, placeholder=None, style={'height':'150px', 'overflow-y':'auto'}), style={'display':'inline-block', 'width':'49%'})
        ], style={'width':'60%'}),
        html.Td([
            dbc.ButtonGroup([
                dbc.Button('Preview', className='btn btn-outline-warning', id={'type': id('button_preview'), 'index': index}), 
                dbc.Button(' X ', className='btn btn-outline-danger', id={'type': id('button_remove'), 'index': index})
            ], style={'height':'100%'})
        ], style={'width':'20%'}),
    ], id={'type':id('row'), 'index': index})

def generate_restapi_details(index):
    return html.Tr([
        html.Td([html.Div(str(index+1), id={'type': id('dataset_index'), 'index': index})], style={'width':'5%'}),
        html.Td([
            dbc.Input(id={'type': id('name'), 'index': index}, placeholder='Enter Dataset Name', style={'min-width':'120px', 'text-align':'center', 'width':'250px'}), 
            dbc.Textarea(id={'type': id('description'), 'index': index}, placeholder='Enter Dataset Description', style={'height':'80px', 'text-align':'center', 'width':'250px'}), 
        ], style={'width':'25%'}),
        html.Td([
            dbc.InputGroup([
                dbc.InputGroupText("Endpoint", style={'width':'80px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                dbc.Input(id={'type': id('endpoint'), 'index': index}, placeholder='Enter Rest Endpoint', style={'min-width':'250px', 'text-align':'center'}), 
            ]),
            dbc.InputGroup([
                dbc.InputGroupText("API Key", style={'width':'80px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                dbc.Input(id={'type': id('api_key'), 'index': index}, placeholder='Enter API Key', style={'min-width':'250px', 'text-align':'center'}), 
            ]),
        ], style={'width':'60%'}),
        html.Td([
            dbc.ButtonGroup([
                dbc.Button('Preview', className='btn btn-outline-warning', id={'type': id('button_preview'), 'index': index}), 
                dbc.Button(' X ', className='btn btn-outline-danger', id={'type': id('button_remove'), 'index': index})
            ], style={'height':'100%'})
        ], style={'width':'20%'}),
    ], id={'type':id('row'), 'index': index})



@app.callback(
    Output(id('dataset_details'), 'children'),
    Input(id('type1'), 'n_clicks'),
    Input(id('type2'), 'n_clicks'),
    Input({'type': id('button_remove'), 'index': ALL}, 'n_clicks'),
    State(id('dataset_details'), 'children'),
    prevent_initial_call=True
)
def generate_dataset_details(n_clicks_type1, n_clicks_type2, n_clicks_list, dataset_details):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if dataset_details is None: dataset_details = []
    index = 0 if dataset_details is None else len(dataset_details)

    if triggered == id('type1'):
        return (dataset_details + [generate_tabularjson_details(index)])
    elif triggered == id('type2'):
        return (dataset_details + [generate_restapi_details(index)])
    elif id('button_remove') in triggered:
        index = json.loads(triggered)['index']

        print(dataset_details)
        for i in range(len(dataset_details)):
            if 'id' in dataset_details[i]['props']:
                if 'index' in dataset_details[i]['props']['id']:
                    if index == dataset_details[i]['props']['id']['index']:
                        print('delete ', index)
                        del dataset_details[i]

        # del dataset_details[index]
        return dataset_details
    else:
        return no_update



# # Remove Dataset
# @app.callback(
#     Output(id('dataset_details'), 'children'),
#     Input({'type': id('button_remove'), 'index': ALL}, 'n_clicks'),
#     State(id('dataset_details'), 'children'),
# )
# def select_node(n_clicks_list, dataset_details):
#     triggered = callback_context.triggered[0]['prop_id']
#     print('-----------', triggered)
#     print(n_clicks_list)
#     pprint(dataset_details)
#     return no_update


# Button Preview/Add
@app.callback(
    Output(id('response_store'), 'data'),
    Output(id('tabs_json'), 'children'),
    Output(id('tabs_json'), 'active_tab'),
    Input({'type': id('button_preview'), 'index': ALL}, 'n_clicks'),
    State({'type': id('uploaded_files'), 'index': ALL}, 'value'),
    State({'type': id('endpoint'), 'index': ALL}, 'value'),
    State({'type': id('api_key'), 'index': ALL}, 'value'),
    State(id('tabs_json'), 'active_tab'),
)
def store_api(n_clicks_preview, 
                uploaded_filenames,         # Tabular / JSON 
                endpoint, api_key,          # REST API
                active_tab):
    # pprint(n_clicks_preview)
    if any(n_clicks_preview) is None: return no_update

    # Get Data from API
    API_KEY = "F2862F3F-C288-447D-A6D7-A9906475D85B"
    url = 'https://rest.coinapi.io/v1/ohlcv/POLONIEX_SPOT_BTC_USDC/latest?period_id=1MIN'
    headers = {'X-CoinAPI-Key' : API_KEY}
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)

    # Enable Tabs
    tab_list = [
        dbc.Tab(label="Data", tab_id="tab1", disabled=False),
        dbc.Tab(label="Metadata", tab_id="tab2", disabled=False),
    ]
    active_tab = active_tab if active_tab is not None else 'tab1'

    return data, tab_list, active_tab



# Button Preview/Add
# @app.callback(
#     Output(id('display_dataset_json'), 'children'),
#     Input(id('tabs_json'), 'active_tab'),
#     Input(id('response_store'), 'data'),
# )
# def button_preview_add(active_tab, data):
#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
#     out = no_update

#     df = json_normalize(data)

#     if active_tab == 'tab1':
#         out = display_dataset_data(data)

#     elif active_tab == 'tab2':
#         dataset = Dataset(
#             id=None,
#             description=None, 
#             api_data=None, 
#             column={col:True for col in df.columns}, 
#             datatype={col:str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)},
#             expectation = {col:None for col in df.columns}, 
#             index = [], 
#             target = []
#         )
#         out = display_metadata(dataset)

#     return out


# dataset_id = get_session('dataset_id')
# dataset = get_document('dataset', dataset_id)
# df = json_normalize(data)
# df.insert(0, column='index', value=range(1, len(df)+1))
# print(df)
# columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]