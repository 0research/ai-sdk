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
from jsondiff import diff
from apps.util import *
import base64
import pandas as pd

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


tab_labels = ['Overwrite', 'objectMerge']
tab_values = ['tab-' + str(i) for i in range(1, len(tab_labels) + 1)]

# Layout
layout = html.Div([
    dcc.Store(id='input_data', storage_type='session'),
    dcc.Store(id='selected_list_store', storage_type='session'),
    html.H1('Merge Strategy', style={"textAlign": "center"}),
    generate_upload(),
    html.Div(id='topDiv2', style={'text-align': 'center'}, children=[
        dbc.ButtonGroup(id='select_list'),
        html.Div(id='selected_list'),
        html.Button('Clear Selection', id={'type': 'select_button', 'index': -1}),
    ]),

    html.Div([
        generate_tabs('tabs-1', tab_labels, tab_values),
        html.Div([
            html.Pre(id='json_tree', style={"textAlign": "left"})
        ], id='leftDiv', style={'float': 'left', 'width': '50%', "textAlign": "center"}),

        html.Div([
            html.Pre(id='json_tree2', children=[], style={"textAlign": "left"})
        ], id='rightDiv', style={'float': 'right', 'width': '50%', "textAlign": "center"})
    ], id='contentDiv', style={'display':'block'})
])

def get_selected_merge_strategy(selected_tab):
    merge_strategy = None
    if selected_tab == 'tab-1': merge_strategy = 'overwrite'
    elif selected_tab == 'tab-2': merge_strategy = 'version'
    elif selected_tab == 'tab-6': merge_strategy = 'objectMerge'

    return merge_strategy



def json_merge(base, new, merge_strategy):
    schema = {'mergeStrategy': merge_strategy}
    merger = Merger(schema)
    base = merger.merge(base, new)
    return base


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
# @app.callback([Output('select_list', 'children'),
#                Output('leftDiv', 'children'),
#                Output('contentDiv', 'style'),
#                Output('json_tree', 'children'),
#                Output('json_tree2', 'children')],
#               [Input('input_data', 'data'),
#                Input('tabs-1', 'value')],
#               [State('upload-file', 'filename'),
#               State('upload-file', 'last_modified')])
# def update_data_table(contents, selected_tab, filename, last_modified):
#     ctx = callback_context

#     if ctx.triggered[0]['prop_id'].split('.')[0] == 'input_data':
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




# Saves input file data in Store
@app.callback(Output('input_data', 'data'), Input('upload-file', 'contents'), 
            [State('upload-file', 'filename'), State('upload-file', 'last_modified')])
def save_input_data(contents, filename, last_modified):
    if filename is None:
        return no_update
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



@app.callback(Output('select_list', 'children'), Input('input_data', 'data'))
def generate_select(input_data):
    return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button', 'index': name.split('.')[0]}) for name in sorted(input_data.keys(), key=lambda x:x[:-5])]


@app.callback(Output('selected_list_store', 'data'),
            Input({'type': 'select_button', 'index': ALL}, 'n_clicks'),
            State('selected_list_store', 'data'))
def store_selected(n_clicks, selected_list):
    if all(v is None for v in n_clicks): return no_update
    if selected_list is None: selected_list = []
    triggered_id = json.loads(callback_context.triggered[0]['prop_id'].split('.')[0])['index']

    # If clicked on Clear Selection
    if triggered_id == -1:
        return []

    # Return selected
    else:
        selected_list.append(triggered_id)
        
    return selected_list


@app.callback(Output('selected_list', 'children'), Input('selected_list_store', 'data'))
def generate_selected(selected_list):
    return str(selected_list)


# Update Left and Right Json Trees
@app.callback([Output('json_tree', 'children'), Output('json_tree2', 'children')], 
            [Input('selected_list_store', 'data'), 
            Input('tabs-1', 'value')],
            State('input_data', 'data'))
def generate_json(selected_list, selected_tab, input_data):
    if selected_list == None or len(selected_list) == 0:
        return [], []

    selected_filenames = [s+'.json' for s in selected_list]
    merge_strategy = get_selected_merge_strategy(selected_tab)
    mergeHistory = []
    version_merge_data = []
    difference_list = []

    # Get Selected Merge Data
    if merge_strategy == 'version':
        flat_base = None
        start_index = 0
    elif merge_strategy in ['append', 'arrayMergeById', 'arrayMergeByIndex']:
        if type(input_data[selected_filenames[0]]) is not list:
            print("Input must be List")
            return json.dumps("Invalid Datatype", indent=2)
    else:
        base = input_data[selected_filenames[0]]
        flat_base = flatten_json(base)
        mergeHistory.append(flat_base)
        start_index = 1
    
    for name in selected_filenames[start_index:]:
        new = flatten(input_data[name])
        flat_base = json_merge(flat_base, new, merge_strategy)
        mergeHistory.append(flat_base)

    if len(selected_list) >= 2:
        # Get Version Merge Data
        for i in range(len(selected_list)):
            new = flatten(input_data[selected_filenames[i]])
            version_merge_data = json_merge(version_merge_data, new, 'version')
            # version_merge_data.append(flat_base)

        # Get Difference between Selected Merge Data and Version
        if merge_strategy == 'version':
            difference = []
        else:
            for i in range(len(selected_list)):
                difference = diff(mergeHistory[i], version_merge_data[i]['value'], syntax='symmetric')
                difference_list.append(difference)
        
    return json.dumps(mergeHistory, indent=2), json.dumps(difference_list, indent=2)



