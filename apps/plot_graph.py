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

# Graph Options
options_graph = [
    {'label':'Line Graph', 'value':'line'},
    {'label':'Bar Plot', 'value':'bar'},
    {'label':'Pie Plot', 'value':'pie'},
    {'label':'Scatter Plot', 'value':'scatter'},
    # {'label':'Box Plot', 'value':'box'},
]



# Layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            # Graph
            dbc.Col([dbc.Select(id=id('dropdown_graph_type'), options=options_graph, value=options_graph[0]['value'], persistence=True, style={'text-align':'center'})], width=12),
            dbc.Col([dcc.Graph(id=id('graph'), style={'height': '400px'})], width=12),

            # Graph Options
            dbc.Col([
                dbc.Col(html.H5('Select Graph Settings'), width=12, className='text-center', style={'margin': '1px'}),
                
                html.Div([
                    # Line Plot
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText("X Axis", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            dbc.Select(id=id('line_x'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                            dbc.InputGroupText("Y Axis", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            html.Div(dcc.Dropdown(id=id('line_y'), multi=True, options=[], value=None), style={'width':'80%'}),
                        ]),
                    ], style={'display': 'none'}, id=id('line_input_container')),

                    # Bar Plot
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText("X Axis", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            dbc.Select(id=id('bar_x'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                            dbc.InputGroupText("Y Axis", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            html.Div(dcc.Dropdown(id=id('bar_y'), multi=True, options=[], value=None), style={'width':'80%'}),
                            dbc.InputGroupText("Mode", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            html.Div(
                                dbc.RadioItems(
                                    options=[{"label": "Stack", "value": 'stack'}, {"label": "Group", "value": 'group'}, ],
                                    value='stack',
                                    id=id('bar_barmode'),
                                    inline=True,
                                ),
                            )
                        ]),
                    ], style={'display': 'none'}, id=id('bar_input_container')),

                    # Pie Plot
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText("Names", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            dbc.Select(id=id('pie_names'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                            dbc.InputGroupText("Values", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            dbc.Select(id=id('pie_values'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                        ]),
                    ], style={'display': 'none'}, id=id('pie_input_container')),

                    # Scatter Plot
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText("X Axis", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            dbc.Select(id=id('scatter_x'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                            dbc.InputGroupText("Y Axis", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            dbc.Select(id=id('scatter_y'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                            dbc.InputGroupText("Color", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            dbc.Select(id=id('scatter_color'), options=[], value=None, style={'width':'80%', 'text-align': 'center'}),
                        ]),
                    ], style={'display': 'none'}, id=id('scatter_input_container')),
                ], id=id('graph_inputs')),

                html.Br(),
                dbc.InputGroup([
                    dbc.InputGroupText("Name", style={'width':'100px', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                    dbc.Input(id=id('graph_name'), placeholder='Enter Graph Name', style={'text-align':'center'}),
                ]),
                dbc.InputGroup([
                    dbc.InputGroupText("Description", style={'width':'100px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'12px'}),
                    dbc.Textarea(id=id('graph_description'), placeholder='Enter Graph Description', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                ]),

            ], width=6),



            # # Datatable
            dbc.Col(generate_datatable(id('datatable'), height='300px'), width=6),
            dbc.Col(html.Br()),
                
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

    Output(id('graph_name'), 'value'),
    Output(id('graph_description'), 'value'),

    Output(id('datatable'), 'data'),
    Output(id('datatable'), 'columns'),

    Input('url', 'pathname'),
)
def generate_graph_inputs(pathname):
    node_id = get_session('node_id')
    dataset = get_document('node', node_id)
    df = get_dataset_data(node_id)
    features = dataset['features']
    options = [{'label': f, 'value': f} for f in features.keys()]

    features_nonnumerical = [f for f, dtype in features.items() if dtype in DATATYPE_NONNUMERICAL]
    features_numerical = [f for f, dtype in features.items() if dtype in DATATYPE_NUMERICAL]

    options_nonnumerical =[{'label': f, 'value': f} for f in features_nonnumerical]
    options_numerical = [{'label': f, 'value': f} for f in features_numerical]

    default = None if len(list(features.keys())) == 0 else list(features.keys())[0]
    default_nonnumerical = None if len(features_nonnumerical) == 0 else features_nonnumerical[0]
    default_numerical = None if len(features_numerical) == 0 else features_numerical[0]

    columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]

    # Display Clean Graph if no Graph ID exist else Display Selected Graph Values
    graph_id = get_session('graph_id')
    print("GRAPH_ID: ", graph_id, type(graph_id), graph_id is None)
    if graph_id == '':
        return (
            # Graph Type Dropdown
            no_update,
            # Line Inputs
            options_nonnumerical, options_numerical, default_nonnumerical, default_numerical,
            # Bar Inputs
            options_nonnumerical, options_numerical, default_nonnumerical, default_numerical, no_update,
            # Pie Inputs
            options_nonnumerical, options_numerical, default_nonnumerical, default_numerical,
            # Scatter Inputs
            options, options, options, default, default, default,
            # Graph Name & Description
            '', '',
            # Datatable
            df.to_dict('records'), columns,
        )
    else:
        graph = get_document('graph', graph_id)
        if graph['type'] == 'line':
            line_x = graph['x']
            line_y = graph['y']
        elif graph['type'] == 'bar':
            bar_x = graph['x']
            bar_y = graph['y']
            bar_barmode = graph['barmode']
        elif graph['type'] == 'pie':
            pie_names = graph['names']
            pie_values = graph['values']
        elif graph['type'] == 'scatter':
            scatter_x = graph['x']
            scatter_y = graph['y']
            scatter_color = graph['color']
        return (
            # Graph Type Dropdown
            graph['type'],
            # Line Inputs
            options_nonnumerical, options_numerical, line_x, line_y,
            # Bar Inputs
            options_nonnumerical, options_numerical, bar_x, bar_y, bar_barmode,
            # Pie Inputs
            options_nonnumerical, options_numerical, pie_names, pie_values,
            # Scatter Inputs
            options, options, options, scatter_x, scatter_y, scatter_color,
            # Graph Name & Description
            graph['name'], graph['description'],
            # Datatable
            df.to_dict('records'), columns,
        )
        

    



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
    style1, style2, style3, style4 = {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, 
    if graph_type == 'line': style1 = {'display': 'block'}
    if graph_type == 'bar': style2 = {'display': 'block'}
    if graph_type == 'pie': style3 = {'display': 'block'}
    if graph_type == 'scatter': style4 = {'display': 'block'}
    return style1, style2, style3, style4



# Line Graph Callback
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
def display_graph_inputs(style1, style2, style3, style4, 
                        line_x, line_y,
                        bar_x, bar_y, bar_barmode,
                        pie_names, pie_values,
                        scatter_x, scatter_y, scatter_color):
    if style1['display'] != 'none':
        return get_line_figure(line_x, line_y)
    elif style2['display'] != 'none':
        return get_bar_figure(bar_x, bar_y, bar_barmode)
    elif style3['display'] != 'none':
        return get_pie_figure(pie_names, pie_values)
    elif style4['display'] != 'none':
        return get_scatter_figure(scatter_x, scatter_y, scatter_color)
    

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

    node_id = get_session('node_id')
    graph_id = str(uuid.uuid1())
    graph['id'] = graph_id
    graph['name'] = name
    graph['description'] = description

    add_graph_to_project(get_session('project_id'), node_id, graph_id)
    upload_graph(graph)

    return '/apps/data_lineage'

