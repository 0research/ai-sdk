import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State, ALL, MATCH
from app import app
import collections
import json
from pprint import pprint
from jsondiff import diff
from dash import no_update
from apps.util import *


# Layout
layout = html.Div([
    dcc.Store(id='input_data', storage_type='session'),
    html.H1('Temporal Data Evolution', style={"textAlign": "center"}),

    generate_upload(),

    html.Div([
        html.Div([
            html.Div(id='topDiv2', style={'text-align': 'center'}, children=[
                dbc.ButtonGroup(id='select_list'),
                html.Div(id='selected_list'),
                html.Button('Clear Selected', id={'type': 'select_button', 'index': -1}),
            ]),
            
            html.Div([
                html.H4('', id='selected_filename_1', style={'text-decoration': 'underline'}), 
                html.Pre(id='json_tree_select_1', style={'textAlign': 'left'}),
            ], style={'textAlign':'center', 'width': '50%', 'float': 'left'}),

            html.Div([
                html.H4('', id='selected_filename_2', style={'text-decoration': 'underline'}), 
                html.Pre(id='json_tree_select_2', style={'textAlign': 'left'}),
            ], style={'textAlign':'center', 'width': '50%', 'float': 'right'})

        ], id='leftDiv', style={'float': 'left', 'width': '40%', "textAlign": "left"}),

        html.Div([
            html.Div(id='topDiv3', style={'float': 'left', 'width': '33%'}, children=[
                dbc.ButtonGroup(id='select_list_2'),
                html.Div(id='selected_list_2'),
                html.Button('Clear Selected', id={'type': 'select_button_2', 'index': -1}),
                html.Pre(id='json_tree_difference_1'),
            ]),
            
            html.Div(id='topDiv4', style={'float': 'left', 'width': '33%'}, children=[
                dbc.ButtonGroup(id='select_list_3'),
                html.Div(id='selected_list_3'),
                html.Button('Clear Selected', id={'type': 'select_button_3', 'index': -1}),
                html.Pre(id='json_tree_difference_2'),
            ]),

            html.Div(id='topDiv5', style={'float': 'left', 'width': '33%'}, children=[
                dbc.ButtonGroup(id='select_list_4'),
                html.Div(id='selected_list_4'),
                html.Button('Clear Selected', id={'type': 'select_button_4', 'index': -1}),
                html.Pre(id='json_tree_difference_3'),
            ]),
        ], id='rightDiv', style={'float': 'right', 'width': '60%', "textAlign": "left"})
        
    ], id='contentDiv', style={'display':'block'}),
])


@app.callback([Output('json_tree_select_1', 'children'), Output('json_tree_select_2', 'children'), 
            Output('selected_filename_1', 'children'), Output('selected_filename_2', 'children')], 
            Input('selected_list', 'children'),
            State('input_data', 'data'))
def generate_selected_data(selected_list, input_data):
    selected_filenames = [s+'.json' for s in selected_list]
    json1, json2, filename1, filename2 = None, None, None, None

    if len(selected_list) >= 1:
        filename1 = selected_filenames[-1]
        json1 = input_data[filename1]
    if len(selected_list) >= 2:
        filename2 = selected_filenames[-2]
        json2 = input_data[filename2]

    return json.dumps(json1, indent=2), json.dumps(json2, indent=2), filename1, filename2


@app.callback(Output('select_list_2', 'children'), Input('input_data', 'data'))
def generate_select2(input_data):
    return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_2', 'index': name.split('.')[0]}) for name in sorted(input_data.keys())]


@app.callback(Output('select_list_3', 'children'), Input('input_data', 'data'))
def generate_select3(input_data):
    return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_3', 'index': name.split('.')[0]}) for name in sorted(input_data.keys())]


@app.callback(Output('select_list_4', 'children'), Input('input_data', 'data'))
def generate_selec4(input_data):
    return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_4', 'index': name.split('.')[0]}) for name in sorted(input_data.keys())]


