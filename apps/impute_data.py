from dash import html
from dash import dcc
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
import base64
from io import BytesIO
from apps.typesense_client import *
# from missingpy import MissForest, KNNImputer


id = id_factory('impute_data')


def get_col_dtype(col):
    import arrow

    if col.dtype == "string":
        try:
            col_new = pd.to_datetime(col.dropna().unique())
            return col_new.dtype
        except:
            pass
    else:
        return col.dtype


option_action = [
    {'label': 'Remove NaN', 'value': 'removeNAN'},
    {'label': 'Replace NAN with Value', 'value': 'replaceNANwithValue'},
    {'label': 'MissForest', 'value': 'missForest'},
    {'label': 'KNNImputer', 'value': 'KNNImputer'}
]
option_graph = [
    {'label': 'Pie Plot', 'value': 'pie'},
    {'label': 'Line Plot', 'value': 'line'},
    # {'label': 'Bar Plot', 'value': 'bar'},
    # {'label': 'Scatter Plot', 'value': 'scatter'},
    # {'label': 'Box Plot', 'value': 'box'}
]


# Layout
layout = html.Div([
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    dcc.Store(id=id('selection_list_store'), storage_type='session'),

    dbc.Container([
        dbc.Row([dbc.Col(html.H2('Impute Data'), width=12)], className='text-center', style={'margin': '3px'}),
        
        # Select Column(Left Panel) and Column Data(Right Panel)
        dbc.Row([
            dbc.Col(html.Div([
                html.H5('Step 1: Select a Column to modify'),
                dcc.Graph(id=id('left_panel_graph')),
            ]), width=6),
            
            dbc.Col(html.Div([
                html.H5('Step 2: Visualize Missing and Invalid Data'),
                dcc.Graph(id=id('right_panel_graph'))
            ]), width=6),
        ], className='text-center', style={'margin': '3px'}),

        # Selected Column
        dbc.Row([
            dbc.Col(html.H6('Column Selected: None', id=id('selection_list')), width=12),
        ], className='text-center', style={'margin': '3px','background-color':'silver'}),

        # Data Cleaning Action
        dbc.Row([
            dbc.Col(html.H5('Step 3: Select Data Cleaning Action'), width=12),
            dbc.Col(html.Div([
                html.H6('Select Graph'),
                html.H6('Perform Action'),
            ]), width=3),
            dbc.Col(html.Div([
                generate_dropdown(id('dropdown_select_graph'), option_graph, value=option_graph[0]['value']),
                generate_dropdown(id('dropdown_select_action'), option_action, value=option_action[0]['value']),
            ]), width=9),
            dbc.Col(dbc.Button('Add Impute', id=id('button_add_impute'), style={'width':'100%'}, className='btn btn-success'), width={'size':10, 'offset':1}),

            dbc.Col(html.Div(dcc.Graph(id=id('selected_column_graph'))), width=6),
            dbc.Col(html.Div(dcc.Graph(id=id('impute_col_graph'))), width=6),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

        dbc.Row([
            dbc.Col([
                html.H6('Changes (TODO)', style={'text-align':'center'}),
            ], id=id('changes'), width=12, style={'min-height':'200px', 'background-color':'silver'}),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
        
        dbc.Row([
            dbc.Col(dbc.Button(html.H6('Confirm'), className='btn-primary', id=id('button_confirm'), href='/apps/data_lineage', style={'width':'100%'}), width={'size':10, 'offset':1}),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

        # dbc.Toast(
        #     id=id('toast_confirm'),
        #     header="Impute Data Success!",
        #     is_open=False,
        #     dismissable=True,
        #     icon="success",
        #     # top: 66 positions the toast below the navbar
        #     style={"position": "fixed", "top": 66, "right": 10, "width": 350},
        # ),
    ], style={'width':'100%', 'maxWidth':'100%'}),
])


# Left Bar Graph
@app.callback(Output(id('left_panel_graph'), 'figure'), 
                Input('url', 'pathname'),)
def generate_left_bar_graph(pathname):
    df = get_dataset_data(get_session('dataset_id'))
    
    # stack_types = ['Valid', 'Missing', 'Invalid'] # TODO add Invalid
    stack_types = ['Valid', 'Missing']
    num_col = len(df.columns)
    # invalid_list = []
    valid_list = list(df.count().to_dict().values())
    null_list = list(df.isna().sum().to_dict().values())
    
    graph_df = pd.DataFrame({
        'column': list(df.columns) * len(stack_types),
        'Freq': valid_list + null_list,
        'type': [j for i in stack_types for j in (i,)*num_col]
    })

    fig = px.bar(graph_df, x="Freq", y="column", color="type", orientation='h', barmode='stack', height=650)

    return fig


# Save & Display selected Column
@app.callback(Output(id('selection_list_store'), 'data'), Input(id('left_panel_graph'), 'clickData'))
def save_selected_column(selected_columns):
    if selected_columns == None: return None
    return selected_columns['points'][0]['label']
@app.callback(Output(id('selection_list'), 'children'), Input(id('selection_list_store'), 'data'))
def generate_selected_column(selected_columns):
    if selected_columns is None or selected_columns == []: return 'Column Selected: None'
    return 'Column Selected: ', selected_columns


# Right Bar Graph
@app.callback(Output(id('right_panel_graph'), 'figure'), 
                Input(id('selection_list_store'), 'data'))
def generate_right_bar_graph(selected_column):
    if selected_column == None or selected_column == []: return no_update
    
    df = get_dataset_data(get_session('dataset_id'))
    data = df[selected_column].value_counts(dropna=False)

    # TODO add invalid as diff colored bars
    colors = ['Valid',] * len(data)
    if len(colors) > 2:
        colors[1] = 'Invalid'
        # colors[2] = 'Missing'

    graph_df = pd.DataFrame({
        'Freq': list(data.values),
        'Unique Values': list(data.index),
        'type': colors
    })

    fig = px.bar(graph_df, x="Freq", y="Unique Values", color='type', orientation='h', barmode='stack', height=650)

    return fig


def impute_col(df, action, fillna=0):
    if action == 'removeNAN':
        df.dropna(inplace=True)
    elif action == 'replaceNANwithValue':
        df.fillna(fillna, inplace=True)
    # elif action == 'missForest':
    #     imputer = MissForest()
    #     df = imputer.fit_transform(df)
    # elif action == 'KNNImputer':
    #     imputer = KNNImputer()
    #     df = imputer.fit_transform(df)
    return df


@app.callback(Output(id('selected_column_graph'), 'figure'), 
                Output(id('impute_col_graph'), 'figure'),
                Input(id('selection_list_store'), 'data'), 
                Input(id('dropdown_select_graph'), 'value'),  
                Input(id('dropdown_select_action'), 'value'))
def generate_select_graph(selected_columns, selected_graph, action):
    if selected_columns == None or selected_columns == []: return no_update
    
    # Get Data
    df = get_dataset_data(get_session('dataset_id'))
    col = df[selected_columns]
    col_clean = impute_col(col, action)

    if selected_graph == 'pie':
        df_value_counts = col.value_counts(dropna=False).reset_index().rename(columns={'index':'Unique Value', selected_columns: 'Freq'})
        figure = px.pie(df_value_counts, values='Freq', names='Unique Value')
        
        df_value_counts = col_clean.value_counts(dropna=False).reset_index().rename(columns={'index':'Unique Value', selected_columns: 'Freq'})
        figure2 = px.pie(df_value_counts, values='Freq', names='Unique Value')

    elif selected_graph == 'line':
        df_clean = impute_col(df, action)
        figure = px.line(df, x="index", y=selected_columns)
        figure2 = px.line(df_clean, x="index", y=selected_columns)
    # elif selected_graph == 'bar':
    #     figure = px.bar(df_value_counts, x=columns[0], y=columns[1], barmode='stack')
    #     figure2 = px.bar(impute_col(df_value_counts, action), x=columns[0],  y=columns[1], barmode='stack')
    # elif selected_graph == 'scatter':
    #     figure = px.scatter(df_value_counts, x=columns[0], y=columns[1])
    #     figure2 = px.scatter(impute_col(df_value_counts, action), x=columns[0], y=columns[1])
    # elif selected_graph == 'box':
    #     figure = px.box(df_value_counts, x=columns[0], y=columns[1])
    #     figure2 = px.scatter(impute_col(df_value_counts, action), x=columns[0], y=columns[1])


    # # Upload temporary output data
    # jsonl = col_clean.to_json(orient='records', lines=True) # Convert to jsonl
    # try:
    #     client.collections['out'].delete()
    #     client.collections.create(generate_schema_auto('out'))
    # except Exception as e:
    #     client.collections.create(generate_schema_auto('out'))
    # client.collections['out'].documents.import_(jsonl, {'action': 'create'})

    return figure, figure2,



# Add Impute to List of Changes
@app.callback(Output(id('changes'), 'children'),
                Input(id('button_add_impute'), 'n_clicks'),
                State(id('selection_list_store'), 'data'),
                State(id('dropdown_select_action'), 'value'),)
def button_add_impute(n_clicks, column, impute_action):
    if n_clicks is None: return no_update
    print('BUTTON IMPUTE')
    print(column)
    print(impute_action)
    return no_update


# Button Confirm
@app.callback(Output('modal', 'children'),
                Input(id('button_confirm'), 'n_clicks'),
                State('current_dataset', 'data'),
                State('current_node', 'data'),
                State(id('selection_list_store'), 'data'), 
                State(id('dropdown_select_action'), 'value'))
def button_confirm(n_clicks, dataset_id, node_id, selected_column, action):
    if n_clicks is None: return no_update
    print('Source: ', node_id)
    df = get_dataset_data(node_id)
    df[selected_column] = impute_col(df[selected_column], action)
    action(dataset_id, node_id, df.to_dict('records'), label='')

    return no_update

