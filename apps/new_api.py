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
import dash_uploader as du



def get_upload_component(id):
    return du.Upload(
        id=id,
        max_file_size=1,  # 1 Mb
        filetypes=['csv', 'json', 'jsonl'],
        upload_id=uuid.uuid1(),  # Unique session id
        max_files=100,
        default_style={'height':'150px'},
    )


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Initialize Variables
id = id_factory('new_api')



# Layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            # Left Panel
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('API Catalog')),
                    dbc.CardBody(generate_datatable(id('datatable'), height='800px')),
                ])
            ], width=6),

            # Right Panel
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6('View')),
                    dbc.CardBody([], id=id('right_panel'), style={'height':'800px'}),
                ]),
            ], width=6),
        ], className='bg-white text-dark text-center'),

        
    ], fluid=True),
])
