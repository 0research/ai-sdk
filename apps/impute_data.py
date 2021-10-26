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
from apps.graph import *
import plotly.graph_objects as go
import pandas as pd
import base64
from io import BytesIO
from apps.typesense_client import *
from missingpy import MissForest, KNNImputer


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
    dcc.Store(id='dataset_metadata', storage_type='session'),
    dcc.Store(id='dataset_profile', storage_type='session'),
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id='input_datatype_store', storage_type='session'),
    dcc.Store(id=id('selection_list_store'), storage_type='session'),
    dcc.Store(id=id('merge_strategy_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),

    dbc.Container([
        # # Datatable & Selected Rows/Json List
        # dbc.Row([
        #     dbc.Col(html.H5('Step 1: Ensure the columns have the correct selected datatype'), width=12),
        #     dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),            
        # ], className='text-center', style={'margin': '3px'}),
        
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
                generate_dropdown(id('dropdown_select_graph'), option_graph),
                generate_dropdown(id('dropdown_select_action'), option_action),
            ]), width=9),
            dbc.Col(html.Div(dcc.Graph(id=id('selected_column_graph'))), width=6),
            dbc.Col(html.Div(dcc.Graph(id=id('perform_action_graph'))), width=6),
            dbc.Col(html.Button('Confirm', className='btn-secondary', id=id('button_confirm'), style={'width':'50%'}), width=12),
            dbc.Toast(
                id=id('toast_confirm'),
                header="Impute Data Success!",
                is_open=False,
                dismissable=True,
                icon="success",
                # top: 66 positions the toast below the navbar
                style={"position": "fixed", "top": 66, "right": 10, "width": 350},
            ),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),
    ], style={'width':'100%', 'maxWidth':'100%'}),
])


# Left Bar Graph
@app.callback(Output(id('left_panel_graph'), 'figure'), 
                [Input('url', 'pathname'), 
                Input('dataset_metadata', 'data')])
def generate_left_bar_graph(pathname, settings):
    if settings is None or settings['name'] is None: return no_update
    
    result = get_documents(settings['name'], 250)
    df = json_normalize(result)
    
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
                [Input(id('selection_list_store'), 'data'),
                State('dataset_metadata', 'data')])
def generate_right_bar_graph(selected_column, settings):
    if settings is None or settings['name'] is None: return no_update
    if selected_column == None: return no_update
    
    result = get_documents(settings['name'], 250)
    data = json_normalize(result)[selected_column].value_counts(dropna=False)

    # TODO add invalid as diff colored bars
    colors = ['Valid',] * len(data)
    colors[1] = 'Invalid'
    colors[2] = 'Missing'

    graph_df = pd.DataFrame({
        'Freq': list(data.values),
        'Unique Values': list(data.index),
        'type': colors
    })

    fig = px.bar(graph_df, x="Freq", y="Unique Values", color='type', orientation='h', barmode='stack', height=650)

    return fig


def perform_action(df, action, fillna=0):
    if action == 'removeNAN':
        df.dropna(inplace=True)
    elif action == 'replaceNANwithValue':
        df.fillna(fillna, inplace=True)
    elif action == 'missForest':
        imputer = MissForest()
        df = imputer.fit_transform(df)
    elif action == 'KNNImputer':
        imputer = KNNImputer()
        df = imputer.fit_transform(df)
    return df



@app.callback([Output(id('selected_column_graph'), 'figure'), 
                Output(id('perform_action_graph'), 'figure')],
                [Input(id('selection_list_store'), 'data'),
                Input(id('dropdown_select_graph'), 'value'),  
                Input(id('dropdown_select_action'), 'value'),
                State('dataset_metadata', 'data')])
