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
id = id_factory('search')

options_search = [
    {"label": "Dataset", "value": 'dataset'},
    {"label": "Project", "value": 'project', "disabled": True},
    {"label": "Question", "value": 'question', "disabled": True},
]

# Layout
layout = html.Div([
    dbc.Container([
        
        dbc.Row([
            html.Br(),
            dbc.Col([
                dbc.RadioItems(
                    options=options_search,
                    value=options_search[0]['value'],
                    id=id('search_type'),
                    inline=True,
                    style={'float':'right'}
                ),
            ], width=12),
        ], className='bg-light'),

        dbc.Row([
            html.Div(id=id('search_result')),
        ], className='text-center', style={'margin': '1px'}),
    ], fluid=True, id=id('content')),
])



@app.callback(Output(id('search_result'), 'children'),
                Input('search', 'value'),
                Input(id('search_type'), 'value'))
def search(search_value, search_type):
    if search_value == '' or search_value is None: return no_update

    if search_type == 'dataset': query_by = ['description', 'column']
    elif search_type == 'project': query_by = ['description']
    elif search_type == 'question': query_by = ['description']

    search_parameters = {
        'q': search_value,
        'query_by'  : query_by,
        'per_page': 250,
    }
    dataset_list = search_documents(search_type, 250, search_parameters)
    
    out = html.Table(
        [
            html.Tr([
                html.Th('No.'),
                html.Th('Description'),
                html.Th('Column'),
                html.Th('Index'),
                html.Th('Target'),
                html.Th(''),
            ])
        ] + 
        [
            html.Tr([
                html.Td(i+1),
                html.Td(dataset['description'], id={'type':id('col_description'), 'index': i}),
                html.Td(str(list(ast.literal_eval(dataset_list[0]['column']).keys())), id={'type':id('col_column'), 'index': i}),
                html.Td(dataset['index'][1:-1], id={'type':id('col_index'), 'index': i}),
                html.Td(dataset['target'][1:-1], id={'type':id('col_target'), 'index': i}),
                html.Td([
                    dbc.Button('View', id={'type':id('col_button'), 'index': i}),
                    # dbc.Button('View', id={'type':id('col_button'), 'index': i}),
                ]),
            ], id={'type':id('row'), 'index': i}) for i, dataset in enumerate(dataset_list)
        ],
        style={'width':'100%', 'height':'800px'}, id=id('table_data_profile')
    )

    return out