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
from dash_extensions import EventListener

id = id_factory('feature_engineering')
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True




# Layout
layout = html.Div([
    dbc.Container([
        # Top Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Select Function', style={'text-align':'center', 'margin':'1px'})),
                    dbc.CardBody([
                        dbc.InputGroup([
                            dbc.InputGroupText('Feature Name', style={'width':'100%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
                            dbc.Input(id=id('feature_name'), style={'height':'40px', 'min-width':'120px', 'text-align':'center'}, persistence=True),
                        ]),
                        dbc.InputGroup([
                            dbc.InputGroupText('Type of Function', style={'width':'100%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
                            dbc.Select(id=id('dropdown_function'), style={'height':'40px', 'min-width':'120px', 'text-align':'center'}, persistence=True),
                        ]),
                        dbc.InputGroup([
                            dbc.InputGroupText('Feature Selection', style={'width':'100%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
                            html.Div(dcc.Dropdown(id=id('selected_features'), multi=True, options=[], value=None, persistence=True), style={'width':'65%'}),
                            dbc.Button('Use Features', id=id('button_use_features'), color='info', style={'width':'35%'}),
                        ]),

                        dbc.CardFooter(dbc.Button('Add Feature', color='warning', id=id('button_add'), style={'width':'100%'})),
                    ]),
                ])
            ], width=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        EventListener(
                            id=id('el_datatable'),
                            events=[{"event": "click", "props": ["srcElement.className", "srcElement.innerText"]}],
                            logging=True,
                            children=generate_datatable(id('datatable'), col_selectable="multi", height='320px', metadata_id=id('metadata'), selected_column_id=id('selected_features')),
                        )
                    ])
                ])
            ], width=9),
        ], style={'height':'430px'}),

        # Bottom Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Graph Inputs', style={'text-align':'center', 'margin':'1px'})),
                    dbc.CardBody([html.Div(generate_graph_inputs(id), id=id('graph_inputs'))]),
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([dcc.Graph(id=id('graph'), style={'height': '400px'})]),
                ])
            ], width=9),

        ], className='text-center', style={'height':'430px'}),

        dbc.CardFooter(dbc.Button('Confirm', color='warning', id=id('button_confirm'), style={'width':'100%'})),
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

    Input('url', 'pathname'),
)
def generate_graph_inputs(pathname):
    return graph_inputs_callback()[:-4]


# Generate List of feature dropdown
@app.callback(
    Output(id('selected_features'), 'options'),
    Input(id('datatable'), 'columns'),
)
def generate_feature_dropdown(features):
    return [{'label': f['name'], 'value': f['name']} for f in features]

# Populate Features on click
@app.callback(
    Output(id('selected_features'), 'value'),
    Input(id('button_use_features'), 'n_clicks'),
    State(id('datatable'), "selected_columns"),
)
def generate_feature_dropdown(n_clicks, selected_columns):
    if n_clicks is None: return no_update
    return selected_columns


# Generate datatable
@app.callback(
    Output(id('datatable'), 'data'),
    Output(id('datatable'), 'columns'),
    Output(id('datatable'), "style_data_conditional"),
    Output(id('datatable'), "selected_columns"),
    Input('url', 'pathname'),
    Input(id('button_add'), 'n_clicks'),
    Input(id('datatable'), "active_cell"),
    State(id('datatable'), "style_data_conditional"),
    State(id('datatable'), "selected_columns"),
    State(id('datatable'), 'columns'),
    State(id('datatable'), 'data'),
    State(id('feature_name'), 'value')
)
def generate_datatable(_, n_clicks, active, current_style, selected_columns, columns, data, feature_name):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    node_id = get_session('node_id')

    # Load Page
    if triggered == '':
        df = get_dataset_data(node_id)
        columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]
        data = df.to_dict('records')

    # Click Cell
    elif triggered == id('datatable'):
        current_style = no_update
        if active:
            # Add to selected Columns
            if active['column_id'] not in selected_columns:
                # current_style.append(
                #     {
                #         'if': {'column_id': active['column_id']},
                #         "backgroundColor": "rgba(150, 180, 225, 0.2)",
                #         "border": "1px solid blue",
                #     },
                # )
                selected_columns.append(active["column_id"])
                
            # Remove from selected columns
            else:
                # for i in range(len(current_style)):
                #     if current_style[i]['if'] == {'column_id': active['column_id']}:
                #         del current_style[i]
                #         break
                
                selected_columns.remove(active["column_id"])

    # Click Add Column
    elif triggered == id('button_add'):
        if feature_name in [c['name'] for c in columns]:
            print("Feature name already exist")
        else:
            # Append Datatable
            columns.append({"name": feature_name, "id": feature_name, "deletable": False, "selectable": True, "deletable": True})
            df = pd.DataFrame(data)
            df[feature_name] = "new data" # TODO change to function
            data = df.to_dict('records')
            # Change font color of new features
            node = get_document('node', node_id)
            for c in columns:
                if c['name'] not in node['features'].keys():
                    current_style.append(
                            {
                                "if": {"column_id": c['id']},
                                "color": "yellow",
                            },
                        )
            # On selecting cell highlight entire columns
            # current_style.append(
            #     {
            #         "if": {"column_id": active["column_id"]},
            #         "backgroundColor": "rgba(150, 180, 225, 0.2)",
            #         "border": "1px solid blue",
            #     },
            # )

    return data, columns, current_style, selected_columns




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


