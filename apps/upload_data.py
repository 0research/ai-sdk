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
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from itertools import zip_longest
from datetime import datetime
from pandas import json_normalize
import io

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


id = id_factory('upload_data')
tab_labels = ['Step 1: Upload Data', 'Step 2: Set Data Profile', 'Step 3: Review Data']
tab_values = [id('upload_data'), id('set_data_profile'), id('review_data')]
datatype_list = ['object', 'string', 'Int64', 'datetime64', 'boolean', 'category']
option_filetype = [
    {'label': 'JSON', 'value': 'json'},
    {'label': 'CSV', 'value': 'csv'},
]

option_data_nature = [
    {'label': 'Numerical', 'value': 'numerical'},
    {'label': 'Categorical', 'value': 'categorical'},
    {'label': 'Hybrid', 'value': 'hybrid'},
    {'label': 'Time Series', 'value': 'time_series'},
    {'label': 'Geo Spatial', 'value': 'geo_spatial'},
]

option_delimiter = [
    {'label': 'Comma (,)', 'value': 'comma'},
    {'label': 'Pipe (|)', 'value': 'pipe'},
    {'label': 'Space', 'value': 'space'},
    {'label': 'Tab', 'value': 'tab'},
]



layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id='input_datatype_store', storage_type='session'),
    dcc.Store(id=id('remove_list_store'), storage_type='session'),
    
    generate_tabs(id('tabs_content'), tab_labels, tab_values),
    dbc.Container([], fluid=True, id=id('content')),
])