def generate_select_graph(selected_columns, selected_graph, action, settings):
    if selected_columns == None: return no_update
    if settings is None or settings['name'] is None: return no_update

    # Get Data
    result = get_documents(settings['name'], 250)
    df = json_normalize(result)
    df.insert(0, column='index', value=range(1, len(df)+1))

    # Get Frequency for each Unique Value
    df_value_counts = df[selected_columns].value_counts(dropna=False).reset_index()
    df_value_counts.rename(columns={'index':'Unique Value', selected_columns: 'Freq'}, inplace=True)

    # print(df_value_counts)
    # print(action)
    # print(perform_action(df_value_counts, action))

    if selected_graph == 'pie':
        figure = px.pie(df_value_counts, values='Freq', names='Unique Value')
        figure2 = px.pie(perform_action(df_value_counts, action), values='Freq', names='Unique Value')
    if selected_graph == 'line':
        figure = px.line(df, x="index", y=selected_columns)
        figure2 = px.line(perform_action(df, action), x="index", y=selected_columns)
    # elif selected_graph == 'bar':
    #     figure = px.bar(df_value_counts, x=columns[0], y=columns[1], barmode='stack')
    #     figure2 = px.bar(perform_action(df_value_counts, action), x=columns[0], y=columns[1], barmode='stack')
    # elif selected_graph == 'scatter':
    #     figure = px.scatter(df_value_counts, x=columns[0], y=columns[1])
    #     figure2 = px.scatter(perform_action(df_value_counts, action), x=columns[0], y=columns[1])
    # elif selected_graph == 'box':
    #     figure = px.box(df_value_counts, x=columns[0], y=columns[1])
    #     figure2 = px.scatter(perform_action(df_value_counts, action), x=columns[0], y=columns[1])

    return figure, figure2




@app.callback(Output(id('toast_confirm'), "is_open"),
                [Input(id('button_confirm'), 'n_clicks'),
                State(id('selection_list_store'), 'data'),
                State(id('dropdown_select_action'), 'value'),
                State('dataset_metadata', 'data')])
def confirm_action(n_clicks, selected_columns, action, settings):
    if n_clicks is None: return no_update
    if selected_columns == None: return no_update
    if settings is None or settings['name'] is None: return no_update

    # Get Data
    result = get_documents(settings['name'], 250)
    df = json_normalize(result)
    df[selected_columns] = perform_action(df[selected_columns], action)
    
    # Delete Collection & Upload TODO fix error
    jsonl = df.to_json(orient='records', lines=True)
    client.collections[settings['name']].delete()
    client.collections[settings['name']].documents.import_(jsonl, {'action': 'create'})

    return True













# # Update datatable when files upload
# @app.callback([Output(id('input_datatable'), "data"), 
#                 Output(id('input_datatable'), 'columns'), 
#                 Output(id('input_datatable'), 'dropdown_data')], 
#                 Input('dataset_metadata', "data"), 
#                 Input('dataset_profile', 'data'), 
#                 Input('url', 'pathname'))
# def update_data_table(setting, profile, pathname):
#     if setting == None: return no_update
#     if profile == None: return no_update
    
#     # Convert data & Convert all values to string
#     result = get_documents(setting['name'], 250)
#     df = json_normalize(result)
#     df.insert(0, column='index', value=range(1, len(df)+1))

#     # for i in range(len(json_dict)):
#     #     for key, val in json_dict[i].items():
#     #         if type(json_dict[i][key]) == list:
#     #             json_dict[i][key] = str(json_dict[i][key])

#     # Get best dtypes and insert to first row
#     datatype = [[i] for i in profile['datatype']]
#     row_dropdown_dtype = pd.DataFrame.from_dict(dict(zip(df.columns, datatype)))
#     df = pd.concat([row_dropdown_dtype, df]).reset_index(drop=True)

#     options_datatype = [{}]
#     datatype_list = ['object', 'string', 'Int64', 'datetime64', 'boolean', 'category']
#     for key in df.to_dict('records')[0].keys():
#         options_datatype[0][key] = {}
#         options_datatype[0][key]['options'] = [{'label': i, 'value': i} for i in datatype_list]

#     # Get Columns
#     # columns = [{ "id": i, "name": i, "deletable": True, "selectable": True, 'presentation': 'dropdown'} for i in df.columns]
#     columns = [{"id": i, "name": i, 'presentation': 'dropdown'} for i in df.columns]
#     print(df.to_dict('records'))
#     print(columns)
#     return df.to_dict('records'), columns, options_datatype