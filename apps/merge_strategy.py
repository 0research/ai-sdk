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
from pandas.io.json import json_normalize
from itertools import zip_longest


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('merge_strategy')


def generate_radio(id, options, label, default_value=0):
    return dbc.FormGroup(
        [
            dbc.Label(label),
            dbc.RadioItems(
                options=[{'label': o, 'value': o} for o in options],                 
                value=options[default_value],
                id=id,
                # className='custom-radio',
            )
        ]
    )

# Layout
layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id=id('merge_strategy_store'), storage_type='session'),
    dcc.Store(id=id('selected_list_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),

    dbc.Container([
        # Page Title
        # dbc.Row(dbc.Col(html.H2('Merge Strategy'))),

        # Upload Files
        dbc.Row([
            dbc.Col(generate_upload('upload_json', "Drag and Drop or Click Here to Select Files"), className='text-center'),
        ], className='text-center', style={'margin': '5px'}),

        # Options
        dbc.Row([
            dbc.Col(html.H5('Step 1: Select Merge Options'), width=12),
            dbc.Col(html.Div(generate_radio(id('merge_radio'), mergeOptions, "Select One Merge Strategy")), width=4),
            dbc.Col(html.Div(generate_radio(id('flatten_radio'), flattenOptions, "Select Json Display type")), width=4),
            dbc.Col(html.Div('Other options?'), width=4),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

        # Datatable & Selected Rows/Json List
        dbc.Row([
            dbc.Col(html.H5('Step 2: Select Rows to Merge'), width=12),
            dbc.Col(html.Div(children=generate_datatable())),
            dbc.Col(html.H5('Selection: None', id=id('selected_list')), width=12),
            dbc.Col(html.Button('Clear Selection', className='btn-secondary', id=id('button_clear')), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

        # Json Data Headers
        dbc.Row([
            dbc.Col(html.H5('Step 3: Select the First or Second Panel to Display Merged Selection'), width=12),

            dbc.Col(html.Button('Display Merge History', className='btn-success btn-block', style={'font-size':'20px'}, id=id('button_json_1')), width=4),
            dbc.Col(html.Button('Display Merge History', className='btn-info btn-block', style={'font-size':'20px'}, id=id('button_json_2')), width=4),
            dbc.Col(html.Button('Observe Difference', className='btn-danger btn-block', style={'font-size':'20px'}, disabled=True), width=4),

            dbc.Col(html.H6(id=id('selected_list_1')), width=4),
            dbc.Col(html.H6(id=id('selected_list_2')), width=4),
            dbc.Col(html.H6(), width=4),

            dbc.Col(html.Pre(id=id('json_1'), className='text-left bg-success text-white'), width=4),
            dbc.Col(html.Pre(id=id('json_2'), className='text-left bg-info text-white'), width=4),
            dbc.Col(html.Pre(id=id('json_3'), className='text-left bg-danger text-white'), width=4),
        ], className='text-center bg-light'),
        
    ], style={'width':'100%', 'maxWidth':'100%'}),
    
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
        
    data = []
    try:
        for filename, content in zip(filename, contents):
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            decoded = json.loads(decoded.decode('utf-8'))
            data.append(decoded)

    except Exception as e:
        print(e)

    return data

# Update datatable when files upload
@app.callback([Output('input_data_datatable', "data"), Output('input_data_datatable', 'columns')], 
                Input('input_data_store', "data"))
def update_data_table(input_data):
    if input_data == None: return [], []

    df = json_normalize(input_data)
    df.insert(0, column='index', value=range(1, len(df)+1))
    json_dict = df.to_dict('records')

    # Convert all values to string
    for i in range(len(json_dict)):
        for key, val in json_dict[i].items():
            if type(json_dict[i][key]) == list:
                json_dict[i][key] = str(json_dict[i][key])

    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    return json_dict, columns


# Store/Clear selected rows
@app.callback([Output(id('selected_list_store'), "data"), Output('input_data_datatable', "selected_rows")],
            Input('input_data_datatable', "selected_rows"), Input(id('button_clear'), 'n_clicks'))
def save_table_data(selected_rows, n_clicks):
    triggered = callback_context.triggered[0]['prop_id']

    if triggered == 'merge_strategy-button_clear.n_clicks':
        selected_rows = []
    elif triggered == 'input_data_datatable.derived_virtual_selected_rows':
        pass

    return selected_rows, selected_rows


# Display selected rows/json
@app.callback(Output(id('selected_list'), "children"), Input(id('selected_list_store'), 'data'))
def generate_selected_list(selected_list):
    return 'Selection: ', str(selected_list)[1:-1]




# Saves last selected merge strategy
@app.callback(Output(id('merge_strategy_store'), 'data'), Input(id('merge_radio'), 'value'))
def save_merge_strategy(merge_strategy):
    return merge_strategy


# Update Json Trees
for x in range(1, 3):
    @app.callback(Output(id('selected_list_'+str(x)), 'children'), 
                [Input(id('button_json_')+str(x), 'n_clicks'), State(id('selected_list_store'), 'data')])
    def display_selected(n_clicks, selected_list):
        return str(selected_list)[1:-1]

    @app.callback(Output(id('json_store_')+str(x), 'data'), 
                [Input(id('button_json_')+str(x), 'n_clicks'),
                State(id('selected_list_store'), 'data'), State(id('merge_strategy_store'), 'data'), State('input_data_store', 'data')])
    def save_json(n_clicks, selected_list, merge_strategy, input_data):
        if selected_list is None or len(selected_list) == 0: return []
        triggered = callback_context.triggered[0]['prop_id']
        if triggered == '.': return [], []

        merge_strategy = get_selected_merge_strategy(merge_strategy)
        selected_filenames = [str(s)+'.json' for s in selected_list]
        base, base_history = None, []

        for i in range(len(selected_list)):
            # TODO hard code convert raw response to json
            if 'raw_response' in input_data[i]:
                input_data[i]['raw_response'] = json.loads(input_data[i]['raw_response'])

            new = flatten(input_data[i])
            base = json_merge(base, new, merge_strategy)
            base_history.append(base)

        return base_history

    @app.callback(Output(id('json_')+str(x), 'children'), Input(id('json_store_')+str(x), 'data'))
    def generate_json(json_tree):
        return json.dumps(json_tree, indent=2)


@app.callback(Output(id('json_3'), 'children'), 
            [Input(id('json_store_1'), 'data'), Input(id('json_store_2'), 'data')])
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