# dash_extensions Event Listener for datatable (if needed)
# @app.callback(
#     Output("modal", "children"),
#     Input(id('el_datatable'), "event"),
#     Input(id('el_datatable'), "n_events"),
# )
# def click_event(event, n_events):
#     print(n_events, event)
#     return no_update
#     # Check if the click is on the active cell.
#     if not event or "cell--selected" not in event["srcElement.className"]:
#         return no_update
#     # Return the content of the cell.
#     return f"Cell content is {event['srcElement.innerText']}, number of clicks in {n_events}"






@app.callback(
    Output(id('metadata'), 'children'),
    Input('url', 'pathname')
)
def update_metadata(pathname):
    dataset_id = get_session('node_id')
    dataset = get_document('node', dataset_id)
    return display_metadata(dataset, id, disabled=True, height='300px')


# Generate Functions
@app.callback(
    Output(id('dropdown_function'), "options"),
    Output(id('dropdown_function'), "value"),
    Input(id('datatable'), "selected_columns"),
)
def generate_functions(selected_columns):
    options = [
        {'label': 'Mathematical', 'value':'mathematical'},
        {'label': 'Conditional', 'value':'conditional'},
        {'label': 'Cumulative', 'value':'cumulative'},
        {'label': 'Aggregate', 'value':'aggregate'},
    ]

    options_number_functions = [
        {'label': 'Average', 'value':'avg'},
        {'label': 'Sum', 'value':'sum'},
        {'label': 'Maximum', 'value':'max'},
        {'label': 'Minimum', 'value':'min'},
        {'label': 'Count', 'value':'count'},
        {'label': 'Distinct', 'value':'distinct'},
        {'label': 'Custom', 'value':'normalize'},
        {'label': 'Normalize', 'value':'normalize', 'disabled':True},
        {'label': 'Low-pass Filter', 'value':'lpf', 'disabled':True},
        {'label': 'High-pass Filter', 'value':'hpf', 'disabled':True},
        {'label': 'Binning', 'value':'binning', 'disabled':True},
        {'label': 'Encode', 'value':'encode', 'disabled':True},
        {'label': 'Fourier Transform', 'value':'fourier_transform', 'disabled':True},
    ]
    options_string_functions = [
        {'label': 'Split by Character', 'value':'split'},
    ]
    options_datetime_functions = [
        {'label': 'None', 'value':'none'},
    ]

    dataset_id = get_session('node_id')
    dataset = get_document('node', dataset_id)
    if len(selected_columns) == 1:
        print(selected_columns[0], dataset['features'][selected_columns[0]])
    elif len(selected_columns) > 1:
        pass

    print(selected_columns)
    return options, options[0]['value']


# # Select Column 
# @app.callback(Output(id('datatable'), "data"),
#                 Output(id('datatable'), 'columns'),
#                 Output(id('dropdown_selected_columns'), "options"), 
#                 Input('url', 'pathname'))
# def generate_datatable(pathname):
#     return no_update


# # Datatable
@app.callback(Output(id('datatable2'), "data"),
                Output(id('datatable2'), 'columns'),
                Output(id('datatable3'), "data"),
                Output(id('datatable3'), 'columns'),
                Input(id('datatable'), "selected_columns"),
                Input(id('dropdown_function'), "value"))
def generate_datatable(selected_columns, func):
    print(selected_columns, func)
    dataset_id = get_session('node_id')
    df = get_dataset_data(dataset_id)
    columns = [{"name": i, "id": i, "deletable": False, "selectable": False} for i in df.columns]
    options = [{'label':c, 'value':c} for c in df.columns]

    return df.to_dict('records'), columns, df.to_dict('records'), columns