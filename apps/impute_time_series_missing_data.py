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
from wordcloud import WordCloud
import base64
from io import BytesIO

id = id_factory('impute_time_series_missing_data')


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
    dcc.Store(id='input_datatype_store', storage_type='session'),
    dcc.Store(id=id('selection_list_store'), storage_type='session'),
    dcc.Store(id=id('merge_strategy_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),

    dbc.Container([
        # Datatable & Selected Rows/Json List
        dbc.Row([
            dbc.Col(html.H5('Step 1: Ensure the columns have the correct selected datatype'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable'))), width=12),            
        ], className='text-center', style={'margin': '3px'}),

        dbc.Row([
            dbc.Col(html.H5('Step 2: Select a Column/Bar to modify'), width=12),
            dbc.Col(bar_graph(id('bar_graph'), 'stack'), width=12),
            dbc.Col(html.H6('Column Selected: None', id=id('selection_list')), width=12),
        ], className='text-center', style={'margin': '3px'}),

        dbc.Row([
            dbc.Col(html.H5('Step 3: Visualize Data'), width=12),
            dbc.Col(html.Div('Invalid Data Stats (Total, unique)'), width=12),
            # dbc.Col(html.Div(id=id('wordcloud')), width=6),
            dbc.Col(bar_graph(id('bar_graph_invalid'), 'stack', orientation='h'), width=12),
        ], className='text-center', style={'margin': '3px'}),

        dbc.Row([
            dbc.Col(html.H5('Step 4: Select Data Cleaning Action'), width=12),
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
        14
    ], style={'width':'100%', 'maxWidth':'100%'}),
])

# Update datatable when files upload
@app.callback([Output(id('input_datatable'), "data"), Output(id('input_datatable'), 'columns'), Output(id('input_datatable'), 'dropdown_data')], 
                Input('input_data_store', "data"), Input('input_datatype_store', 'data'), Input('url', 'pathname'))
def update_data_table(input_data, datatype, pathname):
    if input_data == None: return no_update, no_update, no_update
    
    # Convert data & Convert all values to string
    df = json_normalize(input_data)
    df.insert(0, column='index', value=range(1, len(df)+1))

    # for i in range(len(json_dict)):
    #     for key, val in json_dict[i].items():
    #         if type(json_dict[i][key]) == list:
    #             json_dict[i][key] = str(json_dict[i][key])

    # Get Columns
    # columns = [{ "id": i, "name": i, "deletable": True, "selectable": True, 'presentation': 'dropdown'} for i in df.columns]
    columns = [{"id": i, "name": i, 'presentation': 'dropdown'} for i in df.columns]

    # Get best dtypes and insert to first row
    row_dropdown_dtype = pd.DataFrame(datatype, index=[0]).reset_index(drop=True)
    df = pd.concat([row_dropdown_dtype, df]).reset_index(drop=True)

    pprint(df)

    options_datatype = [{}]
    datatype_list = ['object', 'string', 'Int64', 'datetime64', 'boolean', 'category']
    for key in df.to_dict('records')[0].keys():
        options_datatype[0][key] = {}
        options_datatype[0][key]['options'] = [{'label': i, 'value': i} for i in datatype_list]

    return df.to_dict('records'), columns, options_datatype


@app.callback(Output(id('selection_list_store'), 'data'), Input(id('bar_graph'), 'clickData'))
def save_selected_column(selected_columns):
    if selected_columns == None: return None
    return selected_columns['points'][0]['label']

@app.callback(Output(id('selection_list'), 'children'), Input(id('selection_list_store'), 'data'))
def generate_selected_column(selected_columns):
    if selected_columns is None or selected_columns == []: return 'Column Selected: None'
    return 'Column Selected: ', selected_columns


@app.callback(Output(id('bar_graph'), 'figure'), Input(id('input_datatable'), 'data'))
def generate_bar_graph(data):
    df = pd.DataFrame(data).iloc[1:,:]
    
    # stack_types = ['Valid', 'Missing', 'Invalid']
    stack_types = ['Valid', 'Missing']
    num_col = len(df.columns)
    valid_list = list(df.count().to_dict().values())
    null_list = list(df.isna().sum().to_dict().values())
    # invalid_list = []

    graph_df = pd.DataFrame({
        'Column': list(df.columns) * len(stack_types),
        'Number of Rows': valid_list + null_list,
        'Data': [j for i in stack_types for j in (i,)*num_col]
    })

    fig = px.bar(graph_df, x="Column", y="Number of Rows", color="Data", barmode='stack')

    return fig


# @app.callback(Output(id('wordcloud'), 'children'), Input(id('selection_list_store'), 'data'))
# def generate_wordcloud(selected_columns):
#     di = {'abc':10, 'def': 20, 'ghi':2, 'jkl':55}
#     wc = WordCloud().generate_from_frequencies(frequencies=di)
#     wc_img = wc.to_image()
#     with BytesIO() as buffer:
#         wc_img.save(buffer, 'png')
#         img2 = base64.b64encode(buffer.getvalue()).decode()

#     return html.Img(src="data:image/png;base64," + img2)


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



@app.callback([Output(id('selected_column_graph'), 'figure'), Output(id('perform_action_graph'), 'figure')],
            [Input(id('selection_list_store'), 'data'),
            Input(id('dropdown_select_graph'), 'value'),  
            Input(id('dropdown_select_action'), 'value'), 
            State(id('input_datatable'), 'data')])
def generate_select_graph(selected_columns, selected_graph, action, data):
    if selected_columns == None: return no_update
    
    columns = ['unique_values', 'count']
    df = pd.DataFrame(data).iloc[1:,:]
    df_col = df[selected_columns].squeeze()
    df_value_counts = df_col.value_counts().to_frame().reset_index()
    df_value_counts.columns = columns
    df_value_counts.loc[len(df_value_counts)] = [None, df_col.isnull().sum()]
    df_value_counts.astype({columns[0]: str, columns[1]: int})

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