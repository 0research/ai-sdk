import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
import dash_table
from dash import no_update, callback_context
import json
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from itertools import zip_longest
from datetime import datetime


def generate_slider(component_id):
    return dcc.RangeSlider(
        id=component_id,
        min=None,
        max=None,
        step=None,
        value=[0, 11]
    ),

tab_labels = ['Overwrite', 'objectMerge', 'version']
tab_values = ['tab-' + str(i) for i in range(1, len(tab_labels) + 1)]


# Layout
layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id='selected_tab_store_merge', storage_type='session'),
    dcc.Store(id='json_tree_store_temporal_merge_1', storage_type='session'),
    dcc.Store(id='json_tree_store_temporal_merge_2', storage_type='session'),
    
    html.H1('Temporal Merge', style={"textAlign": "center"}),
    generate_upload('upload_json', "Step 1: Drag and Drop or Click Here to Select Files"),
    html.Div(children=[
        html.H4('Step 2: Select Merge Strategy', style={'text-align':'center'}),
        generate_tabs('tabs-1', tab_labels, tab_values),
    ], style={'background-color':'#F5F5DC', 'padding':'5px 25px 25px 5px'}),

    html.Div(children=[
        html.Div([
            html.Div([
                html.H4('Step 3: Select Merge Date Range I', style={'textAlign':'center'}),
                html.Div(generate_slider('select_slider_temporal_merge_1')),
                html.Div(id='selected_range_1'),
            ], style={'float':'left', 'width':'32.8%', 'margin':'2px', 'background-color':'#FFEBCD'}),

            html.Div([
                html.H4('Step 4: Select Merge Date Range II', style={'textAlign':'center'}),
                html.Div(generate_slider('select_slider_temporal_merge_2')),
                html.Div(id='selected_range_2'),
            ], style={'float':'left', 'width':'32.8%', 'margin':'2px', 'background-color':'#FFEBCD'}),

            html.Div([
                html.H4('Step 5: Observe Difference', style={'textAlign':'center'}),
                html.Div(id='num_changes'),
            ], style={'float':'left', 'width':'32.8%', 'background-color':'#DEB887'}),
        ], style={'width':'100%', 'display':'block', 'overflow': 'hidden', 'margin':'2px', 'display':'flex'}),
        
        html.Div([
            html.Div(children=[
                html.Pre(id='json_tree_temporal_merge_1', style={'textAlign': 'left'}),
            ], style={'float':'left', 'width':'32.8%', 'margin':'2px', 'background-color':'#FFEBCD'}),

            html.Div(children=[
                html.Pre(id='json_tree_temporal_merge_2', style={'textAlign': 'left'}),
            ], style={'float':'left', 'width':'32.8%', 'margin':'2px', 'background-color':'#FFEBCD'}),

            html.Div(children=[
                html.Pre(id='json_tree_temporal_merge_3', style={'textAlign': 'left'}),
            ], style={'float':'left', 'width':'32.8%', 'margin':'2px', 'background-color':'#DEB887'}),
        ], style={'width':'100%', 'display':'block', 'overflow': 'hidden', 'display':'flex'}),

    ], style={'overflow':'auto'}),
])


# Save Upload data
@app.callback(Output('input_data_store', 'data'), Input('upload_json', 'contents'), 
                [State('upload_json', 'filename'), State('upload_json', 'last_modified'), State('input_data_store', 'data')])
def save_input_data(contents, filename, last_modified, input_data_store):
    if filename is None: 
        return input_data_store
    for name in filename:
        if not name.endswith('.json'):
            return no_update
        
    data = {}
    try:
        for filename, content in zip(filename, contents):
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            data[filename] = json.loads(decoded.decode('utf-8'))
    except Exception as e:
        print(e)

    return data




