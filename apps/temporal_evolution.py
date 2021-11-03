from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State, ALL, MATCH
from app import app
import collections
import json
from pprint import pprint
from jsondiff import diff
from dash import no_update
from apps.util import *
from apps.typesense_client import *

id = id_factory('temporal_evolution')


# Layout
layout = html.Div([
    dcc.Store(id='current_dataset', storage_type='session'),
    dcc.Store(id='current_node', storage_type='session'),
    dcc.Store(id='dataset_metadata', storage_type='session'),
    dcc.Store(id=id('selection_list_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),
    dcc.Store(id=id('json_store_3'), storage_type='session'),
    dcc.Store(id=id('json_store_4'), storage_type='session'),
    dcc.Store(id=id('json_store_5'), storage_type='session'),

    dbc.Container([
        # Datatable & Selected Rows/Json List
        dbc.Row([
            dbc.Col(html.H5('Step 1: Select Rows to Merge'), width=12),
            dbc.Col(html.Div(generate_datatable(id('input_datatable')))),
            dbc.Col(html.H5('Selection: None', id=id('selection_list')), width=12),
            dbc.Col(html.Button('Clear Selection', className='btn-secondary', id=id('button_clear')), width=12),
        ], className='text-center bg-light', style={'padding':'3px', 'margin': '5px'}),

        # Json Data Headers
        dbc.Row([
            dbc.Col(html.H5('Step 2: Select Panel to display selection'), width=12),

            dbc.Col(html.Button('Original Data', className='btn-success btn-block', style={'font-size':'20px'}, id=id('button_json_1')), width=3),
            dbc.Col(html.Button('Original Data', className='btn-success btn-block', style={'font-size':'20px'}, id=id('button_json_2')), width=3),
            dbc.Col(html.Button('Difference', className='btn-danger btn-block', style={'font-size':'20px'}, id=id('button_json_3')), width=2),
            dbc.Col(html.Button('Difference', className='btn-danger btn-block', style={'font-size':'20px'}, id=id('button_json_4')), width=2),
            dbc.Col(html.Button('Difference', className='btn-danger btn-block', style={'font-size':'20px'}, id=id('button_json_5')), width=2),

            dbc.Col(html.Div(id=id('selected_list_1')), width=3),
            dbc.Col(html.Div(id=id('selected_list_2')), width=3),
            dbc.Col(html.Div(id=id('selected_list_3')), width=2),
            dbc.Col(html.Div(id=id('selected_list_4')), width=2),
            dbc.Col(html.Div(id=id('selected_list_5')), width=2),
            
            dbc.Col(html.Pre(id=id('json_1'), className='bg-success text-white', style={'text-align': 'left'}), width=3),
            dbc.Col(html.Pre(id=id('json_2'), className='bg-success text-white', style={'text-align': 'left'}), width=3),
            dbc.Col(html.Pre(id=id('json_3'), className='bg-danger text-white', style={'text-align': 'left'}), width=2),
            dbc.Col(html.Pre(id=id('json_4'), className='bg-danger text-white', style={'text-align': 'left'}), width=2),
            dbc.Col(html.Pre(id=id('json_5'), className='bg-danger text-white', style={'text-align': 'left'}), width=2),
        ], className='text-center bg-light'),
        
    ], style={'width':'100%', 'maxWidth':'100%'}),
    
])

# Update Datatable in "Review Data" Tab
@app.callback([Output(id('input_datatable'), "data"), 
                Output(id('input_datatable'), 'columns')], 
                Input('current_node', "data"))
def update_data_table(node_id):
    if node_id is None: return no_update
    
    df = get_node_data(node_id)
    df.insert(0, column='index', value=range(1, len(df)+1))
    json_dict = df.to_dict('records')

    columns = [{"name": i, "id": i, "deletable": True, "selectable": True} for i in df.columns]

    return json_dict, columns


# Store/Clear selected rows
@app.callback([Output(id('selection_list_store'), "data"), 
                Output(id('input_datatable'), "selected_rows")],
                [Input(id('input_datatable'), "selected_rows"), 
                Input(id('button_clear'), 'n_clicks')])
def save_table_data(selected_rows, n_clicks):
    triggered = callback_context.triggered[0]['prop_id']

    if triggered == id('input_datatable.selected_rows'):
        pass
    elif triggered == id('button_clear.n_clicks'):
        selected_rows = []

    return selected_rows, selected_rows


# Display selected rows/json
@app.callback(Output(id('selection_list'), "children"), Input(id('selection_list_store'), 'data'))
def generate_selected_list(selection_list):
    if selection_list == None: return None
    selection_list = list(map(lambda x:x+1, selection_list))
    return 'Selection: ', str(selection_list)[1:-1]



# Update Json Trees (Original)
for x in range(1, 3):
    @app.callback(Output(id('selected_list_'+str(x)), 'children'), 
                    [Input(id('button_json_')+str(x), 'n_clicks'), 
                    State(id('selection_list_store'), 'data')])
    def display_selected(n_clicks, selection_list):
        if selection_list is None: return no_update
        selection_list = list(map(lambda x:x+1, selection_list))[-1:]
        return 'You have Selected: ', str(selection_list)[1:-1]

    @app.callback(Output(id('json_store_')+str(x), 'data'), 
                [Input(id('button_json_')+str(x), 'n_clicks'),
                State(id('selection_list_store'), 'data'),
                State(id('input_datatable'), 'data')])
    def save_json(n_clicks, selected_list, data):
        if n_clicks is None: return no_update
        if selected_list is None or len(selected_list) == 0: return []
        
        index = selected_list[-1] + 1
        for d in data:
            if d['index'] == index:
                data = data
                break
        else:
            data = None

        return json.dumps(data, indent=2)

    @app.callback(Output(id('json_')+str(x), 'children'), Input(id('json_store_')+str(x), 'data'))
    def generate_json(json_tree):
        if json_tree == [] or json_tree is None: return []
        json_tree = json.loads(json_tree)
        return json.dumps(json_tree, indent=2)


# Update Json Trees (Difference)
for x in range(3, 6):
    @app.callback(Output(id('selected_list_'+str(x)), 'children'), 
                    Input(id('button_json_')+str(x), 'n_clicks'), 
                    State(id('selection_list_store'), 'data'))
    def display_selected(n_clicks, selection_list):
        if selection_list is None: return no_update
        selection_list = list(map(lambda x:x+1, selection_list))[-2:]
        return 'You have Selected: ', str(selection_list)[1:-1]

    @app.callback(Output(id('json_store_')+str(x), 'data'), 
                    Input(id('button_json_')+str(x), 'n_clicks'),
                    State(id('selection_list_store'), 'data'),
                    State(id('input_datatable'), 'data'))
    def save_json(n_clicks, selected_list, data):
        if n_clicks is None: return no_update
        if selected_list is None or len(selected_list) < 2: return []

        df = json_normalize(data)
        index1 = selected_list[-2] + 1
        index2 = selected_list[-1] + 1

        json1 = json.loads(df.set_index('index').loc[index1].to_json())
        json2 = json.loads(df.set_index('index').loc[index2].to_json())
        difference = diff(json1, json2, syntax='symmetric', marshal=True)

        return json.dumps(difference, indent=2)

    @app.callback(Output(id('json_')+str(x), 'children'), Input(id('json_store_')+str(x), 'data'))
    def generate_json(json_tree):
        if json_tree == [] or json_tree is None: return []
        json_tree = json.loads(json_tree)
        return json.dumps(json_tree, indent=2)