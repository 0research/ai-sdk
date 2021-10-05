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
from itertools import zip_longest
from datetime import datetime
from pandas import json_normalize
from apps.graph import *

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


id = id_factory('overview')


option_date = [
    {'label': 'Minute', 'value': 'minute'},
    {'label': 'Hour', 'value': 'hour'},
    {'label': 'Day', 'value': 'day'},
    {'label': 'Year', 'value': 'year'},
    {'label': 'Month', 'value': 'month'},
]


def card_content(card_header, card_body):
    return [dbc.CardHeader(card_header),
            dbc.CardBody(card_body)]
    


layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id='input_datatype_store', storage_type='session'),
    
    dbc.Container([
        dbc.Row(dbc.Col(html.H1('Overview')), style={'text-align':'center'}),
         dbc.Row([
            dbc.Col(dbc.Card(card_content('Data Frequency', [
                html.Div('Time Format', style={'width':'25%', 'display':'inline-block', 'vertical-align':'top'}),
                html.Div(generate_dropdown(id('dropdown_data_frequency'), option_date), style={'width':'75%', 'display':'inline-block'}),
                html.Div(bar_graph(id('bar_graph_data_frequency'), 'stack')),
                
            ]), color="primary", inverse=True)),

            dbc.Col(dbc.Card('bbb', color="secondary", inverse=True)),

            dbc.Col(dbc.Card('ccc', color="info", inverse=True)),

        ], className="mb-4"),


        dbc.Row([
            dbc.Col(dbc.Card('aaa', color="success", inverse=True)),

            dbc.Col(dbc.Card('bbb', color="warning", inverse=True)),

            dbc.Col(dbc.Card('ccc', color="danger", inverse=True)),

        ], className="mb-4"),

    ], fluid=True),
    
])
