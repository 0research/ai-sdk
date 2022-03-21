import pandas as pd
import dash_bootstrap_components as dbc
import json
from app import app
import dash_cytoscape as cyto
from dash import Dash, no_update, html, Input, Output, dash_table
from dash.exceptions import PreventUpdate
from dash_extensions import EventListener
from collections import OrderedDict
from apps.util import *

df = pd.DataFrame(OrderedDict([
    ('climate', ['Sunny', 'Snowy', 'Sunny', 'Rainy']),
    ('temperature', [13, 43, 50, 30]),
    ('city', ['NYC', 'Montreal', 'Miami', 'NYC'])
]))

layout = html.Div([
    dash_table.DataTable(
        id='table-dropdown',
        data=df.to_dict('records'),
        columns=[
            {'id': 'climate', 'name': 'climate', 'presentation': 'dropdown'},
            {'id': 'temperature', 'name': 'temperature'},
            {'id': 'city', 'name': 'city', 'presentation': 'dropdown'},
        ],
        editable=True,
                                        #list of dictionaries. One dict per row
        dropdown_data=[{                #their keys represent column IDs
            'climate': {                #their values are 'options' and 'clearable'
                'options': [            #'options' represent cell data
                    {'label': i, 'value': i}
                    for i in df['climate'].unique()
                ],

                'clearable':True
            },

            'city': {
                'options': [
                    {'label': i, 'value': i}
                    for i in df['city'].unique()
                ],

                'clearable':True
            },
        } for x in range(2)
        ],

    ),

    html.Div(generate_datatable('abc', height='400px')),
])



@app.callback(
    Output('abc', 'data'),
    Output('abc', 'columns'),
    Output('abc', 'dropdown_data'),
    Input('url', 'pathname'),
)
def generate_datatable_aggregate(_):
    node_id = get_session('node_id')
    df = get_dataset_data(node_id)
    columns = [{"name": i, "id": i, "deletable": False, "selectable": True, 'presentation': 'dropdown'} for i in df.columns]

    dropdown_data = [
        {                #their keys represent column IDs
            c['name']: {                #their values are 'options' and 'clearable'
                'options': [            #'options' represent cell data
                    {'label': 'one', 'value': 1},
                    {'label': 'two', 'value': 2},
                ],
            },
        } for c in columns
    ]

    return df.to_dict('records'), columns, dropdown_data