@app.callback(Output(id("content"), "children"), [Input(id("tabs_content"), "value")])
def generate_tab_content(active_tab):
    content = None
    if active_tab == id('upload_data'):
        content = dbc.Row([
            dbc.Col([
                html.H5('Step 1.1: Upload Data'),
                generate_upload('upload_json', "Drag and Drop or Click Here to Select Files"),
            ], className='text-center', width=6),
            
            dbc.Col([
                html.H5('Step 1.2: Select Settings'),
                html.Div('Type of Dataset', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                html.Div(generate_dropdown(id('dropdown_file_type'), option_data_nature), style={'width':'80%', 'display':'inline-block'}),

                html.Div('Delimiter', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                html.Div(generate_dropdown(id('dropdown_delimiter'), option_delimiter), style={'width':'80%', 'display':'inline-block'}),
                
                html.Div('Index Column', style={'width':'20%', 'display':'inline-block', 'vertical-align':'top'}),
                html.Div(generate_dropdown(id('dropdown_index_column'), [
                    {'label': 'Add New Index', 'value': 'new_index'},
                ]), style={'width':'80%', 'display':'inline-block'}),
    
                dbc.Checklist(options=[
                    {"label": "Remove Spaces", "value": 'remove_space'},
                    {"label": "Remove Header/First Row ", "value": 'remove_header'}
                ], inline=False, switch=True, id=id('checklist_settings'), value=['remove_space']),
            ], width=6),

            dbc.Col(html.Hr(), width=12),

            dbc.Col([
                dbc.Col(html.H5('Sample Data', style={'text-align':'center'})),
                dbc.Col(html.Div(generate_datatable(id('input_datatable_sample'))), width=12),
                html.Br(),
            ], width=12),

            dbc.Col([
                html.Div('Error Log', style={'text-align':'center', 'width':'100%'}, className='bg-warning'),
                html.Div('Error Log', style={'text-align':'center', 'width':'100%'}, className='bg-danger'),
                html.Br(),
                # html.Div(html.Button('Next Step', className='btn btn-primary', id=id('next_button_1')), className='text-center'),
            ], id=id('upload_errors'), width=12),
        ], className='text-center', style={'margin': '3px'}),


    elif active_tab == id('set_data_profile'):
        content = html.Div([
            dbc.Row(dbc.Col(html.H5('Step 3: Set Data Profile'), width=12)),
            html.Div(id=id('data_profile'), style={'overflow-y': 'auto', 'overflow-x': 'hidden', 'height':'600px', 'width':'100%', 'height':'800px'}),
            # html.Div(id=id('data_profile')),
            # html.Div(html.Button('Next Step', className='btn btn-primary', id=id('next_button_2')), className='text-center'),
        ], className='text-center', style={'margin': '3px'}),
        

    elif active_tab == id('review_data'):
        content = dbc.Row([
            dbc.Col(html.H5('Step 4: Review Data'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),
            html.Br(),
            dbc.Col(html.Div(html.Button('Upload Data', className='btn btn-primary', id=id('upload')), className='text-center'), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '3px'}),

    return content



# @app.callback(Output(id("tabs_content"), "value"), [Input(id("next_button"), "n_clicks"), State(id('tabs_content'), 'value')])
# def next_step_button(n_clicks, tab_value):
#     print('insdie')
#     if n_clicks is None: return tab_value

#     if tab_value == id('set_data_profile'):
#         return id('review_data')

#     return tab_value



# Save Upload data
@app.callback([Output('input_data_store', 'data'), Output('input_datatype_store', 'data')], 
                [Input('upload_json', 'contents'), 
                # Input(id('upload'), 'n_clicks'), 
                # State(id('checklist_settings'), 'value'), 
                State('upload_json', 'filename'), State('upload_json', 'last_modified'), State('input_data_store', 'data'), State('input_datatype_store', 'data'),
                State({'type':id('col_column'), 'index': ALL}, 'children'), State({'type':id('col_datatype'), 'index': ALL}, 'last_modified'), State('input_data_store', 'data')])
def save_input_data(contents, filename, last_modified, input_data_store, input_datatype_store, column_list, datatype_list, remove_list):
    if filename is None: 
        return input_data_store, input_datatype_store

    data = []
    # JSON 
    if all(f.endswith('.json') for f in filename):
        try:
            for filename, content in zip(filename, contents):
                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)
                decoded = json.loads(decoded.decode('utf-8'))
                decoded = flatten(decoded)
                data.append(decoded)
        except Exception as e:
            print(e)

        df = json_normalize(data)

    # CSV
    elif len(filename) == 1 and filename[0].endswith('csv'):
        content_type, content_string = contents[0].split(',')
        decoded = base64.b64decode(content_string)
        pprint(decoded)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=',', header=0)

    # if 'remove_space' in checklist_settings:
    #     pass
    # if 'remove_header' in checklist_settings:
    #     df = df.iloc[1: , :].reset_index(drop=True)

    datatype = list(map(str, df.convert_dtypes().dtypes))
    datatype = dict(zip(df.columns, datatype))

    return df.to_dict('records'), datatype


# On Upload or click next button go onto next tab
# @app.callback(Output(id('tabs_content'), 'value'), Input('input_data_store', 'data'))
# def next_step_after_upload(data):
#     print('aaainsidee')
#     if data == None: return no_update
#     return id('set_data_profile')


# Update datatable when files upload
@app.callback([Output(id('input_datatable_sample'), "data"), Output(id('input_datatable_sample'), 'columns')], 
                Input('input_data_store', "data"), Input('url', 'pathname'))
def update_data_table(input_data, pathname):
    if input_data == None: return [], []
        
    df = json_normalize(input_data).iloc[:10,:]
    df.insert(0, column='index', value=range(1, len(df)+1))
    json_dict = df.to_dict('records')

    # Convert all values to string
    for i in range(len(json_dict)):
        for key, val in json_dict[i].items():
            if type(json_dict[i][key]) == list:
                json_dict[i][key] = str(json_dict[i][key])

    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    return json_dict, columns

# Update datatable when files upload
@app.callback([Output(id('input_datatable'), "data"), Output(id('input_datatable'), 'columns')], 
                Input('input_data_store', "data"), Input('url', 'pathname'))
def update_data_table(input_data, pathname):
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




def generate_expectations():
    datatype = None # TODO get selected dropdown datatype from arg
    expectation = html.Div()

    if datatype == datatype_list[0]:    # Object
        pass
    elif datatype == datatype_list[1]:  # String
        pass
    elif datatype == datatype_list[2]:  # Int64
        pass
    elif datatype == datatype_list[3]:  # datetime64
        pass
    elif datatype == datatype_list[4]:  # boolean
        pass
    elif datatype == datatype_list[5]:  # category
        pass

    return [ 
        html.Div([
            expectation,
            html.Div('Not Null Threshold', style={'width':'40%', 'display':'inline-block', 'vertical-align':'top'}),
            html.Div(generate_slider(id('slider_not_null_threshold'), min=0, max=100, step=1, value=1), style={'width':'50%','display':'inline-block'}),
            html.Div(style={'width':'40%', 'display':'inline-block', 'vertical-align':'top'}, id=id('val_not_null_threshold')),
        ]),
    ]
    


@app.callback(Output(id('data_profile'), 'children'), 
            [Input('input_data_store', 'data'), 
            Input('input_datatype_store', 'data'),
            # Input(id('dropdown_datatype'), 'value') 
            Input('url', 'pathname')])
def generate_profile(data, datatype, pathname):
    if data == None: return [], []
    df = json_normalize(data)
    columns = list(df.columns)

    detected_datatype_list = list(datatype.values())
    option_datatype = [
        {'label': 'object', 'value': 'object'},
        {'label': 'string', 'value': 'string'},
        {'label': 'Int64', 'value': 'Int64'},
        {'label': 'datetime64', 'value': 'datetime64'},
        {'label': 'boolean', 'value': 'boolean'},
        {'label': 'category', 'value': 'category'}
    ]

    return (
        [dbc.Row([])] +
        [dbc.Row([
            dbc.Col(html.H6('Column'), width=3),
            dbc.Col(html.H6('Datatype'), width=3),
            dbc.Col(html.H6('Invalid(%)'), width=2),
            dbc.Col(html.H6('Result'), width=2),
        ])] +
        [dbc.Row([
        dbc.Col(html.H6(col), id={'type':id('col_column'), 'index': i}, width=3),
        dbc.Col(generate_dropdown({'type':id('col_dropdown_datatype'), 'index': i}, option_datatype, value=dtype), width=3),
        dbc.Col(html.H6('%', id={'type':id('col_invalid'), 'index': i}), width=2),
        dbc.Col(html.H6('-', id={'type':id('col_result'), 'index': i}), width=2),
        dbc.Col(html.Button('Remove', id={'type':id('col_button_remove'), 'index': i}, value=col), width=1),
    ]) for i, (col, dtype) in enumerate(zip(columns, detected_datatype_list))])



# @app.callback(Output('asd', 'data'),
#             [Input({'type':id('col_dropdown_datatype'), 'index': ALL}, 'value'),
#             Input({'type':id('col_button_remove'), 'index': MATCH}, 'n_clicks'),
#             State({'type':id('col_column'), 'index': ALL}, 'children')])
# def update_output(datatypes, column):
#     pprint(datatypes)
#     print(column)
#     return no_update

@app.callback(Output(id('val_not_null_threshold'), 'children'),
            [Input(id('slider_not_null_threshold'), 'value')])
def update_output(value):
    return value


# Remove Buttons
@app.callback(Output(id('remove_list_store'), 'data'),
            [Input({'type':id('col_button_remove'), 'index': ALL}, 'n_clicks'),
            State({'type':id('col_button_remove'), 'index': ALL}, 'value'),
            State(id('remove_list_store'), 'data')])
def update_output(n_clicks, value, remove_list):
    if remove_list is None: remove_list = []

    if value in remove_list:
        remove_list.remove(value)
    else:
        remove_list.append(value)

    print('remove_list ', remove_list)
    return remove_list