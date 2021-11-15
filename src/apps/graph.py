import json
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
import os
import pandas as pd



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

