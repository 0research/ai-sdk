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
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype


id = id_factory('plot_graph')

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

options_graph = [
    {'label':'Pie Plot', 'value':'pie'},
    {'label':'Bar Plot', 'value':'bar'},
    {'label':'Line Graph', 'value':'line'},
    {'label':'Scatter Plot', 'value':'scatter'},
    # {'label':'Box Plot', 'value':'box'},
]


# Layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H5('Step 1: Enter Story Details'), width=12),
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("Name", style={'width':'100px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Input(id=id('input_story_name'), style={'text-align':'center'}),
                    dbc.Checklist(
                        options=[
                            {"label": "Stateful", "value": True}
                        ],
                        value=[],
                        id="switches-inline-input",
                        inline=True,
                        switch=True,
                        style={'width':'190px', 'text-align':'left'}
                    ),
                ]),
                dbc.InputGroup([
                    dbc.InputGroupText("Description", style={'width':'100px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'12px'}),
                    dbc.Textarea(id=id('input_story_description'), placeholder='Enter Story Description (Optional)', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                ]),
                dbc.InputGroup([
                    dbc.InputGroupText("Delimiter", style={'width':'100px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Select(options=[{'label': 'New Story', 'value':'new'}, {'label': 'Story 1', 'value':'story1', 'disabled':True}, {'label': 'Story 2', 'value':'story2', 'disabled':True},], id=id('dropdown_story'), value='new', style={'font-size': '12px'}),
                ]),
            ], width={"size": 8, 'offset': 2}),
            dbc.Col(html.Br()),
        ], className='text-center bg-light'),

        dbc.Row([dbc.Col(html.H5('Step 2: Set Graph Settings'), width=12),], className='text-center', style={'margin': '1px'}),
        dbc.Row(children=[], id=id('graphs')),
        
        dbc.Row(dbc.Col([
            html.Hr(),
            dbc.Button('Add Graph', id=id('add_graph'), style={'width':'100%'}, className='btn btn-warning'),
            html.Hr(),
        ], width={'size':6, 'offset':3})),

        dbc.Row([
            dbc.Col(dbc.Button(html.H6('Save Story'), className='btn-primary', id=id('button_plot_graph'), href='/apps/dashboard', style={'width':'100%'}), width={'size':10, 'offset':1}),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        
    ], fluid=True, id=id('content')),
])


# # Generate New Graph
# def add_graph(i):
#     return [
#         dbc.Col(dbc.Input(id={'type': id('graph_description'), 'index': i}, placeholder='Graph Description (Optional)', style={'text-align':'center', 'height':'40px'})),
#         dbc.Col(dbc.Select(options=options_graph, id={'type': id('dropdown_graph_type'), 'index': i}, value=None, placeholder='Select Graph', style={'text-align':'center'}), width=12),
#         html.Hr(),
#         dbc.Col([], id={'type': id('graph_options'), 'index': i}, width=4),
#         dbc.Col(dcc.Graph(id={'type': id('graph'), 'index': i}, style={'height':'550px'}), width=8),
#     ]
# @app.callback(Output(id('graphs'), 'children'),
#                 Input('url', 'pathname'),
#                 Input(id('add_graph'), 'n_clicks'),
#                 State(id('graphs'), 'children'))
# def generate_graph(pathname, n_clicks, graphs):
#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
#     # On Page Loadfap
#     if triggered == '':
#         return add_graph(0)

#     # On Button Add Graph
#     else:
#         return graphs + add_graph(len(graphs)//5) # 5 elements in add_graph()



    


# # Generate Graph Options
# @app.callback(Output({'type': id('graph_options'), 'index': MATCH}, 'children'),
#                 Input({'type': id('dropdown_graph_type'), 'index': MATCH}, 'value'),
#                 State({'type': id('dropdown_graph_type'), 'index': MATCH}, 'id'))
# def generate_graph_options(graph_type, graph_type_id):
#     if graph_type is None: graph_type = 'pie'
    
#     i = graph_type_id['index']
#     dataset = get_document('node', get_session('dataset_id'))
#     features = dataset['features']
    
#     columns = [col for col, isNotDeleted in dataset['features'].items() if isNotDeleted is True]
#     columns_string = [c for c in columns if is_string_dtype(features[c])]
#     columns_numerical = [c for c in columns if is_numeric_dtype(features[c])]
#     options = [ {'label': col, 'value': col} for col in columns]
#     options_categorical = [ {'label': col, 'value': col} for col in columns_string]
#     options_numerical = [ {'label': col, 'value': col} for col in columns_numerical]
    
