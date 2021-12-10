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
from urllib.parse import parse_qs, urlparse

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
    dcc.Store(id=id('current_dataset_id_store'), storage_type='memory'),
    dbc.Container([
        dbc.Row([

            # Left Panel
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Data Catalog')),
                    dbc.CardBody([
                        # html.Div([], id=id('search_div')),
                        dbc.Input(type="search", id=id('search'), debounce=False, autoFocus=True, placeholder="Search...", style={'text-align':'center'}),
                        dbc.RadioItems(
                            id=id('search_type'),
                            className="btn-group",
                            inputClassName="btn-check",
                            labelClassName="btn btn-outline-primary",
                            labelCheckedClassName="active",
                            options=options_search,
                            value=options_search[0]['value'],
                        ),
                    ]),
                    dbc.CardBody(html.Div(id=id('search_result'), style={'height':'720px', 'overflow-y':'auto'})),
                ])
            ], width=8),

            # Right Panel
            dbc.Col([
                dbc.Tabs([], id=id("tabs_node")), 
                dbc.Card([
                    dbc.CardHeader([ html.P(id=id('node_name_list'), style={'text-align':'center', 'font-size':'20px', 'font-weight':'bold', 'float':'left', 'width':'100%'}) ]),
                    dbc.CardBody(html.Div(id=id('node_content'), style={'height': '800px', 'overflow-x': 'scroll', 'overflow-y':'auto'})),
                ], className='bg-primary', inverse=True),
            ], width=4),
            

        ], className='text-center', style={'margin': '1px'}),
    ], fluid=True, id=id('content')),
])


# Remove Navbar Search Bar
@app.callback(
    Output('search', 'style'),
    Input('url', 'pathname'),
    State('search', 'style'),
)
def remove_search_bar(pathname, search_style):
    if pathname == '/apps/search':
        if search_style is None: search_style = {}
        search_style['display'] = 'none'
        return search_style
    else:
        search_style

# Add search value to search bar
@app.callback(
    Output(id('search'), 'value'),
    Output(id('search_type'), 'value'),
    Input('search_str_store', 'data'),
)
def generate_search_value(search_str):
    return search_str, 'dataset'


@app.callback(
    Output(id('search_result'), 'children'),
    Input(id('search'), 'value'),
    Input(id('search_type'), 'value')
)
def search(search_value, search_type):
    if search_value == '' or search_value is None: return no_update
    print(search_type)
    if search_type == 'dataset': query_by = ['description', 'column']
    elif search_type == 'project': query_by = ['description']
    elif search_type == 'question': query_by = ['description']

    search_parameters = {
        'q': search_value,
        'query_by'  : query_by,
        'per_page': 250,
    }
    dataset_list = search_documents(search_type, 250, search_parameters)

    if len(dataset_list) > 0:
        out = html.Table(
            [
                html.Tr([
                    html.Th('No.'),
                    html.Th('Name'),
                    html.Th('Description'),
                    html.Th('Type'),
                    html.Th(''),
                ])
            ] + 
            [
                html.Tr([
                    html.Td(dbc.Input(value=dataset['id'], id={'type':id('col_dataset_id'), 'index': i}), style={'display':'none'}),
                    html.Td(i+1),
                    html.Td(dataset['name'], id={'type':id('col_description'), 'index': i}),
                    html.Td(dataset['description'], id={'type':id('col_description'), 'index': i}),
                    html.Td(dataset['type'], id={'type':id('col_type'), 'index': i}),
                    html.Td([
                        dbc.ButtonGroup([
                            dbc.Button('View', id={'type':id('col_button_view'), 'index': i}, className='btn btn-primary'),
                            dbc.Button('Add To Project', id={'type':id('col_button_add_dataset'), 'index': i}, className='btn btn-warning'),
                        ]),
                    ]),
                ], id={'type':id('row'), 'index': i}) for i, dataset in enumerate(dataset_list)
            ],
            style={'width':'100%'}, id=id('table_data_profile')
        )
    else:
        out = html.H6('No Results Found')

    return out


# dbc.InputGroup([
#     dbc.InputGroupText("Params", style={'width':'20%', 'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
#     dbc.Input(id={'type': id('param_key'), 'index': index}, placeholder='Enter Parameter', style={'width':'39%', 'text-align':'center'}),
#     dbc.Input(id={'type': id('param_value'), 'index': index}, placeholder='Enter Value', style={'width':'39%', 'text-align':'center'}), 
# ]),



# On page load, View
@app.callback(
    Output(id('tabs_node'), 'children'),
    Output(id('tabs_node'), 'active_tab'),
    Output(id('current_dataset_id_store'), 'data'),
    Input({'type':id('col_button_view'), 'index': ALL}, 'n_clicks'),
    State(id('tabs_node'), 'active_tab'),
    State({'type':id('col_dataset_id'), 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def generate_tabs(n_clicks_view_list, active_tab, col_dataset_id_list):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    tab1_disabled, tab2_disabled = True, True
    try:
        triggered = json.loads(triggered)
        index = triggered['index']
        if triggered['type'] == id('col_button_view'):
            if n_clicks_view_list[index] is not None:
                tab1_disabled, tab2_disabled = False, False
                active_tab = active_tab if (active_tab is not None) else 'tab1'
        
        tab_list = [
            dbc.Tab(label="JSON", tab_id="tab1", disabled=tab1_disabled),
            dbc.Tab(label="Metadata", tab_id="tab2", disabled=tab2_disabled),
        ]
        return tab_list, active_tab, col_dataset_id_list[index]

    except Exception as e:
        pass
        



# Display Dataset
@app.callback(
    Output(id('node_name_list'), 'children'),
    Output(id('node_content'), 'children'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('current_dataset_id_store'), 'data'),
)
def display(active_tab, dataset_id):
    if dataset_id is None: return no_update
    out = []
    
    dataset = get_document('dataset', dataset_id)
    name = html.Div(dataset['description'], id=id(dataset['id']), contentEditable='true', className="badge border border-info text-wrap")

    if active_tab == 'tab1':
        dataset_data_store = get_dataset_data_store(dataset['id']).to_dict('records')
        out = [dbc.Input(id=id('search_json'), placeholder='Search', style={'text-align':'center'})] + [display_dataset_data_store(dataset_data_store)]

    elif active_tab == 'tab2':
        dataset = get_document('dataset', dataset['id'])
        out = out + [display_metadata(dataset)]
        out = [dbc.CardBody(dbc.Button('Modify Metadata', id=id('button_modify_metadata'), className='btn btn-warning btn-lg', style={'width':'100%'}))] + out

    return name, out


# Add to Project Button
@app.callback(
    Output('url', 'pathname'),
    Input({'type':id('col_button_add_dataset'), 'index': ALL}, 'n_clicks'),
    State({'type':id('col_dataset_id'), 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def button_add_dataset(n_clicks_add_list, col_dataset_id_list):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    try:
        triggered = json.loads(triggered)
        index = triggered['index']
        if n_clicks_add_list[index] is not None:
            dataset_id = col_dataset_id_list[index]
            add_dataset(get_session('project_id'), dataset_id)
            return '/apps/data_lineage'
            

    except Exception as e:
        pass

    return no_update