for x in range(1, 3):
    # Generate Slider data
    @app.callback([Output('select_slider_temporal_merge_'+str(x), 'marks'),
                Output('select_slider_temporal_merge_'+str(x), 'min'),
                Output('select_slider_temporal_merge_'+str(x), 'max'),
                Output('select_slider_temporal_merge_'+str(x), 'value')],
                Input('input_data_store', 'data'))
    def generate_slider_values(input_data_store):
        if input_data_store is None: return no_update
        # for val in input_data_store.values():
        #     date = val['created']
        #     if date[-1] == 'Z':
        #         date = date[:-1]
        #     if len(date.rsplit('.', 1)[1]) != 6:
        #         # date = date.rsplit('.', 1)[0] + '.000000'
        #         continue

        #     created = datetime.fromisoformat(date)
        #     # print(type(created))
        #     # print(created)
        #     # print(val['created'])
        
        marks = {}
        date_list = []
        for key, val in input_data_store.items():
        # for key, val in sorted(input_data_store.items(), key=lambda item: int(item[1]['created'])):
            # marks[val['created']] = key[:-5]
            marks[int(key[:-5])] = key[:-5]
            date_list.append(int(key[:-5]))

        start = min(date_list)
        end = max(date_list)

        return marks, start, end, [start, end]

    # Generate selected range
    @app.callback(Output('selected_range_'+str(x), 'children'), 
                [Input('select_slider_temporal_merge_'+str(x), 'value'), State('input_data_store', 'data')])
    def generate_selected_range(selected_range, input_data_store):
        if input_data_store is None: return input_data_store

        file1 = str(selected_range[0]) + '.json'
        file2 = str(selected_range[1]) + '.json'
        date1 = input_data_store[file1]['created']
        date2 = input_data_store[file2]['created']

        return html.P('Start: '+ date1), html.P('End: '+ date2)


    @app.callback(Output('json_tree_store_temporal_merge_'+str(x), 'data'), 
                [Input('select_slider_temporal_merge_'+str(x), 'value'),
                Input('selected_tab_store_merge', 'data'),
                State('input_data_store', 'data')])
    def save_json(selected_range, selected_tab, input_data_store):
        if selected_range is None or input_data_store is None: return no_update

        merge_strategy = get_selected_merge_strategy(selected_tab)
        selected_list = map(str, list(range(selected_range[0], selected_range[1]+1)))
        selected_filenames = [s+'.json' for s in selected_list]
        base, base_history = None, []

        for name in selected_filenames:
            new = flatten(input_data_store[name])
            base = json_merge(base, new, merge_strategy)
            base_history.append(base)

        return base_history

    
    @app.callback(Output('json_tree_temporal_merge_'+str(x), 'children'), Input('json_tree_store_temporal_merge_'+str(x), 'data'))
    def generate_json(json_tree):
        return json.dumps(json_tree, indent=2)




@app.callback([Output('json_tree_temporal_merge_3', 'children'), Output('num_changes', 'children')], 
            [Input('json_tree_store_temporal_merge_1', 'data'), Input('json_tree_store_temporal_merge_2', 'data')])
def generate_json(json_history_1, json_history_2):
    if json_history_1 is None or json_history_2 is None: return [], []

    # difference_history option 1
    difference, difference_history = None, []
    for i in range(max(len(json_history_1), len(json_history_2))):
        ix1 = min(i, len(json_history_1)-1)
        ix2 = min(i, len(json_history_2)-1)
        difference = diff(json_history_1[ix1], json_history_2[ix2], syntax='symmetric', marshal=True)
        difference_history.append(difference)

    # difference_history option 2 
    # difference_history = diff(json_history_1, json_history_2, syntax='symmetric', marshal=True)
        
    num_changes = {}

    for difference in difference_history:
        for key in difference.keys():
            if key in num_changes:
                num_changes[key] +=1 
            else:
                num_changes[key] = 1

    return (json.dumps(difference_history, indent=2), 
            ([html.P('Number of Changes per key'), html.Pre(json.dumps(num_changes, indent=2)), html.Br()]))