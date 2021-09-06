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

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


tab_labels = ['Overwrite', 'objectMerge', 'version']
tab_values = ['tab-' + str(i) for i in range(1, len(tab_labels) + 1)]



# Layout
layout = html.Div([
    dcc.Store(id='input_data_store_merge_1', storage_type='session'),
    dcc.Store(id='input_data_store_merge_2', storage_type='session'),
    dcc.Store(id='selected_tab_store_merge', storage_type='session'),
    dcc.Store(id='selected_list_store_merge_1', storage_type='session'),
    dcc.Store(id='selected_list_store_merge_2', storage_type='session'),
    dcc.Store(id='selected_list_store_merge_3', storage_type='session'),
    dcc.Store(id='json_tree_merge_store_1', storage_type='session'),
    dcc.Store(id='json_tree_merge_store_2', storage_type='session'),
    html.H1('Merge Strategy', style={"textAlign": "center"}),
    
    html.Div(children=[
        html.H4('Step 1: Select Merge Strategy', style={'text-align':'center'}),
        generate_tabs('tabs-1', tab_labels, tab_values),
    ], style={'background-color':'#F5F5DC', 'padding':'5px 25px 25px 5px'}),
    
    
    html.Div([
        html.Div([
            html.Div([
                html.H4('Step 2: Merge History I', style={'textAlign': 'center'}),
                generate_upload('upload_json_merge_1'),
                html.H4("Step 3: Select files to merge"),
                html.Div(id='merge_selection_div_1', children=generate_selection(1), style={'text-align': 'center'}),
            ], style={'float': 'left', 'width': '33%', "textAlign": "center", 'background-color': '#E6E6FA', 'margin': '2px'}),
            html.Div([
                html.H4('Step 4: Merge History II', style={'textAlign': 'center'}),
                generate_upload('upload_json_merge_2'),
                html.H4("Step 5: Select files to merge"),
                html.Div(id='merge_selection_div_2', children=generate_selection(2), style={'text-align': 'center'}),
            ], style={'float': 'left', 'width': '33%', "textAlign": "center", 'background-color': '#E6E6FA', 'margin': '2px'}),
            html.Div([
                html.H4('Step 6: Observe Difference', style={'textAlign': 'center'}),
            ], style={'float': 'left', 'width': '33%', "textAlign": "center", 'background-color': '#E6E6FA', 'margin': '2px', 'height':'100'}),
        ], style={'width':'100%', 'display':'block', 'overflow': 'hidden', 'display':'flex'}),
        
        html.Div([
            html.Div([
                html.Pre(id='json_tree_merge_1', style={"textAlign": "left"}),
            ], style={'float': 'left', 'width': '33%', "textAlign": "center", 'background-color': '#E6E6FA', 'margin': '2px'}),
            html.Div([
                html.Pre(id='json_tree_merge_2', children=[], style={"textAlign": "left"})
            ], style={'float': 'left', 'width': '33%', "textAlign": "center", 'background-color': '#E6E6FA', 'margin': '2px'}),
            html.Div([
                html.Pre(id='json_tree_merge_3', children=[], style={"textAlign": "left"})
            ], style={'float': 'left', 'width': '33%', "textAlign": "center", 'background-color': '#E6E6FA', 'margin': '2px'})
        ], style={'width':'100%', 'display':'block', 'display':'flex'}),

        

    ], id='contentDiv', style={'display':'block', "margin-top": '10px'})
])



# Saves input file data in Store
for x in range(1, 3):
    @app.callback(Output('input_data_store_merge_'+str(x), 'data'), Input('upload_json_merge_'+str(x), 'contents'), 
                [State('upload_json_merge_'+str(x), 'filename'), State('upload_json_merge_'+str(x), 'last_modified'), State('input_data_store_merge_'+str(x), 'data')])
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



@app.callback(Output('select_list_merge_1', 'children'), Input('input_data_store_merge_1', 'data'))
def generate_select(input_data):
    if input_data == None: return no_update
    return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_merge_1', 'index': name.split('.')[0]}) for name in sorted(input_data.keys(), key=lambda x:int(x[:-5]))]

@app.callback(Output('select_list_merge_2', 'children'), Input('input_data_store_merge_2', 'data'))
def generate_select(input_data):
    if input_data == None: return no_update
    return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_merge_2', 'index': name.split('.')[0]}) for name in sorted(input_data.keys(), key=lambda x:int(x[:-5]))]



