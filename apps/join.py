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
from jsonmerge import Merger

options_merge_type = [
    {'label': 'Overwrite', 'value':'overwrite'},
    {'label': 'ObjectMerge', 'value':'objectMerge'},
    {'label': 'Version', 'value':'version'},
]

id = id_factory('join')

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Layout
layout = html.Div([
    dcc.Store(id=id('selection_list_store'), storage_type='session'),

    dbc.Container([
        dbc.Row([
            # Left Panel
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Data Catalog')),
                    dbc.CardBody([
                        dbc.Input(type="search", id=id('search'), debounce=False, placeholder="Search...", style={'text-align':'center'}),
                        html.Div(id=id('search_result'), style={'height':'400px', 'overflow-y':'auto'}),
                    ]),
                    
                    dbc.CardBody([
                        dbc.InputGroup([
                            dbc.InputGroupText("Type of Merge", style={'font-weight':'bold', 'font-size': '12px', 'padding-left':'12px'}),
                            dbc.Select(options=options_merge_type, id=id('join_type'), value=options_merge_type[0]['value'], style={'min-width':'120px', 'text-align':'center'}, persistence_type='session', persistence=True), 
                        ]), 
                    ]),

                ]),
            ], width=5),

            # Right Panel
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('Data Catalog')),
                    dbc.CardBody([
                        html.Div(id=id('json_list'), style={'height':'400px', 'overflow-x':'scroll'})
                    ])
                ]),
            ], width=7),
        ], className='text-center bg-light'),

    ], fluid=True, id=id('content')),
])

# Search Raw Datasets
@app.callback(Output(id('search_result'), 'children'),
                Input(id('search'), 'value'))
def search(search_value):
    if search_value == '' or search_value is None: return no_update

    search_type = 'dataset'
    if search_type == 'dataset': query_by = ['description', 'column']
    elif search_type == 'project': query_by = ['description']
    elif search_type == 'question': query_by = ['description']

    search_parameters = {
        'q': search_value,
        'query_by'  : query_by,
        'per_page': 250,
    }
    dataset_list = search_documents(search_type, 250, search_parameters)
    
    out = html.Table(
        [
            html.Tr([
                html.Th('No.'),
                html.Th('Description'),
                html.Th('Index'),
                html.Th('Target'),
                html.Th(''),
            ])
        ] + 
        [
            html.Tr([
                html.Td(i+1),
                html.Td(dataset['id'], id={'type':id('col_id'), 'index': i}, style={'display':'none'}),
                html.Td(dataset['description'], id={'type':id('col_description'), 'index': i}),
                html.Td(dataset['index'][1:-1], id={'type':id('col_index'), 'index': i}),
                html.Td(dataset['target'][1:-1], id={'type':id('col_target'), 'index': i}),
                html.Td([
                    dbc.Button('Add', id={'type':id('col_button'), 'index': i}),
                ]),
            ], id={'type':id('row'), 'index': i}) for i, dataset in enumerate(dataset_list)
        ],
        style={'width':'100%', 'height':'800px'}, id=id('table_data_profile')
    )

    return out


# Add dataset to Right Panel
@app.callback(
    Output(id('json_list'), 'children'),
    Input({'type':id('col_button'), 'index': ALL}, 'n_clicks'),
    State({'type':id('col_id'), 'index': ALL}, 'children'),
    prevent_initial_call=True,            
)
def add_dataset(n_clicks_list, col_id_list):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    pprint(n_clicks_list)
    pprint(col_id_list)
    print('triggered:  ', triggered)
    # print(col)

    return no_update


# @app.callback(Output(id('datatable_1'), "data"), 
#                 Output(id('datatable_1'), 'columns'), 
#                 Input('url', 'pathname'),)
# def generate_datatable1(pathname):
#     dataset_id_multiple = ast.literal_eval(get_session('dataset_id_multiple'))
#     if len(dataset_id_multiple) != 2: return no_update
#     dataset_id = dataset_id_multiple[0]
#     df = get_dataset_data(dataset_id)
#     json_dict = df.to_dict('records')
#     columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]

#     return json_dict, columns


# @app.callback(Output(id('datatable_2'), "data"), 
#                 Output(id('datatable_2'), 'columns'), 
#                 Input('url', 'pathname'),)
# def generate_datatable2(pathname):
#     dataset_id_multiple = ast.literal_eval(get_session('dataset_id_multiple'))
#     if len(dataset_id_multiple) != 2: return no_update
#     dataset_id = dataset_id_multiple[1]
#     df = get_dataset_data(dataset_id)
#     json_dict = df.to_dict('records')
#     columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]

