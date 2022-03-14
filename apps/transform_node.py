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

function_options = [
    {'label': 'Arithmetic', 'value':'arithmetic'},
    {'label': 'Comparison', 'value':'comparison'},
    {'label': 'Aggregate', 'value':'aggregate'},
    {'label': 'Sliding Window', 'value':'slidingwindow'},
    {'label': 'Format Date', 'value':'formatdate'},
    {'label': 'Cumulative', 'value':'cumulative'},
    {'label': 'Shift', 'value':'shift'},
]

arithmetic_options = [
    {'label': '[+] Add', 'value':'add'},
    {'label': '[-] Subtract', 'value':'subtract'},
    {'label': '[/] Divide', 'value':'divide'},
    {'label': '[*] Multiply', 'value':'multiply'},
    {'label': '[**] Exponent', 'value':'exponent'},
    {'label': '[%] Modulus', 'value':'modulus'},
]

comparison_options = [
    {'label': '[>] Greater than', 'value':'gt'},
    {'label': '[<] Less than', 'value':'lt'},
    {'label': '[>=] Greater than or Equal to', 'value':'ge'},
    {'label': '[<=] Less than or Equal to', 'value':'le'},
    {'label': '[==] Equal to', 'value':'eq'},
    {'label': '[!=] Not equal to', 'value':'ne'},
]

aggregate_options = [
    {'label': 'Sum', 'value':'sum'},
    {'label': 'Average', 'value':'avg'},
    {'label': 'Minimum', 'value':'min'},
    {'label': 'Maximum', 'value':'max'},
]

slidingwindow_options = [
    {'label': 'Sum', 'value':'sum'},
    {'label': 'Average', 'value':'avg'},
    {'label': 'Minimum', 'value':'min'},
    {'label': 'Maximum', 'value':'max'},
]

dateformat_options = [
    {'label': 'DD-MM-YYYY', 'value':'YYYY-MM-DD'},
    {'label': 'MM-DD-YYYY', 'value':'YYYY-MM-DD'},
    {'label': 'YYYY-MM-DD', 'value':'YYYY-MM-DD'},
    {'label': 'TODO', 'value':'TODO'},
]


