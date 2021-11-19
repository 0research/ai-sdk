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
from jsondiff import diff
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from itertools import zip_longest
from datetime import datetime
from pandas import json_normalize
from apps.typesense_client import *

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('overview')


def bar_graph(component_id, barmode, x=None, y=None, data=None, orientation='v', showlegend=True):
    colors = {
        'background': '#111111',
        'text': '#7FDBFF'
    }

    if x == None: x='Fruit'
    if y == None: y='Amount'
    if data == None:
        data = pd.DataFrame({
            "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
            "Amount": [4, 1, 2, 2, 4, 5],
            "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
        })

    fig = px.bar(data, x=x, y=y, color="City", barmode=barmode, orientation=orientation)

    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        showlegend=showlegend
    )

    return dcc.Graph(
        id=component_id,
        figure=fig
    ),


option_date = [
    {'label': 'Minute', 'value': 'minute'},
    {'label': 'Hour', 'value': 'hour'},
    {'label': 'Day', 'value': 'day'},
    {'label': 'Year', 'value': 'year'},
    {'label': 'Month', 'value': 'month'},
]


def card_content(card_header, card_body):
    return [dbc.CardHeader(card_header), dbc.CardBody(card_body)]
    


layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id='input_datatype_store', storage_type='session'),
    
    dbc.Container([
        dbc.Row(dbc.Col(html.H1('Overview')), style={'text-align':'center'}),
        dbc.Row(html.Div(id=id('graphs')), className="mb-4"),

            # dbc.Col(dbc.Card(card_content('Data Frequency', [
            #     html.Div(generate_dropdown(id('dropdown_data_frequency'), option_date, placeholder='Select Unit of Time')),
            #     html.Div(bar_graph(id('bar_graph_data_frequency'), 'stack', showlegend=False)),
            # ]), color="primary", inverse=True)),

            # dbc.Col(dbc.Card(card_content('Frequency Distribution', [
            #     html.Div(generate_dropdown(id('dropdown_frequency_distribution'), option_date, placeholder='Select Column')),
            #     html.Div(bar_graph(id('bar_graph_data_frequency'), 'stack', orientation='h', showlegend=False)),
            # ]), color="secondary", inverse=True)),

            # dbc.Col(dbc.Card(card_content('Seasonality', [
            #     html.Div(generate_dropdown(id('dropdown_frequency_distribution'), option_date, placeholder='Select Column')),
            #     # html.Div(bar_graph(id('bar_graph_data_frequency'), 'stack', orientation='h', showlegend=False)),
            # ]), color="info", inverse=True)),

        

    ], fluid=True),
    
])


# @app.callback(Output(id('bar_graph_invalid'), 'figure'), Input('input_data_store', 'data'), Input('url', 'pathname'))
# def generate_bar_graph(data, pathname):
#     df = json_normalize(data)
    
#     # stack_types = ['Valid', 'Missing', 'Invalid']
#     stack_types = ['Valid', 'Missing']
#     num_col = len(df.columns)
#     valid_list = list(df.count().to_dict().values())
#     null_list = list(df.isna().sum().to_dict().values())
#     # invalid_list = []

#     graph_df = pd.DataFrame({
#         'Column': list(df.columns) * len(stack_types),
#         'Number of Rows': valid_list + null_list,
#         'Data': [j for i in stack_types for j in (i,)*num_col]
#     })

#     fig = px.bar(graph_df, x="Column", y="Number of Rows", color="Data", barmode='stack')

#     return fig

@app.callback(Output(id('graphs'), 'figure'),
                Input('url', 'pathname'))
def generate_graphs(pathname):
    graph_id = get_session('graph_id')
    
    return graph_id

