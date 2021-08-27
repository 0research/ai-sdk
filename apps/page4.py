import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
import collections
import typesense
from pprint import pprint
import json
import dash_core_components as dcc
import dash_html_components as html


# client = typesense.Client({
#   'nodes': [{
#     'host': 'localhost', # For Typesense Cloud use xxx.a1.typesense.net
#     'port': '8108',      # For Typesense Cloud use 443
#     'protocol': 'http'   # For Typesense Cloud use https
#   }],
#   'api_key': 'Hu52dwsas2AdxdE',
#   'connection_timeout_seconds': 2
# })

# TODO check if has container
# client.collections['container'].delete()
# container_schema = {
#   'name': 'container',
#   'fields': [
#     {'name': 'date', 'type': 'string' },
#     {'name': 'type', 'type': 'string', },
#     {'name': 'actual', 'type': 'bool' },
#     {'name': 'status', 'type': 'string' },
#     {'name': 'vessel', 'type': 'int32' },
#     {'name': 'voyage', 'type': 'string' },
#     {'name': 'location', 'type': 'int32' },
#     {'name': 'description', 'type': 'string' }
#   ]
# }
# client.collections.create(container_schema)


# with open('tmp/TRIU8780930.json') as f:
#   containerEvents = json.load(f)
#   for c in containerEvents:
#     if c['vessel'] == None: c['vessel'] = -1
#     if c['voyage'] == None: c['voyage'] = ''
#     # container_document = json.loads(json_line)
#     client.collections['container'].documents.create(c)


# search_parameters = {
#   'q'         : 'sea',
#   'query_by'  : 'type',
# }

# a = client.collections['container'].documents.search(search_parameters)
# pprint(a)


# Layout
layout = html.Div([
    html.H1('Page', style={"textAlign": "center"}),
    dcc.Input(id='input1', type='text'),
    html.Div(id='output1'),
    html.Button(id='button1', value='Submit')
])


# @app.callback(
#     Output("output1", "children"),
#     [Input('input1', 'value')],
# )
# def cb_render(input1):
#     return html.P(input1)