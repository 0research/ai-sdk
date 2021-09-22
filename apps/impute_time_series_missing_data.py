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
import plotly.graph_objects as go
import pandas as pd
from pandas.io.json import json_normalize

id = id_factory('impute_time_series_missing_data')

def bar_graph(component_id, barmode, x='Fruit', y='Amount', data=None):
    colors = {
        'background': '#111111',
        'text': '#7FDBFF'
    }

    if data == None:
        data = pd.DataFrame({
            "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
            "Amount": [4, 1, 2, 2, 4, 5],
            "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
        })

    fig = px.bar(data, x=x, y=y, color="City", barmode=barmode)

    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    return dcc.Graph(
        id=component_id,
        figure=fig
    ),

def generate_dropdown(component_id, options):
    return dcc.Dropdown(
        id=component_id,
        options=options,
        value=options[0]['value']
    )


option_action = [
    {'label': 'Remove NaN', 'value': 'removeNaN'},
    {'label': 'SimpleImputer', 'value': 'simpleImputer'},
    {'label': 'Moving Average', 'value': 'movingAverage'},
    {'label': 'Exponential Moving Average', 'value': 'exponentialMovingAverage'}]

option_graph = [
    {'label': 'Bar Plot', 'value': 'bar'},
    {'label': 'Pie Plot', 'value': 'pie'},
    {'label': 'Scatter Plot', 'value': 'scatter'},
    {'label': 'Box Plot', 'value': 'box'}]


# Layout
layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id=id('selection_list_store'), storage_type='session'),
    dcc.Store(id=id('merge_strategy_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),

    dbc.Container([
        # Page Title
        dbc.Row(dbc.Col(html.H2('Impute Time Series Missing Data')), style={'textAlign':'center'}),

        # Datatable & Selected Rows/Json List
        dbc.Row([
            dbc.Col(html.H5('Step 1: Select Column to Impute Data'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),            
        ], className='text-center', style={'margin': '5px'}),

        dbc.Row([
            dbc.Col(html.H5('Step 1: Observe Valid, Invalid and Missing data per column'), width=12),
            dbc.Col(bar_graph(id('bar_graph'), 'stack'), width=12),
        ], className='text-center', style={'margin': '5px'}),

        dbc.Row([
            dbc.Col(html.Div([
                html.H6('Column Selected: None', id=id('selection_list')),
                generate_dropdown(id('dropdown_select_graph'), option_graph),
                html.H6('<Graph>', id=id('selected_column_graph')),
            ]), width=6),

            dbc.Col(html.Div([
                html.H6('Perform Action'),
                html.Div(generate_dropdown(id('dropdown_select_action'), option_action)),
                html.H6('<Graph>', id=id('perform_action_graph')),
            ]), width=6),

            dbc.Col(html.Button('Confirm', className='btn-secondary', id=id('button_confirm'), style={'width':'50%'}), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        
    ], style={'width':'100%', 'maxWidth':'100%'}),
    
])

# Update datatable when files upload
@app.callback([Output(id('input_datatable'), "data"), Output(id('input_datatable'), 'columns')], 
                Input('input_data_store', "data"))
def update_data_table(input_data):
    if input_data == None: return [], []
    # for i in range(len(input_data)):
    #     input_data[i] = flatten(input_data[i])
        
    df = json_normalize(input_data)
    df.insert(0, column='index', value=range(1, len(df)+1))
    json_dict = df.to_dict('records')

    # Convert all values to string
    for i in range(len(json_dict)):
        for key, val in json_dict[i].items():
            if type(json_dict[i][key]) == list:
                json_dict[i][key] = str(json_dict[i][key])

    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    return json_dict, columns


@app.callback(Output(id('selection_list_store'), 'data'), Input(id('input_datatable'), 'selected_columns'))
def save_selected_column(selected_columns): 
    if selected_columns is None or len(selected_columns) < 1: return None
    return selected_columns

@app.callback(Output(id('selection_list'), 'children'), Input(id('selection_list_store'), 'data'))
def generate_selected_column(selected_columns):
    if selected_columns is None or len(selected_columns) < 1: return 'Column Selected: None'
    return 'Column Selected: ' , str(selected_columns[0])


@app.callback(Output(id('bar_graph'), 'figure'), [Input('input_data_store', 'data'), Input('input_datatable', 'selected_columns')])
def generate_bar_graph(input_data_store, _):
    df = json_normalize(input_data_store)

    graph_df = pd.DataFrame({
        'Column': list(df.columns) + list(df.columns),
        'Number of Rows': list(df.count().to_dict().values()) + list(df.isna().sum().to_dict().values()),
        'Data': ['Valid'] * len(df.columns) + ['Missing'] * len(df.columns) 
    })

    fig = px.bar(graph_df, x="Column", y="Number of Rows", color="Data", barmode='stack')

    return fig


@app.callback(Output(id('selected_column_graph'), 'children'), Input(id('dropdown_select_graph'), 'value'))
def generate_select_graph(graph):
    return graph