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
    {'label':'Line Graph', 'value':'line'},
    {'label':'Pie Plot', 'value':'pie'},
    {'label':'Bar Plot', 'value':'bar'},
    {'label':'Scatter Plot', 'value':'scatter'},
    # {'label':'Box Plot', 'value':'box'},
]


# Layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            # Graph
            dbc.Col([dbc.Select(id=id('dropdown_graph_type'), options=options_graph, value=options_graph[0]['value'], style={'text-align':'center'})], width=12),
            dbc.Col(children=[], id=id('graph'), width=12),

            # Graph Options
            dbc.Col([
                dbc.Col(html.H5('Select Graph Settings'), width=12, className='text-center', style={'margin': '1px'}),
                
                # Line Plot
                dbc.InputGroup([
                    dbc.InputGroupText("X Axis", style={'width':'100%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Select(id=id('x_axis'), style={'display': 'block'}),
                ]),
                dbc.InputGroup([
                    dbc.InputGroupText("Y Axis", style={'width':'80%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Button(' - ', id=id('button_remove_param'), color='dark', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
                    dbc.Button(' + ', id=id('button_add_param'), color='dark', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
                    dbc.Select(id=id('y_axis'), style={'display': 'block'}),
                ]),

                html.Br(),
                dbc.InputGroup([
                    dbc.InputGroupText("Name", style={'width':'100px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Input(id=id('input_story_name'), style={'text-align':'center'}),
                ]),
                dbc.InputGroup([
                    dbc.InputGroupText("Description", style={'width':'100px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'12px'}),
                    dbc.Textarea(id=id('input_story_description'), placeholder='Enter Story Description (Optional)', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                ]),
            ], width={"size": 8, 'offset': 2}),
            dbc.Col(html.Br()),
        ], className='text-center bg-light'),

        # Save 
        dbc.Row([
            dbc.Col(dbc.Button('Save Graph', id=id('button_save_graph'), color='primary', style={'width':'100%', 'margin-right':'1px', 'display':'block'}), width={'size':10, 'offset':1}),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        
    ], fluid=True, id=id('content')),
])
    

@app.callback(
    Output(id('x_axis'), 'options'),
    Output(id('y_axis'), 'value'),
    Input(id('dropdown_graph_type'), 'value'),
)
def select_graph_type(graph_type):
    dataset_id = get_session('dataset_id')
    dataset = get_document('node', dataset_id)

    features = dataset['features'].keys()
    options = [{'label': f, 'value': f} for f in features]
    print(features, options)

    return options, features[0]


@app.callback(
    Output(id('graph'), 'children'),
    Input(id('dropdown_graph_type'), 'value'),
    Input(id('input1'), 'value'),
    Input(id('input2'), 'value'),
    Input(id('input3'), 'value'),
    Input(id('input4'), 'value'),
)
def load_graph():
    dataset_id = get_session('dataset_id')
    dataset = get_document('node', dataset_id)
    df = get_dataset_data(dataset_id)

    if graph_type == 'pie':
        fig = px.pie(df, names=input1, values=input2)
    elif graph_type == 'bar':
        fig = px.bar(df, x=input1, y=input2, barmode=input3)
    elif graph_type == 'line':
        fig = px.line(df, x=input1, y=input2)
    elif graph_type == 'scatter':
        if input3 == '': input3 = None
        fig = px.scatter(df, x=input1, y=input2, size=input3)
    elif graph_type == 'box':
        fig = []
    
    return fig



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