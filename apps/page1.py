import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
from app import app
import dash_table
from dash import no_update

import io
import base64
import datetime

import pandas as pd

layout = html.Div([
    html.H1('Page1', style={"textAlign": "center"}),

    html.Div([
        dcc.Upload(
            id='upload-file',
            children=html.Div([
                'Drag and Drop or ', html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=True
        )
    ], id='topDiv'),

    html.Div(id='topDiv2', style={'text-align': 'center'}),

    html.Div([
        html.H2('LeftDiv')
    ], id='leftDiv', style={'float': 'left', 'width': '50%', "textAlign": "center"}),

    html.Div([
        html.H2('RightDiv')
    ], id='rightDiv', style={'float': 'right', 'width': '50%', "textAlign": "center"})
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),
        html.P("Inset X axis data"),
        dcc.Dropdown(id='xaxis-data', options=[{'label': x, 'value': x} for x in df.columns], persistence=True),
        html.P("Inset Y axis data"),
        dcc.Dropdown(id='yaxis-data', options=[{'label': x, 'value': x} for x in df.columns], persistence=True),
        html.Button(id="submit-button", children="Create Graph"),
        html.Hr(),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=15
        ),
        dcc.Store(id='stored-data', data=df.to_dict('records')),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])


@app.callback([Output('topDiv2', 'children'),
               Output('leftDiv', 'children')],
              Input('upload-file', 'contents'),
              State('upload-file', 'filename'),
              State('upload-file', 'last_modified'))
def update_data_table(contents, filename, last_modified):
    if contents is None:
        return no_update
    children = [parse_contents(c, n, d) for c, n, d in zip(contents, filename, last_modified)]
    return html.Div([
        html.P('individual file info & metadata inputs'),
        html.P('missing data stats'),
        html.P('schema r/s discovery')
    ]), children


@app.callback(Output('rightDiv', 'children'),
              Input('submit-button','n_clicks'),
              State('stored-data','data'),
              State('xaxis-data','value'),
              State('yaxis-data', 'value'))
def update_graph(n, data, x_data, y_data):
    if n is None:
        return no_update
    else:
        bar_fig = px.bar(data, x=x_data, y=y_data)
        # print(data)
        return dcc.Graph(figure=bar_fig)
