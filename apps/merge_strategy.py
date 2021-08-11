import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
import dash_table
from dash import no_update
import json_dash
import json
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

import io
import base64
import datetime

import pandas as pd


def generate_tab(label, value):
    return dcc.Tab(
                label=label,
                value=value,
                className='custom-tab',
                selected_className='custom-tab--selected'
            )


def generate_tabs(tabs_id, tab_labels, tab_values):
        return dcc.Tabs(
            id=tabs_id,
            parent_className='custom-tabs',
            className='custom-tabs-container',
            children=[
                generate_tab(label, value) for label, value in zip(tab_labels, tab_values)
            ],
        )



def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True


def get_data(filedir):
    with open(filedir) as f:
        data = json.load(f)
    for i in range(len(data)):
        data[i]['raw_response'] = json.loads(data[i]['raw_response'])

    return data


def generate_upload():
    return html.Div([
        dcc.Upload(
            id='upload-file',
            children=html.Div([
                'Drag and Drop or ', html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=True
        )
    ], id='topDiv')


def generate_json(component_id, data):
    return html.Div(id=component_id, children=[
        # html.Button('Submit', id='button'),
        # html.Div(dcc.Input(id='input-box', type='text')),
        json_dash.jsondash(
            id='json_merge_strategy',
            json=data,
            height=800,
            width=600,
            selected_node='',
        ),
        html.Div('', id='node_selected')
    ])


tab_labels = ['Original', 'Flattened', 'Overwrite', 'Version',
                      'Append', 'arrayMergeById', 'arrayMergeByIndex', 'objectMerge']
tab_values = ['tab-' + str(i) for i in range(1, len(tab_labels) + 1)]
data = get_data('datasets/cntr1_dataprovider.json') # TODO remove? or create placeholder file to instantiate json tree

# Layout
layout = html.Div([
    html.H1('Merge Strategy', style={"textAlign": "center"}),
    generate_upload(),
    html.Div(id='topDiv2', style={'text-align': 'center'}),

    html.Div([
        generate_tabs('tabs-1', tab_labels, tab_values),
        generate_json('json_merge_strategy_div', data=data),
    ], id='leftDiv', style={'float': 'left', 'width': '50%', "textAlign": "center", 'display': 'block'}),

    html.Div([
        html.P('Output something')
    ], id='rightDiv', style={'float': 'right', 'width': '50%', "textAlign": "center"})
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),
        html.P("Inset X axis data"),
        dcc.Dropdown(id='xaxis-data', options=[{'label': x, 'value': x} for x in df.columns], persistence=True),
        html.P("Inset Y axis data"),
        dcc.Dropdown(id='yaxis-data', options=[{'label': x, 'value': x} for x in df.columns], persistence=True),
        html.Button(id="submit-button", children="Create Graph"),
        html.Hr(),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=15
        ),
        dcc.Store(id='stored-data', data=df.to_dict('records')),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])



@app.callback(Output('rightDiv', 'children'),
              Input('submit-button','n_clicks'),
              State('stored-data','data'),
              State('xaxis-data','value'),
              State('yaxis-data', 'value'))
def update_graph(n, data, x_data, y_data):
    if n is None:
        return no_update
    else:
        bar_fig = px.bar(data, x=x_data, y=y_data)
        # print(data)
        return dcc.Graph(figure=bar_fig)




def flatten_json(data):
    for i in range(len(data)):
        data[i] = flatten(data[i])
    return data


def overwrite_json(data):
    schema = {'mergeStrategy': 'overwrite'}
    base = None
    mergeHistory = {}
    merger = Merger(schema)
    for i in range(len(data)):
        base = merger.merge(base, data[i])
        mergeHistory[str(i+1)] = base
    return mergeHistory


def version_json(data):
    schema = {'mergeStrategy': 'version'}
    base = None
    merger = Merger(schema)
    for i in range(len(data)):
        base = merger.merge(base, data[i], merge_options={'version': {'metadata': {'revision': i}}})
    return base

def append_json(data):
    schema = {'mergeStrategy': 'append'}
    base = None
    merger = Merger(schema)
    for i in range(len(data)):
        base = merger.merge(base, [data[i]])
    return base


def arrayMergeById_json(data):
    schema = {'mergeStrategy': 'arrayMergeById'}
    base = None
    merger = Merger(schema)
    for i in range(len(data)):
        base = merger.merge(base, [data[i]])
    return base


def arrayMergeByIndex_json(data):
    schema = {'mergeStrategy': 'arrayMergeByIndex'}
    base = None
    mergeHistory = {}
    merger = Merger(schema)
    for i in range(len(data)):
        base = merger.merge(base, [data[i]])
        mergeHistory[str(i + 1)] = base
    return mergeHistory


def objectMerge_json(data):
    schema = {'mergeStrategy': 'objectMerge'}
    base = None
    merger = Merger(schema)
    mergeHistory = {}
    for i in range(len(data)):
        base = merger.merge(base, data[i])
        mergeHistory[str(i + 1)] = base
    return mergeHistory


# @app.callback(
#     Output('json_merge_strategy', 'json'),
#     Input('tabs-1', 'value')
# )
# def render_tabs(active_tab):
#     data = get_data('datasets/cntr1_dataprovider.json')
#
#     if active_tab == 'tab-2':
#         data = flatten_json(data)
#     if active_tab == 'tab-3':
#         data = flatten_json(data)
#         data = overwrite_json(data)
#
#     if active_tab == 'tab-4':
#         data = flatten_json(data)
#         data = version_json(data)
#     if active_tab == 'tab-5':
#         data = flatten_json(data)
#         data = append_json(data)
#     if active_tab == 'tab-6':
#         data = flatten_json(data)
#         data = arrayMergeById_json(data)
#     if active_tab == 'tab-7':
#         data = flatten_json(data)
#         data = arrayMergeByIndex_json(data)
#     if active_tab == 'tab-8':
#         data = flatten_json(data)
#         data = objectMerge_json(data)
#
#     # for i in range(len(data)):
#     #     # print(type(data[i]))
#     #     data[i] = unflatten(data[i])
#
#     return data


@app.callback(
               Output('json_merge_strategy', 'json'),
              Input('upload-file', 'contents'),
              State('upload-file', 'filename'),
              State('upload-file', 'last_modified'))
def update_data_table(contents, filename, last_modified):
    # data =
    # print(type(contents))
    # pprint(contents)

    if contents is None:
        return no_update

    if 'json' in filename[0]:
        try:
            content_type, content_string = contents[0].split(',')
            decoded = base64.b64decode(content_string)
            json_dict = json.loads(decoded.decode('utf-8'))
            children = pd.DataFrame()  # TODO flatten into df format
        except Exception as e:
            print(e)
    else:
        children = [parse_contents(c, n, d) for c, n, d in zip(contents, filename, last_modified)]


    return html.Div([
        html.P('individual file info & metadata inputs'),
        html.P('missing data stats'),
        html.P('schema r/s discovery')
    ]), children, json_dict

