import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State, ALL, MATCH
from app import app
import collections
import json
from pprint import pprint
from jsondiff import diff
from dash import no_update
from apps.util import *

id = id_factory('temporal_evolution')


# Layout
layout = html.Div([
    dcc.Store(id='input_data_store', storage_type='session'),
    dcc.Store(id=id('selection_list_store'), storage_type='session'),
    dcc.Store(id=id('json_store_1'), storage_type='session'),
    dcc.Store(id=id('json_store_2'), storage_type='session'),
    dcc.Store(id=id('json_store_3'), storage_type='session'),
    dcc.Store(id=id('json_store_4'), storage_type='session'),
    dcc.Store(id=id('json_store_5'), storage_type='session'),

    dbc.Container([
        # Upload Files
        # dbc.Row([
        #     dbc.Col(generate_upload('upload_json', "Drag and Drop or Click Here to Select Files"), className='text-center'),
        # ], className='text-center', style={'margin': '5px'}),

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
            
            dbc.Col(html.Pre(id=id('json_1'), className='text-left bg-success text-white'), width=3),
            dbc.Col(html.Pre(id=id('json_2'), className='text-left bg-success text-white'), width=3),
            dbc.Col(html.Pre(id=id('json_3'), className='text-left bg-danger text-white'), width=2),
            dbc.Col(html.Pre(id=id('json_4'), className='text-left bg-danger text-white'), width=2),
            dbc.Col(html.Pre(id=id('json_5'), className='text-left bg-danger text-white'), width=2),
        ], className='text-center bg-light'),
        
    ], style={'width':'100%', 'maxWidth':'100%'}),
    
])

# Update datatable when files upload
@app.callback([Output(id('input_datatable'), "data"), Output(id('input_datatable'), 'columns')], 
                Input('input_data_store', "data"), Input('url', 'pathname'))
def update_data_table(input_data, pathname):
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

# Store/Clear selected rows
@app.callback([Output(id('selection_list_store'), "data"), Output(id('input_datatable'), "selected_rows")],
            [Input(id('input_datatable'), "selected_rows"), Input(id('button_clear'), 'n_clicks')])
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
    selection_list = list(map(lambda x:x+1, selection_list))
    return 'Selection: ', str(selection_list)[1:-1]




# Update Json Trees (Original)
for x in range(1, 3):
    @app.callback(Output(id('selected_list_'+str(x)), 'children'), 
                [Input(id('button_json_')+str(x), 'n_clicks'), State(id('selection_list_store'), 'data')])
    def display_selected(n_clicks, selection_list):
        if selection_list is None: return no_update
        selection_list = list(map(lambda x:x+1, selection_list))[-1:]
        return 'You have Selected: ', str(selection_list)[1:-1]

    @app.callback(Output(id('json_store_')+str(x), 'data'), 
                [Input(id('button_json_')+str(x), 'n_clicks'),
                State(id('selection_list_store'), 'data'), State('input_data_store', 'data')])
    def save_json(n_clicks, selected_list, input_data):
        if selected_list is None or len(selected_list) == 0: return []
        if input_data is None or len(input_data) == 0: return []
        
        index = selected_list[-1]
        if 'raw_response' in input_data[index]:
            input_data[index]['raw_response'] = json.loads(input_data[index]['raw_response'])
        
        data = flatten(input_data[index])

        return json.dumps(data, indent=2)

    @app.callback(Output(id('json_')+str(x), 'children'), Input(id('json_store_')+str(x), 'data'))
    def generate_json(json_tree):
        if json_tree == [] or json_tree is None: return []
        json_tree = json.loads(json_tree)
        return json.dumps(json_tree, indent=2)


