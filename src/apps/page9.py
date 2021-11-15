# from dash import html
# from dash import dcc
# from dash.dependencies import Input, Output, State, ALL, MATCH
# from app import app
# import collections
# import json
# from pprint import pprint
# from jsondiff import diff
# from dash import no_update
# from apps.util import *


# # Layout
# layout = html.Div([
#     dcc.Store(id='input_data_store', storage_type='session'),
#     dcc.Store(id='selected_list_store_evolution_1', storage_type='session'),
#     dcc.Store(id='selected_list_store_evolution_3', storage_type='session'),
#     dcc.Store(id='selected_list_store_evolution_4', storage_type='session'),
#     dcc.Store(id='selected_list_store_evolution_5', storage_type='session'),
#     html.H1('Temporal Data Evolution', style={"textAlign": "center"}),

#     generate_upload('upload_json'),

#     html.Div([
#         html.Div([
#             html.H4('Original Data', style={'text-decoration': 'underline', 'textAlign': 'center'}),
#             html.Div(style={'text-align': 'center'}, children=[
#                 dbc.ButtonGroup(id='select_list_evolution_1'),
#                 html.Div(id='selected_list_evolution_1'),
#                 html.Button('Clear Selected', id={'type': 'select_button_evolution_1', 'index': -1}),
#             ]),
#             html.Div([
#                 html.H4(id='selected_filename_evolution_1', style={'text-decoration': 'underline'}), 
#                 html.Pre(id='json_tree_evolution_original_1', style={'textAlign': 'left'}),
#             ], style={'textAlign':'center', 'width': '50%', 'float': 'left'}),
#             html.Div([
#                 html.H4('', id='selected_filename_evolution_2', style={'text-decoration': 'underline'}), 
#                 html.Pre(id='json_tree_evolution_original_2', style={'textAlign': 'left'}),
#             ], style={'textAlign':'center', 'width': '50%', 'float': 'right'})
#         ], style={'float': 'left', 'width': '39.5%', "textAlign": "left", 'background-color':'#E6E6FA', 'margin':'2px'}),

#         html.Div([
#             html.Div(style={'float': 'left', 'width': '32.8%', 'background-color':'#E6E6FA', 'margin':'2px'}, children=[
#                 html.H4('Difference One', style={'text-decoration': 'underline', 'textAlign': 'center'}),
#                 dbc.ButtonGroup(id='select_list_evolution_3'),
#                 html.Div(id='selected_list_evolution_3'),
#                 html.Button('Clear Selected', id={'type': 'select_button_evolution_3', 'index': -1}),
#                 html.H4(id='selected_filename_evolution_3', style={'text-decoration': 'underline', 'textAlign': 'center'}), 
#                 html.Pre(id='json_tree_evolution_3'),
#             ]),
            
#             html.Div(style={'float': 'left', 'width': '32.8%', 'background-color':'#E6E6FA', 'margin':'2px'}, children=[
#                 html.H4('Difference Two', style={'text-decoration': 'underline', 'textAlign': 'center'}),
#                 dbc.ButtonGroup(id='select_list_evolution_4'),
#                 html.Div(id='selected_list_evolution_4'),
#                 html.Button('Clear Selected', id={'type': 'select_button_evolution_4', 'index': -1}),
#                 html.H4('', id='selected_filename_evolution_4', style={'text-decoration': 'underline', 'textAlign': 'center'}), 
#                 html.Pre(id='json_tree_evolution_4'),
#             ]),

#             html.Div(style={'float': 'left', 'width': '32.8%', 'background-color':'#E6E6FA', 'margin':'2px'}, children=[
#                 html.H4('Difference Three', style={'text-decoration': 'underline', 'textAlign': 'center'}),
#                 dbc.ButtonGroup(id='select_list_evolution_5'),
#                 html.Div(id='selected_list_evolution_5'),
#                 html.Button('Clear Selected', id={'type': 'select_button_evolution_5', 'index': -1}),
#                 html.H4('', id='selected_filename_evolution_5', style={'text-decoration': 'underline', 'textAlign': 'center'}), 
#                 html.Pre(id='json_tree_evolution_5'),
#             ]),
#         ], style={'float': 'right', 'width': '60%', "textAlign": "left"})
        
#     ], id='contentDiv', style={'display':'block'}),
# ])


# # Generate buttons
# @app.callback(Output('select_list_evolution_1', 'children'), Input('input_data_store', 'data'))
# def generate_select_2(input_data):
#     return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_evolution_1', 'index': name.split('.')[0]}) for name in sorted(input_data.keys())]

# @app.callback(Output('select_list_evolution_3', 'children'), Input('input_data_store', 'data'))
# def generate_select_2(input_data):
#     return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_evolution_3', 'index': name.split('.')[0]}) for name in sorted(input_data.keys())]

# @app.callback(Output('select_list_evolution_4', 'children'), Input('input_data_store', 'data'))
# def generate_select_3(input_data):
#     return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_evolution_4', 'index': name.split('.')[0]}) for name in sorted(input_data.keys())]

# @app.callback(Output('select_list_evolution_5', 'children'), Input('input_data_store', 'data'))
# def generate_select_4(input_data):
#     return [dbc.Button(name.split('.')[0], value=name, id={'type': 'select_button_evolution_5', 'index': name.split('.')[0]}) for name in sorted(input_data.keys())]


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

