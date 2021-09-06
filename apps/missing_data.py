import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from app import app
import collections
import json
from pprint import pprint
from jsondiff import diff
from dash import no_update
from apps.util import *



# Layout
tab_labels = ['tab one', 'tab two', 'tab three']
tab_values = ['tab-' + str(i) for i in range(1, len(tab_labels)+1)]
layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    html.H1('Missing Data', style={"textAlign": "center"}),
    generate_upload('upload_json'),
    html.Div(id='topDiv2', style={'text-align': 'center'}, children=[
        dbc.ButtonGroup(id='select_list'),
        html.Div(id='selected_list'),
        html.Button('Clear Selected', id={'type': 'select_button', 'index': -1}),
    ]),
])

