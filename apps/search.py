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
    {"label": "Project", "value": 0},
    {"label": "Dataset", "value": 1},
    {"label": "Action", "value": 2},
],

# Layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            html.Br(),
            dbc.Col([
                # dbc.RadioItems(
                #     options=options_search,
                #     value=0,
                #     id=id("search_type"),
                #     inline=True,
                #     persistence=True,
                # ),
                dbc.RadioItems(
                    options=[
                        {"label": "Option 1", "value": 1},
                        {"label": "Option 2", "value": 2},
                    ],
                    value=1,
                    id="radioitems-inline-input",
                    inline=True,
                ),
            ], width=12),
        ], className='text-center bg-light'),

        dbc.Row([
            html.Div(id=id('search_result')),
        ], className='text-center', style={'margin': '1px'}),

        
    ], fluid=True, id=id('content')),
])



@app.callback(Output('search_result', 'children'),
                Input('search', 'value'))
def search(search_value):
    return no_update
    # return html.Table(
    #     [
    #         html.Tr([
    #             html.Th('Column'),
    #             html.Th('Datatype'),
    #             html.Th('Invalid (%)'),
    #             html.Th('Result'),
    #             html.Th(''),
    #         ])
    #     ] + 
    #     [
    #         html.Tr([
    #             html.Td(html.H6(col), id={'type':id('col_column'), 'index': i}),
    #             html.Td(generate_dropdown({'type':id('col_dropdown_datatype'), 'index': i}, option_datatype, value=dtype)),
    #             html.Td(html.H6('%', id={'type':id('col_invalid'), 'index': i})),
    #             html.Td(html.H6('-', id={'type':id('col_result'), 'index': i})),
    #             html.Td([
    #                 html.Button('Index', id={'type':id('col_button_index'), 'index': i}, className=('btn btn-warning' if col in dataset['index'] else '')),
    #                 html.Button('Target', id={'type':id('col_button_target'), 'index': i}, className=('btn btn-success' if col in dataset['target'] else '')),
    #                 html.Button('Remove', id={'type':id('col_button_remove'), 'index': i}, className=('btn btn-danger' if dataset['column'][col] == False else ''))
    #             ]),
    #         ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(datatype.items())
    #     ],
    #     style={'width':'100%', 'height':'800px'}, id=id('table_data_profile')
    # )