@app.callback(Output('selected_list_2', 'children'), 
            Input({'type': 'select_button_2', 'index': ALL}, 'n_clicks'),
            State('selected_list_2', 'children'))
def generate_selected2(n_clicks, selected_list):
    if all(v is None for v in n_clicks): return no_update
    if selected_list is None: selected_list = []
    triggered_id = json.loads(callback_context.triggered[0]['prop_id'].split('.')[0])['index']

    # If clicked on Clear Selection
    if triggered_id == -1:
        selected_list = []
    # Return selected
    else:
        selected_list.append(triggered_id)

    return selected_list

@app.callback(Output('selected_list_3', 'children'), 
            Input({'type': 'select_button_3', 'index': ALL}, 'n_clicks'),
            State('selected_list_3', 'children'))
def generate_selected2(n_clicks, selected_list):
    if all(v is None for v in n_clicks): return no_update
    if selected_list is None: selected_list = []
    triggered_id = json.loads(callback_context.triggered[0]['prop_id'].split('.')[0])['index']

    # If clicked on Clear Selection
    if triggered_id == -1:
        selected_list = []
    # Return selected
    else:
        selected_list.append(triggered_id)

    return selected_list


@app.callback(Output('selected_list_4', 'children'), 
            Input({'type': 'select_button_4', 'index': ALL}, 'n_clicks'),
            State('selected_list_4', 'children'))
def generate_selected2(n_clicks, selected_list):
    if all(v is None for v in n_clicks): return no_update
    if selected_list is None: selected_list = []
    triggered_id = json.loads(callback_context.triggered[0]['prop_id'].split('.')[0])['index']

    # If clicked on Clear Selection
    if triggered_id == -1:
        selected_list = []
    # Return selected
    else:
        selected_list.append(triggered_id)

    return selected_list


@app.callback(Output('json_tree_difference_1', 'children'), 
            Input('selected_list_2', 'children'), 
            State('input_data', 'data'))
def generate_selected_lists(selected_list, input_data):
    if selected_list is None: return no_update
    if len(selected_list) < 2: return 'Select one more'

    selected_filenames = [s+'.json' for s in selected_list]
    json1, json2, filename1, filename2 = None, None, None, None

    if len(selected_list) >= 1:
        filename1 = selected_filenames[-1]
        json1 = input_data[filename1]
    if len(selected_list) >= 2:
        filename2 = selected_filenames[-2]
        json2 = input_data[filename2]
    difference = diff(json1, json2, syntax='symmetric')

    return json.dumps(difference, indent=2)


@app.callback(Output('json_tree_difference_2', 'children'), 
            Input('selected_list_3', 'children'), 
            State('input_data', 'data'))
def generate_selected_lists(selected_list, input_data):
    if selected_list is None: return no_update
    if len(selected_list) < 2: return 'Select one more'

    selected_filenames = [s+'.json' for s in selected_list]
    json1, json2, filename1, filename2 = None, None, None, None

    if len(selected_list) >= 1:
        filename1 = selected_filenames[-1]
        json1 = input_data[filename1]
    if len(selected_list) >= 2:
        filename2 = selected_filenames[-2]
        json2 = input_data[filename2]
    difference = diff(json1, json2, syntax='symmetric')

    return json.dumps(difference, indent=2)


@app.callback(Output('json_tree_difference_3', 'children'), 
            Input('selected_list_4', 'children'), 
            State('input_data', 'data'))
def generate_selected_lists(selected_list, input_data):
    if selected_list is None: return no_update
    if len(selected_list) < 2: return 'Select one more'

    selected_filenames = [s+'.json' for s in selected_list]
    json1, json2, filename1, filename2 = None, None, None, None

    if len(selected_list) >= 1:
        filename1 = selected_filenames[-1]
        json1 = input_data[filename1]
    if len(selected_list) >= 2:
        filename2 = selected_filenames[-2]
        json2 = input_data[filename2]
    difference = diff(json1, json2, syntax='symmetric')

    return json.dumps(difference, indent=2)