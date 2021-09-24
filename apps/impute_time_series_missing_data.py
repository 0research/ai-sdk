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
from apps.graph import *
import plotly.graph_objects as go
import pandas as pd
from pandas.io.json import json_normalize

id = id_factory('impute_time_series_missing_data')


def generate_dropdown(component_id, options):
    return dcc.Dropdown(
        id=component_id,
        options=options,
        value=options[0]['value'],
        searchable=False
    )


option_action = [
    {'label': 'Remove NaN', 'value': 'removeNAN'},
    {'label': 'SimpleImputer', 'value': 'simpleImputer'},
    {'label': 'Moving Average', 'value': 'movingAverage'},
    {'label': 'Exponential Moving Average', 'value': 'exponentialMovingAverage'}]

option_graph = [
    {'label': 'Pie Plot', 'value': 'pie'},
    {'label': 'Bar Plot', 'value': 'bar'},
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
        # Datatable & Selected Rows/Json List
        dbc.Row([
            dbc.Col(html.H5('Step 1: Ensure the columns have the correct selected datatype'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),            
        ], className='text-center', style={'margin': '5px'}),

        dbc.Row([
            dbc.Col(html.H5('Step 2: Select a Column/Bar to modify'), width=12),
            dbc.Col(bar_graph(id('bar_valid_invalid_missing'), 'stack'), width=12),
        ], className='text-center', style={'margin': '5px'}),

        dbc.Row([
            dbc.Col(html.H5('Step 3: Select Data Cleaning Action'), width=12),
            dbc.Col(html.H6('Column Selected: None', id=id('selection_list')), width=12),
            dbc.Col(html.Div([
                html.H6('Select Graph'),
                html.H6('Perform Action'),
            ]), width=3),
            dbc.Col(html.Div([
                generate_dropdown(id('dropdown_select_graph'), option_graph),
                generate_dropdown(id('dropdown_select_action'), option_action),
            ]), width=9),
            dbc.Col(html.Div(dcc.Graph(id=id('selected_column_graph'))), width=6),
            dbc.Col(html.Div(dcc.Graph(id=id('perform_action_graph'))), width=6),
            dbc.Col(html.Button('Confirm', className='btn-secondary', id=id('button_confirm'), style={'width':'50%'}), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        
    ], style={'width':'100%', 'maxWidth':'100%'}),
])

# Update datatable when files upload
@app.callback([Output(id('input_datatable'), "data"), Output(id('input_datatable'), 'columns')], 
                Input('input_data_store', "data"), Input('url', 'pathname'))
def update_data_table(input_data, pathname):
    if input_data == None: return [], []
        
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


@app.callback(Output(id('selection_list_store'), 'data'), Input(id('bar_valid_invalid_missing'), 'clickData'))
def save_selected_column(selected_columns):
    if selected_columns == None: return None
    return selected_columns['points'][0]['label']

@app.callback(Output(id('selection_list'), 'children'), Input(id('selection_list_store'), 'data'))
def generate_selected_column(selected_columns):
    if selected_columns is None or selected_columns == []: return 'Column Selected: None'
    return 'Column Selected: ', selected_columns


@app.callback(Output(id('bar_valid_invalid_missing'), 'figure'), Input(id('input_datatable'), 'data'))
def generate_bar_graph(data):
    df = pd.DataFrame(data)

    graph_df = pd.DataFrame({
        'Column': list(df.columns) + list(df.columns),
        'Number of Rows': list(df.count().to_dict().values()) + list(df.isna().sum().to_dict().values()),
        'Data': ['Valid'] * len(df.columns) + ['Missing'] * len(df.columns) 
    })

    fig = px.bar(graph_df, x="Column", y="Number of Rows", color="Data", barmode='stack')

    return fig


def perform_action(df, action):
    if action == 'removeNAN':
        df = df.dropna()
    elif action == 'simpleImputer':
        pass
    elif action == 'movingAverage':
        pass
    elif action == 'exponentialMovingAverage':
        pass
    
    return df.reset_index()



option_action = [
    {'label': 'Remove NaN', 'value': 'removeNAN'},
    {'label': 'SimpleImputer', 'value': 'simpleImputer'},
    {'label': 'Moving Average', 'value': 'movingAverage'},
    {'label': 'Exponential Moving Average', 'value': 'exponentialMovingAverage'}]


@app.callback([Output(id('selected_column_graph'), 'figure'), Output(id('perform_action_graph'), 'figure')],
            [Input(id('selection_list_store'), 'data'),
            Input(id('dropdown_select_graph'), 'value'),  
            Input(id('dropdown_select_action'), 'value'), 
            State(id('input_datatable'), 'data')])
def generate_select_graph(selected_columns, selected_graph, action, data):
    if selected_columns == None: return no_update
    
    columns = ['unique_values', 'count']
    df = pd.DataFrame(data)
    df_col = df[selected_columns].squeeze()
    df_value_counts = df_col.value_counts().to_frame().reset_index()
    df_value_counts.columns = columns
    df_value_counts.loc[len(df_value_counts)] = [None, df_col.isnull().sum()]
    df_value_counts.astype({columns[0]: str, columns[1]: int})

    pprint(df_value_counts)

    if selected_graph == 'pie':
        figure = px.pie(df_value_counts, values=columns[1], names=columns[0])
        figure2 = px.pie(perform_action(df_value_counts, action), values=columns[1], names=columns[0])
    elif selected_graph == 'bar':
        figure = px.bar(df_value_counts, x=columns[0], y=columns[1], barmode='stack')
        figure2 = px.bar(perform_action(df_value_counts, action), x=columns[0], y=columns[1], barmode='stack')
    elif selected_graph == 'scatter':
        figure = px.scatter(df_value_counts, x=columns[0], y=columns[1])
        figure2 = px.scatter(perform_action(df_value_counts, action), x=columns[0], y=columns[1])
    elif selected_graph == 'box':
        figure = px.box(df_value_counts, x=columns[0], y=columns[1])
        figure2 = px.scatter(perform_action(df_value_counts, action), x=columns[0], y=columns[1])

    return figure, figure2