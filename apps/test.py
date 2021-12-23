from typing_extensions import ParamSpecArgs

from requests.models import ContentDecodingError
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
    dbc.Input(children=['TEXT'], id='test_edit'),
    html.P(children=['AAAA'], id='test_edit2')
])

@app.callback(
    Output('test_edit2', 'children'),
    Input('test_edit', 'value'),
)
def callback(value):
    print("INSIDE")
    return value