# Layout
layout = html.Div([
    dbc.Container([
        dcc.Store(id=id('new_feature'), storage_type='session'),

        # Top Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Select Function', style={'text-align':'center', 'margin':'1px'})),
                    dbc.CardBody([
                        dbc.InputGroup([
                            dbc.InputGroupText('Feature Name', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
                            dbc.Input(id=id('feature_name'), style={'height':'40px', 'text-align':'center'}, persistence=True),
                        ]),

                        dbc.InputGroup([
                            dbc.InputGroupText('Function Type', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
                            dbc.Select(id=id('dropdown_function_type'), options=function_options, value=function_options[0]['value'], style={'height':'40px', 'text-align':'center'}, persistence=True),
                        ]),
                        
                        # Arithmetic Functions
                        dbc.InputGroup([
                            dbc.InputGroupText('Feature', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Operator', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Feature', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.Select(id=id('dropdown_arithmeticfeature1'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                            dbc.Select(id=id('dropdown_arithmeticfunction'), options=arithmetic_options, value=arithmetic_options[0]['value'], style={'height':'40px', 'text-align':'center'}, persistence=True),
                            dbc.Select(id=id('dropdown_arithmeticfeature2'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                        ], id=id('arithmetic_inputs'), style={'display': 'none'}),

                        # Comparison Functions
                        dbc.InputGroup([
                            dbc.InputGroupText('Feature', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Operator', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Feature', style={'width':'33.3%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.Select(id=id('dropdown_comparisonfeature1'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                            dbc.Select(id=id('dropdown_comparisonfunction'), options=comparison_options, value=comparison_options[0]['value'], style={'height':'40px', 'text-align':'center'}, persistence=True),
                            dbc.Select(id=id('dropdown_comparisonfeature2'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                        ], id=id('comparison_inputs'), style={'display': 'none'}),

                        # Custom Input
                        dbc.Input(id=id('custom_input'), style={'display':'none', 'height':'40px', 'text-align':'center', 'width':'33.3%', 'float':'right'}, persistence=True),

                        # Aggregate Functions
                        dbc.InputGroup([
                            dbc.InputGroupText('Function', style={'width':'20%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Features', style={'width':'80%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.Select(id=id('dropdown_aggregate_function'), options=aggregate_options, value=aggregate_options[0]['value'], style={'text-align':'center', 'width':'20%'}, persistence=True),
                            html.Div(dcc.Dropdown(id=id('dropdown_aggregatefeatures'), multi=True, options=[], value=None, persistence=True), style={'width':'50%'}),
                            dbc.Button('Use Features', id=id('button_aggregate_use_features'), color='info', style={'width':'30%'}),
                        ], id=id('aggregate_inputs'), style={'display': 'none'}),

                        # Sliding Window Functions
                        dbc.InputGroup([
                            dbc.InputGroupText('Function', style={'width':'25%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Window Size', style={'width':'25%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Feature', style={'width':'50%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.Select(id=id('dropdown_slidingwindow_function'), options=aggregate_options, value=aggregate_options[0]['value'], style={'text-align':'center', 'width':'25%'}, persistence=True),
                            dbc.Select(id=id('dropdown_slidingwindow_size'), options=[], value=None, style={'text-align':'center', 'width':'25%'}, persistence=True),
                            dbc.Select(id=id('dropdown_slidingwindow_feature'), options=[], value=None, style={'width':'50%', 'text-align':'center'}, persistence=True),
                        ], id=id('slidingwindow_inputs'), style={'display': 'none'}),

                        # Format Date Functions
                        dbc.InputGroup([
                            dbc.InputGroupText('Feature', style={'width':'50%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Format', style={'width':'50%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.Select(id=id('dropdown_dateformat'), options=dateformat_options, value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                            dbc.Select(id=id('dropdown_formatdatefeature'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                        ], id=id('formatdate_inputs'), style={'display': 'none'}),

                        # Cumulative Function
                        dbc.InputGroup([
                            dbc.InputGroupText('Feature', style={'width':'100%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.Select(id=id('dropdown_cumulativefeature'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                        ], id=id('cumulative_inputs'), style={'display': 'none'}),

                        # Shift Function
                        dbc.InputGroup([
                            dbc.InputGroupText('Size', style={'width':'20%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.InputGroupText('Feature', style={'width':'80%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px', 'text-align':'center'}),
                            dbc.Select(id=id('dropdown_shift_size'), options=[], value=None, style={'text-align':'center', 'width':'20%'}, persistence=True),
                            dbc.Select(id=id('dropdown_shift_feature'), options=[], value=None, persistence=True, style={'width':'80%'}),
                        ], id=id('shift_inputs'), style={'display': 'none'}),

                        # Conditions
                        dbc.InputGroup([
                            dbc.InputGroup([
                                dbc.InputGroupText("Conditions", style={'width':'80%', 'font-weight':'bold', 'font-size': '13px', 'text-align':'center'}),
                                dbc.Button(' - ', id=id('button_add_condition'), color='dark', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
                                dbc.Button(' + ', id=id('button_remove_condition'), color='dark', outline=True, style={'font-size':'15px', 'font-weight':'bold', 'width':'10%', 'height':'28px'}),
                                # dbc.Select(id=id('dropdown_conditionfeature1'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                                # dbc.Select(id=id('dropdown_conditionfunction'), options=comparison_options, value=comparison_options[0]['value'], style={'height':'40px', 'text-align':'center'}, persistence=True),
                                # dbc.Select(id=id('dropdown_conditionfeature2'), options=[], value=None, style={'height':'40px', 'text-align':'center'}, persistence=True),
                            ]),
                        ], id=id('conditions'), style={'display': 'none'}),

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
    store_session('graph_id', '')
    return graph_inputs_callback()[:-4]


# Generate List of feature dropdown
@app.callback(
    Output(id('dropdown_aggregatefeatures'), 'options'),
    Output(id('dropdown_arithmeticfeature1'), 'options'),
    Output(id('dropdown_arithmeticfeature2'), 'options'),
    Output(id('dropdown_comparisonfeature1'), 'options'),
    Output(id('dropdown_comparisonfeature2'), 'options'),
    Output(id('dropdown_formatdatefeature'), 'options'),
    Output(id('dropdown_cumulativefeature'), 'options'),
    Output(id('dropdown_slidingwindow_feature'), 'options'),
    Output(id('dropdown_slidingwindow_size'), 'options'),
    Output(id('dropdown_shift_size'), 'options'),
    Output(id('dropdown_shift_feature'), 'options'),
    Input(id('datatable'), 'columns'),
    State(id('datatable'), 'data')
)
def generate_feature_dropdown(features, data):
    options = [{'label': f['name'], 'value': f['name']} for f in features]
    options_slidingwindow_size = [{'label': i, 'value': i} for i in range(2, len(data)-1)]
    options_shift_size = [{'label': i, 'value': i} for i in range(2, len(data)-1)]
    options_custom = options + [{'label': 'Custom Input', 'value': '_custom'}]
    return options, options, options_custom, options, options_custom, options, options, options, options_slidingwindow_size, options_shift_size, options

# Display Custom Inputs
@app.callback(
    Output(id('custom_input'), 'style'),
    Input(id('dropdown_arithmeticfeature2'), 'value'),
    Input(id('dropdown_comparisonfeature2'), 'value'),
    Input(id('dropdown_function_type'), 'value'),
    State(id('custom_input'), 'style'),
)
def display_custom_inputs(arithmetic_feature, comparison_feature, function_type, style):
    style['display'] = 'none'
    if arithmetic_feature == '_custom' and function_type == 'arithmetic': style['display'] = 'flex'
    if comparison_feature == '_custom' and function_type == 'comparison': style['display'] = 'flex'
    return style



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
def display_graph_inputs(style1, style2, style3, style4, 
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


# Populate Features on click
@app.callback(
    Output(id('dropdown_aggregatefeatures'), 'value'),
    Input(id('button_aggregate_use_features'), 'n_clicks'),
    State(id('datatable'), "selected_columns"),
)
def generate_feature_dropdown(n_clicks, selected_columns):
    if n_clicks is None: return no_update
    return selected_columns


# Add Feature (Arithmetic)
@app.callback(
    Output(id('new_feature'), 'data'),
    Input(id('button_add'), 'n_clicks'),
    State(id('dropdown_function_type'), 'value'),
    State(id('datatable'), 'data'),
    State(id('dropdown_arithmeticfunction'), 'value'),
    State(id('dropdown_arithmeticfeature1'), 'value'),
    State(id('dropdown_arithmeticfeature2'), 'value'),
)
def add_feature1(n_clicks, function_type, data, function, feature1, feature2):
    if n_clicks is None: return no_update
    if function_type != 'arithmetic': return no_update
    df = pd.DataFrame(data)
    try:
        if function == 'add': feature = df[feature1] + df[feature2]
        elif function == 'subtract': feature = df[feature1] - df[feature2]
        elif function == 'divide': feature = df[feature1] / df[feature2]
        elif function == 'multiply': feature = df[feature1] * df[feature2]
        elif function == 'exponent': feature = df[feature1] ** df[feature2]
        elif function == 'modulus': feature = df[feature1] % df[feature2]
    except:
        feature = 'error'
    return feature

# Add Feature (Comparison)
@app.callback(
    Output(id('new_feature'), 'data'),
    Input(id('button_add'), 'n_clicks'),
    State(id('dropdown_function_type'), 'value'),
    State(id('datatable'), 'data'),
    State(id('dropdown_comparisonfunction'), 'value'),
    State(id('dropdown_comparisonfeature1'), 'value'),
    State(id('dropdown_comparisonfeature2'), 'value'),
)
def add_feature2(n_clicks, function_type, data, function, feature1, feature2):
    if n_clicks is None: return no_update
    if function_type != 'comparison': return no_update
    df = pd.DataFrame(data)
    try:
        if function == 'gt': feature = df[feature1].gt(df[feature2])
        elif function == 'lt': feature = df[feature1].lt(df[feature2])
        elif function == 'ge': feature = df[feature1].ge(df[feature2])
        elif function == 'le': feature = df[feature1].le(df[feature2])
        elif function == 'eq': feature = df[feature1].eq(df[feature2])
        elif function == 'ne': feature = df[feature1].ne(df[feature2])
    except: 
        feature = 'error'
    return feature

# Add Feature (aggregate)
@app.callback(
    Output(id('new_feature'), 'data'),
    Input(id('button_add'), 'n_clicks'),
    State(id('dropdown_function_type'), 'value'),
    State(id('dropdown_aggregate_function'), 'value'),
    State(id('datatable'), 'data'),
    State(id('dropdown_aggregatefeatures'), 'value'),
)
def add_feature3(n_clicks, function_type, func, data, features):
    if n_clicks is None: return no_update
    if function_type != 'aggregate': return no_update
    df = pd.DataFrame(data)
    try:
        if func == 'sum': feature = df[features].sum(axis=1)
        elif func == 'avg': feature = df[features].mean(axis=1)
        elif func == 'min': feature = df[features].min(axis=1)
        elif func == 'max': feature = df[features].max(axis=1)
    except:
        feature = 'error'
    return feature

# Add Feature (Sliding Window)
@app.callback(
    Output(id('new_feature'), 'data'),
    Input(id('button_add'), 'n_clicks'),
    State(id('dropdown_function_type'), 'value'),
    State(id('datatable'), 'data'),
    State(id('dropdown_slidingwindow_function'), 'value'),
    State(id('dropdown_slidingwindow_size'), 'value'),
    State(id('dropdown_slidingwindow_feature'), 'value'),
)
def add_feature4(n_clicks, function_type, data, func, window_size, feature):
    if n_clicks is None: return no_update
    if function_type != 'slidingwindow': return no_update
    df = pd.DataFrame(data)
    try:
        window = df[feature].rolling(int(window_size))
        if func == 'sum': feature = window.sum()
        elif func == 'avg': feature = window.mean()
        elif func == 'min': feature = window.min()
        elif func == 'max': feature = window.max()
    except:
        feature = 'error'

    return feature

# Add Feature (Format Date)
@app.callback(
    Output(id('new_feature'), 'data'),
    Input(id('button_add'), 'n_clicks'),
    State(id('dropdown_function_type'), 'value'),
    State(id('datatable'), 'data'),
    State(id('dropdown_dateformat'), 'value'),
    State(id('dropdown_formatdatefeature'), 'value'),
)
def add_feature5(n_clicks, function_type, data, date_format, feature):
    if n_clicks is None: return no_update
    if function_type != 'formatdate': return no_update
    df = pd.DataFrame(data)

    try:
        pass
    except:
        pass

    return feature

# Add Feature (Cumulative)
@app.callback(
    Output(id('new_feature'), 'data'),
    Input(id('button_add'), 'n_clicks'),
    State(id('dropdown_function_type'), 'value'),
    State(id('datatable'), 'data'),
    State(id('dropdown_cumulativefeature'), 'value'),
)
def add_feature5(n_clicks, function_type, data, feature):
    if n_clicks is None: return no_update
    if function_type != 'cumulative': return no_update
    df = pd.DataFrame(data)
    feature = df[feature].cumsum()

    return feature

# Add Feature (Shift)
@app.callback(
    Output(id('new_feature'), 'data'),
    Input(id('button_add'), 'n_clicks'),
    State(id('dropdown_function_type'), 'value'),
    State(id('datatable'), 'data'),
    State(id('dropdown_shift_size'), 'value'),
    State(id('dropdown_shift_feature'), 'value'),
)
def add_feature7(n_clicks, function_type, data, size, features):
    if n_clicks is None: return no_update
    if function_type != 'shift': return no_update
    df = pd.DataFrame(data)
    feature = df[features].shift(int(size))

    return feature.squeeze()



# Generate datatable
@app.callback(
    Output(id('datatable'), 'data'),
    Output(id('datatable'), 'columns'),
    Output(id('datatable'), "style_data_conditional"),
    Output(id('datatable'), "selected_columns"),
    Input('url', 'pathname'),
    Input(id('new_feature'), 'data'),
    Input(id('datatable'), "active_cell"),
    State(id('datatable'), "style_data_conditional"),
    State(id('datatable'), "selected_columns"),
    State(id('datatable'), 'columns'),
    State(id('datatable'), 'data'),
    State(id('feature_name'), 'value'),
)
def generate_datatable(_, new_feature, active, current_style, selected_columns, columns, data, feature_name):
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
                selected_columns.append(active["column_id"])
            # Remove from selected columns
            else:
                selected_columns.remove(active["column_id"])

    # Click Add Column
    elif triggered == id('new_feature'):
        if feature_name in [c['name'] for c in columns]:
            print("Feature name already exist")
        else:
            # Append Datatable
            columns.append({"name": feature_name, "id": feature_name, "deletable": False, "selectable": True, "deletable": True})
            df = pd.DataFrame(data)
            df[feature_name] = new_feature
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




# # Datatable
@app.callback(
    Output(id('datatable2'), "data"),
    Output(id('datatable2'), 'columns'),
    Output(id('datatable3'), "data"),
    Output(id('datatable3'), 'columns'),
    Input(id('datatable'), "selected_columns"),
    Input(id('dropdown_function_type'), "value")
)
def generate_datatable(selected_columns, func):
    print(selected_columns, func)
    dataset_id = get_session('node_id')
    df = get_dataset_data(dataset_id)
    columns = [{"name": i, "id": i, "deletable": False, "selectable": False} for i in df.columns]

    return df.to_dict('records'), columns, df.to_dict('records'), columns


# Function Input Visibility
@app.callback(
    Output(id('arithmetic_inputs'), "style"),
    Output(id('comparison_inputs'), "style"),
    Output(id('aggregate_inputs'), "style"),
    Output(id('slidingwindow_inputs'), "style"),
    Output(id('formatdate_inputs'), "style"),
    Output(id('cumulative_inputs'), "style"),
    Output(id('shift_inputs'), "style"),
    Output(id('conditions'), "style"),
    Input(id('dropdown_function_type'), "value"),
    State(id('arithmetic_inputs'), "style"),
    State(id('comparison_inputs'), "style"),
    State(id('aggregate_inputs'), "style"),
    State(id('slidingwindow_inputs'), "style"),
    State(id('formatdate_inputs'), "style"),
    State(id('cumulative_inputs'), "style"),
    State(id('shift_inputs'), "style"),
    State(id('conditions'), "style"),
)
def function_input_style(function_type, style1, style2, style3, style4, style5, style6, style7, conditions_style):
    style1['display'], style2['display'], style3['display'], style4['display'], style5['display'], style6['display'], style7['display'] = 'none', 'none', 'none', 'none', 'none', 'none', 'none'
    conditions_style['display'] = 'none'
    if function_type == 'arithmetic': style1['display'] = 'flex'
    elif function_type == 'comparison': style2['display'] = 'flex'
    elif function_type == 'aggregate': style3['display'] = 'flex'
    elif function_type == 'slidingwindow': style4['display'] = 'flex'
    elif function_type == 'formatdate': style5['display'] = 'flex'
    elif function_type == 'cumulative': style6['display'] = 'flex'
    elif function_type == 'shift': style7['display'] = 'flex'

    if function_type in ['arithmetic', 'comparison']:
        conditions_style['display'] = 'flex'
        
    return style1, style2, style3, style4, style5, style6, style7, conditions_style



# Confirm Action
@app.callback(
    Output('url', 'pathname'),
    Input(id('button_confirm'), "n_clicks"),
    State(id('datatable'), 'data'),
)
def button_confirm(n_clicks, data):
    if n_clicks is None: return no_update
    df = pd.DataFrame(data)
    node_id = get_session('node_id')
    node = get_document('node', node_id)
    action(get_session('project_id'), node_id, 'Transform Node', node, df_dataset_data=df, details=None)
    
    return '/apps/data_lineage'
