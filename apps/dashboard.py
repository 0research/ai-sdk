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


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('dashboard')



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
        dbc.Row(dbc.Col(html.H1('Dashboard')), style={'text-align':'center'}),
        dbc.Row(html.Div(id=id('graphs')), className="mb-4"),

        html.Div(id=id('content'), style={'height':'290px'})

    ], fluid=True),
    
])


# def bar_graph(component_id, barmode, x=None, y=None, data=None, orientation='v', showlegend=True):
#     colors = {
#         'background': '#111111',
#         'text': '#7FDBFF'
#     }

#     if x == None: x='Fruit'
#     if y == None: y='Amount'
#     if data == None:
#         data = pd.DataFrame({
#             "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
#             "Amount": [4, 1, 2, 2, 4, 5],
#             "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
#         })

#     fig = px.bar(data, x=x, y=y, color="City", barmode=barmode, orientation=orientation)

#     fig.update_layout(
#         plot_bgcolor=colors['background'],
#         paper_bgcolor=colors['background'],
#         font_color=colors['text'],
#         showlegend=showlegend
#     )

#     return dcc.Graph(
#         id=component_id,
#         figure=fig
#     ),


# @app.callback(
#     Output(id('content'), 'children'),
#     Input('url', 'pathname'),
# )
# def generate_graphs(pathname):
#     project_id = get_session('project_id')
#     project = get_document('project', project_id)
#     content = []
    
#     for node_id in project['graph_dict'].keys():
#         for graph_id in project['graph_dict'][node_id]:
#             graph = get_document('graph', graph_id)

#             if graph['type'] == 'line': fig = get_line_figure(node_id, graph['x'], graph['y'])
#             elif graph['type'] == 'bar': fig = get_bar_figure(node_id, graph['x'], graph['y'], graph['barmode'])
#             elif graph['type'] == 'pie': fig = get_pie_figure(node_id, graph['names'], graph['values'])
#             elif graph['type'] == 'scatter': fig = get_scatter_figure(node_id, graph['x'], graph['y'], graph['color'])

#             content += [
#                 dbc.Col([
#                     dbc.Card([
#                         dbc.Button(dbc.CardHeader(graph['name']), id={'type': id('button_graph_id'), 'index': graph_id}, href='/apps/plot_graph/', value=graph_id),
#                         dbc.CardBody([
#                             dcc.Graph(figure=fig, style={'height':'270px'}),
#                         ]),
#                     ], color='primary', inverse=True, style={})
#                 ], style={'width':'32%', 'display':'inline-block', 'text-align':'center', 'margin':'3px 3px 3px 3px'})
#             ]
#     return content


@app.callback(
    Output(id('content'), 'children'),
    Input('url', 'pathname'),
)
def generate_all_graphs(active_tab):
    project_id = get_session('project_id')
    project = get_document('project', project_id)
    content = []

    for dataset_id, graph_id_list in project['graph_dict'].items():
        dataset = get_document('dataset', dataset_id)
        labels = {feature_id:feature['name'] for feature_id, feature in dataset['features'].items()}

        for graph_id in graph_id_list:
            graph = get_document('graph', graph_id)
            df = get_dataset_data(dataset_id)

            if graph['type'] == 'line': fig = get_line_figure(df, graph['x'], graph['y'], labels)
            # elif graph['type'] == 'bar': fig = get_bar_figure(df, graph['x'], graph['y'], graph['barmode'], labels)
            # elif graph['type'] == 'pie': fig = get_pie_figure(df, graph['names'], graph['values'], labels)
            # elif graph['type'] == 'scatter': fig = get_scatter_figure(df, graph['x'], graph['y'], graph['color'], labels)

            content += [
                dbc.Col([
                    dbc.Card([
                        dbc.Button(dbc.CardHeader(graph['name']), id={'type': id('button_graph_id'), 'index': graph_id}, href='/apps/data_flow/', value=graph_id),
                        dbc.CardBody([
                            dcc.Graph(figure=fig, style={'height':'270px'}),
                        ]),
                    ], color='primary', inverse=True, style={})
                ], style={'width':'32%', 'display':'inline-block', 'text-align':'center', 'margin':'3px 3px 3px 3px'})
            ]
        
    return content


# @app.callback(
#     Output('url', 'pathname'),
#     Input({'type': id('button_graph'), 'index': ALL}, 'n_clicks')
# )
# def save_graph_id_session(n_clicks):
#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
#     if triggered == '': return no_update
#     if len(callback_context.triggered) != 1: return no_update

#     print("Store graph_id: ", json.loads(triggered)['index'])
#     store_session('graph_id', json.loads(triggered)['index'])

#     return '/apps/plot_graph/'

# Button Chart for specific ID
@app.callback(
    Output({'type': id('button_graph_id'), 'index': MATCH}, 'n_clicks'),
    Input({'type': id('button_graph_id'), 'index': MATCH}, 'n_clicks'),
    State({'type': id('button_graph_id'), 'index': MATCH}, 'value')
)
def load_graph(n_clicks, graph_id):
    store_session('graph_id', graph_id)
    return no_update