# Update Json Trees (Difference)
for x in range(3, 6):
    @app.callback(Output(id('selected_list_'+str(x)), 'children'), 
                [Input(id('button_json_')+str(x), 'n_clicks'), State(id('selection_list_store'), 'data')])
    def display_selected(n_clicks, selection_list):
        if selection_list is None: return no_update
        selection_list = list(map(lambda x:x+1, selection_list))[-2:]
        return 'You have Selected: ', str(selection_list)[1:-1]

    @app.callback(Output(id('json_store_')+str(x), 'data'), 
                [Input(id('button_json_')+str(x), 'n_clicks'),
                State(id('selection_list_store'), 'data'), State('input_data_store', 'data')])
    def save_json(n_clicks, selected_list, input_data):
        if selected_list is None or len(selected_list) < 2: return []
        if input_data is None or len(input_data) == 0: return []
        
        file1_index = selected_list[-2]
        file2_index = selected_list[-1]
        if 'raw_response' in input_data[file1_index]:
            input_data[file1_index]['raw_response'] = json.loads(input_data[file1_index]['raw_response'])
        if 'raw_response' in input_data[file2_index]:
            input_data[file2_index]['raw_response'] = json.loads(input_data[file2_index]['raw_response'])
        
        json1 = flatten(input_data[file1_index])
        json2 = flatten(input_data[file2_index])
        difference = diff(json1, json2, syntax='symmetric', marshal=True)

        return json.dumps(difference, indent=2)

        selected_filenames = [s+'.json' for s in selected_list]
        json1, json2, filename1, filename2 = None, None, None, None

        if len(selected_list) >= 1:
            filename1 = selected_filenames[-1]
            json1 = input_data[filename1]
        if len(selected_list) >= 2:
            filename2 = selected_filenames[-2]
            json2 = input_data[filename2]
        difference = diff(json1, json2, syntax='symmetric', marshal=True)

        return json.dumps(difference, indent=2), (filename1 + ' & ' + filename2)

    @app.callback(Output(id('json_')+str(x), 'children'), Input(id('json_store_')+str(x), 'data'))
    def generate_json(json_tree):
        if json_tree == [] or json_tree is None: return []
        json_tree = json.loads(json_tree)
        return json.dumps(json_tree, indent=2)













# # Store & generate selected
# for x in range(1, 6):
#     if x == 2: continue

#     @app.callback(Output('selected_list_store_evolution_'+str(x), 'data'), 
#                 Input({'type': 'select_button_evolution_'+str(x), 'index': ALL}, 'n_clicks'),
#                 State('selected_list_store_evolution_'+str(x), 'data'))
#     def store_selected(n_clicks, selected_list):
#         if all(v is None for v in n_clicks): return selected_list
#         if selected_list is None: selected_list = []
#         triggered_id = json.loads(callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0])['index']

#         # If clicked on Clear Selection
#         if triggered_id == -1:
#             selected_list = []
#         # Return selected
#         else:
#             selected_list.append(triggered_id)

#         return selected_list

#     @app.callback(Output('selected_list_evolution_'+str(x), 'children'), Input('selected_list_store_evolution_'+str(x), 'data'))
#     def generate_selected(selected_list):
#         return str(selected_list)


# # Generate Original Json Trees
# @app.callback([Output('json_tree_evolution_original_1', 'children'), Output('selected_filename_evolution_1', 'children')], 
#             [Input('selected_list_store_evolution_1', 'data'), State('input_data_store', 'data')])
# def generate_json_tree(selected_list, input_data):
#     if selected_list is None or len(selected_list) < 1: return [], ''
#     selected_filenames = [s+'.json' for s in selected_list]
#     filename = selected_filenames[-1]
#     return json.dumps(input_data[filename], indent=2), filename

# @app.callback([Output('json_tree_evolution_original_2', 'children'), Output('selected_filename_evolution_2', 'children')], 
#             [Input('selected_list_store_evolution_1', 'data'), State('input_data_store', 'data')])
# def generate_json_tree(selected_list, input_data):
#     if selected_list is None or len(selected_list) < 2: return [], ''
#     selected_filenames = [s+'.json' for s in selected_list]
#     filename = selected_filenames[-2]
#     return json.dumps(input_data[filename], indent=2), filename


# # General Difference Json Trees
# for x in range(3, 6):
#     @app.callback([Output('json_tree_evolution_'+str(x), 'children'), Output('selected_filename_evolution_'+str(x), 'children')], 
#                 [Input('selected_list_store_evolution_'+str(x), 'data'), State('input_data_store', 'data')])
#     def generate_json_tree(selected_list, input_data):
#         if selected_list is None: return selected_list, no_update
#         if len(selected_list) < 2: return 'Select one more', no_update

#         selected_filenames = [s+'.json' for s in selected_list]
#         json1, json2, filename1, filename2 = None, None, None, None

#         if len(selected_list) >= 1:
#             filename1 = selected_filenames[-1]
#             json1 = input_data[filename1]
#         if len(selected_list) >= 2:
#             filename2 = selected_filenames[-2]
#             json2 = input_data[filename2]
#         difference = diff(json1, json2, syntax='symmetric', marshal=True)

#         return json.dumps(difference, indent=2), (filename1 + ' & ' + filename2)

