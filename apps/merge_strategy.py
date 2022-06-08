from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
from dash import dash_table
from dash import no_update, callback_context
import json
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


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('merge_strategy')

mergeOptions = ['overwrite', 'objectMerge', 'version']
flattenOptions = ['Flatten', 'Unflatten']

# Layout
layout = html.Div([
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    dcc.Store(id='dataset_metadata', storage_type='session'),
    dcc.Store(id=id('slider_store'), storage_type='session'),
    dcc.Store(id=id('selection_list_store'), storage_type='session'),
    dcc.Store(id=id('merge_strategy_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),

    dbc.Container([
        # Page Title
        # dbc.Row(dbc.Col(html.H2('Merge Strategy'))),

        # Datatable & Selected Rows/Json List
        dbc.Row([
            dbc.Col(html.H5('Step 1: Select Rows to Merge'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),
            dbc.Col(html.Div(generate_range_slider(id('slider')), style={'display':'hidden'}), width=12),
            dbc.Col(html.H5('Selection: None', id=id('selection_list')), width=12),
            dbc.Col(html.Button('Clear Selection', className='btn-secondary', id=id('button_clear')), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

        # Options
        dbc.Row([
            dbc.Col(html.H5('Step 2: Select Merge Options'), width=12),
            dbc.Col(html.Div(generate_radio(id('merge_radio'), mergeOptions, "Select One Merge Strategy")), width=4),
            dbc.Col(html.Div(generate_radio(id('flatten_radio'), flattenOptions, "Select Json Display type")), width=4),
            dbc.Col(html.Div('Other options?'), width=4),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

        # Json Data Headers
        dbc.Row([
            dbc.Col(html.H5('Step 3: Select the First or Second Panel to Display Merged Selection'), width=12),

            dbc.Col(html.Button('Display Merge History', className='btn-success btn-block', style={'font-size':'20px'}, id=id('button_json_1')), width=4),
            dbc.Col(html.Button('Display Merge History', className='btn-info btn-block', style={'font-size':'20px'}, id=id('button_json_2')), width=4),
            dbc.Col(html.Button('Observe Difference', className='btn-danger btn-block', style={'font-size':'20px'}, disabled=True), width=4),

            dbc.Col(html.Div(id=id('selected_list_1')), width=4),
            dbc.Col(html.Div(id=id('selected_list_2')), width=4),
            dbc.Col(html.Div(id=id('selected_list_3')), width=4),

            dbc.Col(html.Pre(id=id('json_1'), className='bg-success text-white'), style={'text-align': 'left'}, width=4),
            dbc.Col(html.Pre(id=id('json_2'), className='bg-info text-white', style={'text-align': 'left'}), width=4),
            dbc.Col(html.Pre(id=id('json_3'), className='bg-danger text-white', style={'text-align': 'left'}), width=4),
        ], className='text-center bg-light', style={'overflow-y':'auto', 'height':'700px'}),

        dbc.Row([
            dbc.Col(dbc.Button(html.H6('Confirm'), className='btn-primary', id=id('button_confirm'), href='/apps/data_flow', style={'width':'100%'}), width={'size':10, 'offset':1}),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        
    ], style={'width':'100%', 'maxWidth':'100%'}),
    
])

# Update Datatable in "Review Data" Tab
@app.callback(Output(id('input_datatable'), "data"), 
                Output(id('input_datatable'), 'columns'), 
                Input('current_node', "data"))
def update_data_table(node_id):
    if node_id is None: return no_update
    
    df = get_dataset_data(node_id)
    df.insert(0, column='index', value=range(1, len(df)+1))
    json_dict = df.to_dict('records')

    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    return json_dict, columns


# Generate Slider data
@app.callback([Output(id('slider'), 'marks'), 
                Output(id('slider'), 'min'), 
                Output(id('slider'), 'max'), 
                Output(id('slider'), 'value')],
                Input(id('input_datatable'), 'data'))
def generate_range_slider_values(data):
    if data is None: return no_update

    # TODO Get Index field and sort
    # for json in data:
    #     date = json['created']
    #     if date[-1] == 'Z':
    #         date = date[:-1]
    #     if len(date.rsplit('.', 1)[1]) != 6:
    #         date = date.rsplit('.', 1)[0] + '.000000'            
    #     created = datetime.fromisoformat(date)
    
    # data.sort(key=lambda item:item['created'], reverse=False)

    marks = {}
    for i, json in enumerate(data):
        marks[i] = str(i+1)

    start = 0
    end = len(data) - 1

    return marks, start, end, [start, start]

@app.callback(Output(id('slider_store'), 'data'), Input(id('slider'), 'value'))
def save_slider(selected_range):
    return selected_range


# Store/Clear selected rows
@app.callback([Output(id('selection_list_store'), "data"), 
                Output(id('input_datatable'), "selected_rows")],
                [Input(id('input_datatable'), "selected_rows"), 
                Input(id('button_clear'), 'n_clicks'), 
                Input(id('slider'), 'value')])
def save_table_data(selected_rows, n_clicks, slider_value):
    triggered = callback_context.triggered[0]['prop_id']

    if triggered == id('input_datatable.selected_rows'):
        pass
    elif triggered == id('button_clear.n_clicks'):
        selected_rows = []
    elif triggered == id('slider.value'):
        selected_rows = [*range(slider_value[0], slider_value[1]+1)]

    return selected_rows, selected_rows


# Display selected rows/json
@app.callback(Output(id('selection_list'), "children"), Input(id('selection_list_store'), 'data'))
def generate_selected_list(selection_list):
    selection_list = list(map(lambda x:x+1, selection_list))
    return 'Selection: ', str(selection_list)[1:-1]



# Saves last selected merge strategy
@app.callback(Output(id('merge_strategy_store'), 'data'), Input(id('merge_radio'), 'value'))
def save_merge_strategy(merge_strategy):
    return merge_strategy


# Update First two Merge History Jsons
for x in range(1, 3):
    @app.callback(Output(id('selected_list_'+str(x)), 'children'), 
                    [Input(id('button_json_')+str(x), 'n_clicks'), 
                    State(id('selection_list_store'), 'data'), 
                    State(id('merge_strategy_store'), 'data')])
    def display_selected(n_clicks, selection_list, merge_strategy):
        if selection_list is None: return no_update
        selection_list = list(map(lambda x:x+1, selection_list))
        return (html.P('You have Selected: ' + str(selection_list)[1:-1]), html.P('Merge Strategy: ' + merge_strategy))

    @app.callback(Output(id('json_store_')+str(x), 'data'), 
                    Input(id('button_json_')+str(x), 'n_clicks'),
                    State(id('selection_list_store'), 'data'), 
                    State(id('merge_strategy_store'), 'data'),
                    State(id('input_datatable'), 'data'))
    def save_json(n_clicks, selected_list, merge_strategy, data):
        if selected_list is None or len(selected_list) == 0: return []
        triggered = callback_context.triggered[0]['prop_id']
        if triggered == '.': return [], []

        selected_list = list(map(lambda x:x+1, selected_list))
        base, base_history = None, []

        df = json_normalize(data)
        
        for index in selected_list:
            new = json.loads(df.set_index('index').loc[index].to_json())
            base = json_merge(base, new, merge_strategy)
            base_history.append(base)

        return base_history

    @app.callback(Output(id('json_')+str(x), 'children'), Input(id('json_store_')+str(x), 'data'))
    def generate_json(json_tree):
        return json.dumps(json_tree, indent=2)


# Generate Difference Json
@app.callback([Output(id('json_3'), 'children'), Output(id('selected_list_3'), 'children')], 
            [Input(id('json_store_1'), 'data'), Input(id('json_store_2'), 'data')])
def generate_json(json_history_1, json_history_2):
    # Difference_history 
    difference_history = generate_difference_history(json_history_1, json_history_2)

    # Number of changes
    num_changes = generate_number_changes(difference_history)

    return (json.dumps(difference_history, indent=2),
            ([html.P('Number of Changes per key', style={'textAlign':'left'}), 
            html.Pre(json.dumps(num_changes, indent=2)[1:-1], style={'textAlign':'left'}), html.Br()]))




# @app.callback(Output('modal', 'children'),
#                 Input(id('button_confirm'), 'n_clicks'),
#                 State('current_dataset', 'data'),
#                 State('current_node', 'data'),
#                 State(id('json_store_1'), 'data'))
# def button_confirm(n_clicks, dataset_id, node_id, data):
#     if n_clicks is None: return no_update

#     df = get_dataset_data(node_id)
#     df[selected_column] = impute_col(df[selected_column], action)

#     action(dataset_id, node_id, df.to_dict('records'), label='')

#     return no_update