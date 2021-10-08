import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
import dash_table
from dash import no_update, callback_context
import json
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from pandas import json_normalize
from itertools import zip_longest
from datetime import datetime

id = id_factory('remove_duplicate')


# Layout
layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id=id('selection_list_store'), storage_type='session'),
    dcc.Store(id=id('merge_strategy_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),

    dbc.Container([
        dbc.Row([
            dbc.Col(html.H5('Title:'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),          
        ], className='text-center', style={'margin': '3px'}),

        dbc.Row([
            dbc.Col(html.H5('Title:'), width=12),
            dbc.Col(dcc.Graph(id=id("heatmap")), width=12),
        ], className='text-center', style={'margin': '3px'}),
        
        dbc.Row([
            dbc.Col(html.H5('Title:'), width=12),
            dbc.Col(html.Div(), width=12),
        ], className='text-center', style={'margin': '3px'}),
    ]),
])


# Update datatable when files upload
@app.callback([Output(id('input_datatable'), "data"), Output(id('input_datatable'), 'columns')], 
                Input('input_data_store', "data"), Input('url', 'pathname'))
def update_data_table(input_data, pathname):
    if input_data == None: return [], []
        
    df = json_normalize(input_data)
    df.insert(0, column='index', value=range(1, len(df)+1))
    json_dict = df.to_dict('records')

    # Convert all values to string
    for i in range(len(json_dict)):
        for key, val in json_dict[i].items():
            if type(json_dict[i][key]) == list:
                json_dict[i][key] = str(json_dict[i][key])

    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    return json_dict, columns


@app.callback(Output(id('heatmap'), 'figure'), Input(id('input_datatable'), 'data'))
def generate_heatmap(data):
    df = px.data.medals_wide(indexed=True)
    # df = pd.DataFrame(data)
    # TODO Algorithm to estimate resemblance of data
    fig = px.imshow(df,
                   labels=dict(x='column', y='column', color='Resemblance'),
                   x=df.columns,
                   y=df.columns)
    return fig