for x in range(1, 3):
    @app.callback(Output('selected_list_store_merge_'+str(x), 'data'),
                Input({'type': 'select_button_merge_'+str(x), 'index': ALL}, 'n_clicks'),
                State('selected_list_store_merge_'+str(x), 'data'))
    def store_selected(n_clicks, selected_list):
        if all(v is None for v in n_clicks): return selected_list
        if selected_list is None: selected_list = []
        triggered_id = json.loads(callback_context.triggered[0]['prop_id'].split('.')[0])['index']

        # If clicked on Clear Selection
        if triggered_id == -1:
            return []
        # Return selected
        else:
            selected_list.append(triggered_id)
            
        return selected_list

    @app.callback(Output('selected_list_merge_'+str(x), 'children'), Input('selected_list_store_merge_'+str(x), 'data'))
    def generate_selected(selected_list):
        if selected_list == None: return None
        
        selected_filenames = ''
        if selected_list is not None and len(selected_list) >= 2:
            selected_filenames = selected_list[-2] , '.json & ' , selected_list[-1] , '.json'
        return str(list(map(int, selected_list)))[1: -1]


# Saves last selected tab
@app.callback(Output('selected_tab_store_merge', 'data'), Input('tabs-1', 'value'))
def save_selected_tab(selected_tab):
    return selected_tab


# Update Json Trees
for x in range(1, 3):
    @app.callback(Output('json_tree_merge_store_'+str(x), 'data'), 
                [Input('selected_list_store_merge_'+str(x), 'data'), 
                Input('selected_tab_store_merge', 'data'),
                State('input_data_store_merge_'+str(x), 'data')])
    def save_json(selected_list, selected_tab, input_data):
        if selected_list is None: return no_update
        triggered = callback_context.triggered[0]['prop_id']
        if triggered == '.': return [], []

        merge_strategy = get_selected_merge_strategy(selected_tab)
        selected_filenames = [s+'.json' for s in selected_list]
        base, base_history = None, []

        for name in selected_filenames:
            new = flatten(input_data[name])
            base = json_merge(base, new, merge_strategy)
            base_history.append(base)
            
        return base_history

    @app.callback(Output('json_tree_merge_'+str(x), 'children'), Input('json_tree_merge_store_'+str(x), 'data'))
    def generate_json(json_tree):
        return json.dumps(json_tree, indent=2)


@app.callback(Output('json_tree_merge_3', 'children'), 
            [Input('json_tree_merge_store_1', 'data'), Input('json_tree_merge_store_2', 'data')])
def generate_json(json_history_1, json_history_2):
    if json_history_1 is None or json_history_2 is None: return []

    # difference_history option 1
    difference, difference_history = None, []
    for json_1, json_2 in list(zip_longest(json_history_1, json_history_2)):
        difference = diff(json_1, json_2, syntax='symmetric', marshal=True)
        difference_history.append(difference)

    # difference_history option 2 
    # difference_history = diff(json_history_1, json_history_2, syntax='symmetric', marshal=True)
        
    return json.dumps(difference_history, indent=2)


# @app.callback(Output('rightDiv', 'children'),
#               Input('submit-button','n_clicks'),
#               State('stored-data','data'),
#               State('xaxis-data','value'),
#               State('yaxis-data', 'value'))
# def update_graph(n, data, x_data, y_data):
#     if n is None:
#         return no_update
#     else:
#         bar_fig = px.bar(data, x=x_data, y=y_data)
#         # print(data)
#         return dcc.Graph(figure=bar_fig)


# Update JSON Tree, Datatable and Tab Selection
# @app.callback([Output('select_list_merge_1', 'children'),
#                Output('leftDiv', 'children'),
#                Output('contentDiv', 'style'),
#                Output('json_tree_merge_1', 'children'),
#                Output('json_tree_merge_2', 'children')],
#               [Input('input_data_store', 'data'),
#                Input('tabs-1', 'value')],
#               [State('upload-file', 'filename'),
#               State('upload-file', 'last_modified')])
# def update_data_table(contents, selected_tab, filename, last_modified):
#     ctx = callback_context

#     if ctx.triggered[0]['prop_id'].split('.')[0] == 'input_data_store':
#         pass

#     if ctx.triggered[0]['prop_id'].split('.')[0] == 'tabs-1':
#         return no_update


#     json_selection = [dbc.Button(name.split('.')[0], id=('json_select_'+str(name.split('.')[0]))) for name in filename]

#     # Get Version merge data
#     schema = {'mergeStrategy': 'version'}
#     base = None
#     merger = Merger(schema)
#     base = merger.merge(base, json_dict, merge_options={'version': {'metadata': {'revision': 1}}})

#     # Get selected merge data
#     json_dict = render_tabs_json_data(json_dict, selected_tab)

#     # Overwrite Selected data with version data
#     schema = {'mergeStrategy': 'overwrite'}
#     mergeHistory = {}
#     merger = Merger(schema)
#     for i, (selected, version) in enumerate(zip(json_dict, base)):
#         merge = merger.merge(selected, version['value'])
#         mergeHistory[str(i)] = merge

#     difference = diff(json_dict, mergeHistory, syntax='symmetric')

#     return json_selection, no_update, {'display':'block'}, json.dumps(json_dict, indent=2), json.dumps(difference, indent=2)
