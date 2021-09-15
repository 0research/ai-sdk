import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
import pandas as pd
import json
from pprint import pprint




# Layout
layout = html.Div([
    html.H1('Git Graph', style={"textAlign": "center"}),
    html.Div(id='jsonEditorDiv', children=[

    ])
])