#     return json_dict, columns



# # Save Selected Columns
# @app.callback(Output(id('selection_list_store'), "data"), 
#                 Input(id('datatable_1'), "selected_columns"),
#                 Input(id('datatable_2'), "selected_columns"))
# def save_selected_column(selected_columns_1, selected_columns_2):
#     if selected_columns_1 is None: selected_columns_1 = []
#     if selected_columns_2 is None: selected_columns_2 = []

#     return selected_columns_1 + selected_columns_2


# # Display Selection
# @app.callback(Output(id('selection_list'), 'children'),
#                 Input(id('selection_list_store'), "data"))
# def display_selected_column(selected_columns):
#     return 'Selection: ', str(selected_columns)[1:-1]


# def join_datasets(df_list, how, on):
#     try:
#         df = pd.merge(df_list[0], df_list[1], how=how, on=on)
#         return df
#     except Exception as e:
#         print(e)

    

# @app.callback(Output(id('datatable_3'), "data"), 
#                 Output(id('datatable_3'), 'columns'), 
#                 Input(id('selection_list_store'), 'data'),
#                 Input(id('join_type'), 'value'))
# def generate_datatable3(selection_list, join_type):
#     dataset_id_1 = ast.literal_eval(get_session('dataset_id_multiple'))[0]
#     dataset_id_2 = ast.literal_eval(get_session('dataset_id_multiple'))[1]
#     df1 = get_dataset_data(dataset_id_1)
#     df2 = get_dataset_data(dataset_id_2)

#     if join_type == 'append':
#         df = pd.concat([df1, df2], ignore_index=True, sort=False)
#         json_dict = df.to_dict('records')
#         columns = [{"name": i, "id": i, "deletable": False, "selectable": False} for i in df.columns]
#         return json_dict, columns

#     if selection_list is None or len(selection_list) != 2: return [], []
#     elif join_type == 'inner':
#         df = join_datasets([df1, df2], how='inner', on=[selection_list[0], selection_list[1]])
#     elif join_type == 'outer':
#         df = join_datasets([df1, df2], how='inner', on=[selection_list[0], selection_list[1]])
#     elif join_type == 'left':
#         df = join_datasets([df1, df2], how='inner', on=[selection_list[0], selection_list[1]])
#     elif join_type == 'right':
#         df = join_datasets([df1, df2], how='inner', on=[selection_list[0], selection_list[1]])
#     json_dict = df.to_dict('records')
#     columns = [{"name": i, "id": i, "deletable": False, "selectable": False} for i in df.columns]

#     print(df.shape)

#     return json_dict, columns


# @app.callback(Output('modal_confirm', "children"),
#                 Input(id('button_confirm'), 'n_clicks'),
#                 State(id('datatable_3'), 'data'),
#                 State(id('join_type'), 'value'),
#                 State(id('selection_list_store'), 'data'),)
# def button_confirm(n_clicks, datatable_data, join_type, columns):
#     if n_clicks is None: return no_update
#     dataset_id_mulitple = ast.literal_eval(get_session('dataset_id_multiple'))
#     dataset_id_1 = ast.literal_eval(get_session('dataset_id_multiple'))[0]
#     dataset_id_2 = ast.literal_eval(get_session('dataset_id_multiple'))[1]
#     dataset_1 = get_document('dataset', dataset_id_1)
#     dataset_2 = get_document('dataset', dataset_id_2)


#     # merger = Merger(schema)

#     if join_type == 'append': 
#         # dataset = merge(dataset_1, dataset_2)
#         columns = [None, None]
#     # if join_type == 'inner': dataset = merge(dataset_1, dataset_2)
#     # if join_type == 'outer': dataset = merge(dataset_1, dataset_2)
#     # if join_type == 'left': dataset = merge(dataset_1, dataset_2)
#     # if join_type == 'right': dataset = merge(dataset_2, dataset_1)

#     dataset = dataset_1

#     action_details = {
#         'join_type': join_type,
#         'column_1': columns[0],
#         'column_2': columns[1]
#     }
        
#     print('dataset'*10)
#     pprint(dataset)

#     join(get_session('project_id'), dataset_id_mulitple, '', datatable_data, dataset, action_details)
#     return no_update