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
from datetime import datetime


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('upload_data')

layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    # Upload Files
    dbc.Row([
        dbc.Col(html.H5('Step 1: Upload Data'), width=12),
        dbc.Col(generate_upload('upload_json', "Drag and Drop or Click Here to Select Files"), className='text-center'),
    ], className='text-center', style={'margin': '5px'}),

    dbc.Row([
        dbc.Col(html.H5('Step 2: Analyze Uploaded Data'), width=12),
        dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),
    ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
])

# Save Upload data
@app.callback(Output('input_data_store', 'data'), Input('upload_json', 'contents'), 
                [State('upload_json', 'filename'), State('upload_json', 'last_modified'), State('input_data_store', 'data')])
def save_input_data(contents, filename, last_modified, input_data_store):
    print('upload1')
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
            decoded = flatten(decoded)
            data.append(decoded)

    except Exception as e:
        print(e)

    return data


# Update datatable when files upload
@app.callback([Output(id('input_datatable'), "data"), Output(id('input_datatable'), 'columns')], 
                Input('input_data_store', "data"), Input('url', 'pathname'))
def update_data_table(input_data, pathname):
    print('insidesss1')
    if input_data == None: return [], []
    # for i in range(len(input_data)):
    #     input_data[i] = flatten(input_data[i])
        
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