#     if graph_type == 'pie':
#         out = generate_options(['Names', 'Values', None, None], 
#                 [generate_dropdown(component_id={'type': id('input1'), 'index': i}, options=options_categorical, value=columns_string[0], multi=False, style={'width':'75%'}),
#                 generate_dropdown(component_id={'type': id('input2'), 'index': i}, options=options_numerical, value=columns_numerical[0], multi=False, style={'width':'75%'}),
#                 dcc.Input(id={'type': id('input3'), 'index': i}),
#                 dcc.Input(id={'type': id('input4'), 'index': i}),
#                 ])

#     if graph_type == 'bar':
#         bar_mode_list = ['stack', 'group']
#         out = generate_options(['X', 'Y', 'Mode', None], 
#                 [generate_dropdown(component_id={'type': id('input1'), 'index': i}, options=options_categorical, value=columns_string[0], multi=False, style={'width':'75%'}),
#                 generate_dropdown(component_id={'type': id('input2'), 'index': i}, options=options_numerical, value=columns_numerical[0], multi=True, style={'width':'75%'}),
#                 dbc.RadioItems(
#                     options=[{'label': bar_mode, 'value': bar_mode} for bar_mode in bar_mode_list],                 
#                     value=bar_mode_list[0],
#                     id={'type': id('input3'), 'index': i},
#                     inline='inline',
#                     style={'margin-left':'10px'}
#                 ),
#                 dcc.Input(id={'type': id('input4'), 'index': i}),
#                 ])

#     if graph_type == 'line':
#         out = generate_options(['X', 'Y', None, None], 
#                 [generate_dropdown(component_id={'type': id('input1'), 'index': i}, options=options_numerical, value=columns_numerical[0], multi=False, style={'width':'75%'}),
#                 generate_dropdown(component_id={'type': id('input2'), 'index': i}, options=options_numerical, value=columns_numerical[0], multi=False, style={'width':'75%'}),
#                 dcc.Input(id={'type': id('input3'), 'index': i}),
#                 dcc.Input(id={'type': id('input4'), 'index': i}),
#                 ])

#     if graph_type == 'scatter':
#         options_numerical2 = options_numerical.copy()
#         options_numerical2.insert(0, {'label': '', 'value':''})
#         out = generate_options(['X', 'Y', 'Size', None], 
#                 [generate_dropdown(component_id={'type': id('input1'), 'index': i}, options=options, value=columns[0], multi=False, style={'width':'75%'}),
#                 generate_dropdown(component_id={'type': id('input2'), 'index': i}, options=options, value=columns[0], multi=False, style={'width':'75%'}),
#                 generate_dropdown(component_id={'type': id('input3'), 'index': i}, options=options_numerical2, value='', multi=False, style={'width':'75%'}),
#                 dcc.Input(id={'type': id('input4'), 'index': i}),
#                 ])

#     if graph_type == 'box':
#         out = []
    
#     return out


# # Generate Graph Data
# @app.callback(Output({'type': id('graph'), 'index': MATCH}, 'figure'),
#                 Input({'type': id('input1'), 'index': MATCH}, 'value'),
#                 Input({'type': id('input2'), 'index': MATCH}, 'value'),
#                 Input({'type': id('input3'), 'index': MATCH}, 'value'),
#                 Input({'type': id('input4'), 'index': MATCH}, 'value'),
#                 State({'type': id('dropdown_graph_type'), 'index': MATCH}, 'value'),
#                 State({'type': id('dropdown_graph_type'), 'index': MATCH}, 'id'))
# def generate_graph_data(input1, input2, input3, input4, graph_type, graph_type_id):
#     i = graph_type_id['index']
#     dataset_id = get_session('dataset_id')
#     dataset = get_document('node', dataset_id)
#     df = get_dataset_data(dataset_id)

#     if graph_type is None:
#         fig = px.pie(df, names=input1, values=input2)
#     elif graph_type == 'pie':
#         fig = px.pie(df, names=input1, values=input2)
#     elif graph_type == 'bar':
#         fig = px.bar(df, x=input1, y=input2, barmode=input3)
#     elif graph_type == 'line':
#         fig = px.line(df, x=input1, y=input2)
#     elif graph_type == 'scatter':
#         if input3 == '': input3 = None
#         fig = px.scatter(df, x=input1, y=input2, size=input3)
#     elif graph_type == 'box':
#         fig = []
    
#     return fig