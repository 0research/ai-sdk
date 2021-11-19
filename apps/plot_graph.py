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


id = id_factory('plot_graph')

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

options_graph = [
    {'label':'123', 'value':'123'}
]

option_graph = [
    {'label': 'Pie Plot', 'value': 'pie'},
    {'label': 'Line Plot', 'value': 'line'},
    # {'label': 'Bar Plot', 'value': 'bar'},
    # {'label': 'Scatter Plot', 'value': 'scatter'},
    # {'label': 'Box Plot', 'value': 'box'}
]

# Layout
layout = html.Div([
    dbc.Container([
        dbc.Row(dbc.Col(html.H2('Graph Your Data'), className='text-center')),

        dbc.Row([
            dbc.Col(html.H5('Step 1: Set Graph Settings'), width=12),
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("Name", style={'width':'120px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Input(id=id('input_graph_name'), style={'text-align':'center'}),
                ]),
                dbc.InputGroup([
                    dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Textarea(id=id('input_graph_description'), placeholder='Enter Graph Description (Optional)', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                ]),
                dbc.InputGroup([
                    dbc.InputGroupText("Select Graph", style={'width':'120px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Select(options=options_graph, id=id('dropdown_graph'), value=options_graph[0]['value'], style={'min-width':'120px'}, persistence_type='session', persistence=True), 
                ]),
                html.Br(),
                dbc.InputGroup([
                    dbc.Select(options=[], id=id('graph_x'), placeholder='Select X Axis', style={'min-width':'120px'}, persistence_type='session', persistence=True), 
                    dbc.Select(options=[], id=id('graph_y'), placeholder='Select Y Axis', style={'min-width':'120px'}, persistence_type='session', persistence=True), 
                    dbc.Select(options=[], id=id('graph_z'), placeholder='Select Z Axis', style={'min-width':'120px'}, persistence_type='session', persistence=True),    
                ]),
            ], width={"size": 8, 'offset': 2}),
        ], className='text-center bg-light'),

        dbc.Row([
            dbc.Col(html.H5('Step 2: Review Graph'), width=12),
            dcc.Graph(id=id('graph'), style={'height':'550px'}),
        ], className='text-center', style={'margin': '1px'}),

        dbc.Row([
            dbc.Col(dbc.Button(html.H6('Add Graph'), className='btn-primary', id=id('button_plot_graph'), href='/apps/overview', style={'width':'100%'}), width={'size':10, 'offset':1}),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        
    ], fluid=True, id=id('content')),
])



# Generate Graph
@app.callback(Output(id('graph'), 'figure'),
                Input(id('dropdown_graph'), 'value'))
def generate_graph(graph_type):
    print(graph_type)
    return no_update
    return fig



# Button Add Graph
@app.callback(Output(id('graph'), 'figure'),
                Input(id('button_plot_graph'), 'n_clicks'))
def generate_graph(n_clicks):
    print(n_clicks)
    return no_update
    return fig
