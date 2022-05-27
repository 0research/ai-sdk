from unicodedata import name
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

import time
import ast
from pathlib import Path
import uuid
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype


id = id_factory('plot_graph')

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True





# Layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            # Graph
            dbc.Col([dcc.Graph(id=id('graph'), style={'height': '400px'})], width=12),

            # Graph Options
            dbc.Col([
                dbc.Col(html.H5('Select Graph Settings'), width=12, className='text-center', style={'margin': '1px'}),
                html.Div(generate_graph_inputs(id), id=id('graph_inputs')),
                html.Br(),
                dbc.InputGroup([
                    dbc.InputGroupText("Name", style={'width':'100px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Input(id=id('graph_name'), placeholder='Enter Graph Name', style={'text-align':'center'}),
                    dbc.InputGroupText("Description", style={'width':'100px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'12px'}),
                    dbc.Textarea(id=id('graph_description'), placeholder='Enter Graph Description', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                ]),
            ], width=6),

            # # Datatable
            dbc.Col(generate_datatable(id('datatable'), height='300px'), width=6),

        ], className='text-center bg-light'),

        # Save 
        dbc.Row([
            dbc.Col(dbc.Button('Save Graph', id=id('button_save_graph'), color='primary', style={'width':'100%', 'margin-right':'1px', 'display':'block'}), width={'size':10, 'offset':1}),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        
    ], fluid=True, id=id('content')),
])





# Generate Graph Inputs from Graph Session
@app.callback(
    Output(id('dropdown_graph_type'), 'value'),
    Output(id('line_x'), 'options'),
    Output(id('line_y'), 'options'),
    Output(id('line_x'), 'value'),
    Output(id('line_y'), 'value'),

    Output(id('bar_x'), 'options'),
    Output(id('bar_y'), 'options'),
    Output(id('bar_x'), 'value'),
    Output(id('bar_y'), 'value'),
    Output(id('bar_barmode'), 'value'),

    Output(id('pie_names'), 'options'),
    Output(id('pie_values'), 'options'),
    Output(id('pie_names'), 'value'),
    Output(id('pie_values'), 'value'),

    Output(id('scatter_x'), 'options'),
    Output(id('scatter_y'), 'options'),
    Output(id('scatter_color'), 'options'),
    Output(id('scatter_x'), 'value'),
    Output(id('scatter_y'), 'value'),
    Output(id('scatter_color'), 'value'),

    Output(id('datatable'), 'data'),
    Output(id('datatable'), 'columns'),

    Output(id('graph_name'), 'value'),
    Output(id('graph_description'), 'value'),

    Input('url', 'pathname'),
)
def generate_graph_inputs(pathname):
    return graph_inputs_callback()
    
        

    



# Make Inputs visible
@app.callback(
    Output(id('line_input_container'), 'style'),
    Output(id('bar_input_container'), 'style'),
    Output(id('pie_input_container'), 'style'),
    Output(id('scatter_input_container'), 'style'),
    Input(id('dropdown_graph_type'), 'value'),
    Input('url', 'pathname')
)
def generate_graph_inputs_visibility(graph_type, pathname):
    return graph_input_visibility_callback(graph_type)




# Graph Callbacks
@app.callback(
    Output(id('graph'), 'figure'),
    Input(id('line_input_container'), 'style'),
    Input(id('bar_input_container'), 'style'),
    Input(id('pie_input_container'), 'style'),
    Input(id('scatter_input_container'), 'style'),

    Input(id('line_x'), 'value'),
    Input(id('line_y'), 'value'),
    
    Input(id('bar_x'), 'value'),
    Input(id('bar_y'), 'value'),
    Input(id('bar_barmode'), 'value'),
    
    Input(id('pie_names'), 'value'),
    Input(id('pie_values'), 'value'),
    
    Input(id('scatter_x'), 'value'),
    Input(id('scatter_y'), 'value'),
    Input(id('scatter_color'), 'value'),
)
def display_graph(style1, style2, style3, style4, 
                        line_x, line_y,
                        bar_x, bar_y, bar_barmode,
                        pie_names, pie_values,
                        scatter_x, scatter_y, scatter_color):
    node_id = get_session('node_id')
    return display_graph_inputs_callback(node_id, 
                                style1, style2, style3, style4, 
                                line_x, line_y,
                                bar_x, bar_y, bar_barmode,
                                pie_names, pie_values,
                                scatter_x, scatter_y, scatter_color)


    

@app.callback(
    Output('url', 'pathname'),
    Input(id('button_save_graph'), 'n_clicks'),
    State(id('dropdown_graph_type'), 'value'),
    State(id('graph_inputs'), 'children'),
    State(id('graph_name'), 'value'),
    State(id('graph_description'), 'value'),
)
def save_graph(n_clicks, graph_type, graph_inputs, name, description):
    if n_clicks is None: return no_update
    
    if graph_type == 'line':
        x = graph_inputs[0]['props']['children'][0]['props']['children'][1]['props']['value']
        y = graph_inputs[0]['props']['children'][0]['props']['children'][3]['props']['children']['props']['value']
        graph = {'type': 'line', 'x': x, 'y': y}

    elif graph_type == 'bar':
        x = graph_inputs[1]['props']['children'][0]['props']['children'][1]['props']['value']
        y = graph_inputs[1]['props']['children'][0]['props']['children'][3]['props']['children']['props']['value']
        barmode = graph_inputs[1]['props']['children'][0]['props']['children'][5]['props']['children']['props']['value']
        graph = {'type': 'bar', 'x': x, 'y': y, 'barmode': barmode }

    elif graph_type == 'pie':
        names = graph_inputs[2]['props']['children'][0]['props']['children'][1]['props']['value']
        values = graph_inputs[2]['props']['children'][0]['props']['children'][3]['props']['value']
        graph = {'type': 'pie', 'names': names, 'values': values }

    elif graph_type == 'scatter':
        x = graph_inputs[3]['props']['children'][0]['props']['children'][1]['props']['value']
        y = graph_inputs[3]['props']['children'][0]['props']['children'][3]['props']['value']
        color = graph_inputs[3]['props']['children'][0]['props']['children'][5]['props']['value']
        graph = {'type': 'scatter', 'x': x, 'y': y, 'color': color}
    
    graph_id = get_session('graph_id')
    if graph_id == '':
        graph_id = str(uuid.uuid1())
        log_description = 'Create Graph: {}'.format(graph_id)
    else:
        log_description = 'Update Graph: {}'.format(graph_id)

    node_id = get_session('node_id')
    graph['id'] = graph_id
    graph['name'] = name
    graph['description'] = description

    
    upsert_graph(get_session('project_id'), node_id, graph_id, log_description, graph)

    return '/apps/data_lineage'

