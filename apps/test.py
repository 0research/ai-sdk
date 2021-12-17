from typing_extensions import ParamSpecArgs
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
from jsonmerge import Merger, merge
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from pandas import json_normalize
from itertools import zip_longest
from datetime import datetime
import dash_cytoscape as cyto
from apps.typesense_client import *
import ast
from apps.constants import *



# Layout
layout = html.Div([
    dcc.Dropdown(options=[], value=None, id='dropdown'),
])


layout = html.Div([
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'a', 'value': 'a'},
            {'label': 'b', 'value': 'b'},
            {'label': 'c', 'value': 'c'},
        ],
        value='a'
    ),
    dcc.Input(id='input', value=''),
    html.Button('Add Option', id='submit'),
])

@app.callback(
    Output('dropdown', 'options'),
    [],
    [State('input', 'value'), State('dropdown', 'options')],
    [Input('submit', 'n_clicks')]
)
def callback(new_value, current_options, n_clicks):
    if not new_value:
        return current_options

    current_options.append({'label': new_value, 'value': new_value})
    return current_options
