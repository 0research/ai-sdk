from typing_extensions import ParamSpecArgs
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
from dash import dash_table
from dash import no_update, callback_context
import json
from flatten_json import flatten, unflatten, unflatten_list
from jsonmerge import Merger
from pprint import pprint
from genson import SchemaBuilder
from jsondiff import diff
import json
from jsondiff import diff, symbols
from apps.util import *
import base64
import pandas as pd
from pandas import json_normalize
from itertools import zip_longest
from datetime import datetime
import dash_cytoscape as cyto
from apps.typesense_client import *
import ast
from apps.constants import *

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('data_lineage')

    

# Creating styles
stylesheet = [
    # Edge
    {
        'selector': 'edge',
        'style': {
            # 'label': 'data(id)',
            'curve-style': 'bezier',
            'target-arrow-color': 'black',
            'target-arrow-shape': 'triangle',
            'line-color': 'black'
        }
    },

    # Dataset_API Node
    {
        'selector': '.dataset_api',
        'style': {
        #     'background-color': 'black',
        #     # 'width': 25,
        #     # 'height': 25,
        #     # 'background-fit': 'cover',
        #     # 'background-image': "/assets/static/api.png"
            'content': 'API'
        }
    },
    # Action
    {
        'selector': '.action',
        'style': {
            # 'background-color': 'yellow',
            # 'width': 25,
            # 'height': 25,
            # 'background-image': "/assets/static/api.png"
            'shape': 'rectangle',
            'content': 'data(action)'
        }
    },

]


layout = html.Div([
    html.Div([
        dbc.Row(dbc.Col(html.H5('Data Lineage (Data Flow Experiments)', style={'text-align':'center'}))),

        dbc.Row([
            dbc.Col([
                html.Button('Inspect', id=id('button_inspect'), className='btn btn-info btn-lg', style={'margin-right':'1px'}), 
                html.Button('Plot Graph', id=id('button_plot_graph'), className='btn btn-success btn-lg', style={'margin-right':'15px'}),
                html.Button('Upload Dataset', id=id('button_upload'), className='btn btn-primary btn-lg', style={'margin-right':'1px'}), 
                html.Button('Remove Node', id=id('button_remove'), className='btn btn-danger btn-lg', style={'margin-right':'15px'}),
                html.Button('Reset', id=id('button_reset'), className='btn btn-secondary btn-lg', style={'margin-right':'1px'}),
                # html.Button('Hide/Show', id=id('button_hide_show'), className='btn btn-warning btn-lg', style={'margin-right':'1px'}), 

                dbc.DropdownMenu(label="Action", children=[], id=id('dropdown_action'), style={'float':'right'}, size='lg', color='warning'),

                cyto.Cytoscape(id=id('cytoscape'),
                                minZoom=0.2,
                                maxZoom=2,
                                elements=[], 
                                layout={'name': 'breadthfirst',
                                        'fit': True,
                                        'directed': True,
                                        'padding': 10,
                                        },
                                style={'height': '815px','width': '100%'},
                                stylesheet=stylesheet)
            ], width=8),

            dbc.Col([
                dbc.Tabs([], id=id("tabs_node")), 
                dbc.Card([
                    dbc.CardHeader(html.P(id=id('node_name'), style={'text-align':'center', 'font-size':'22px', 'font-weight':'bold', 'width':'100%'})),
                    dbc.CardBody(html.Div(id=id('node_content'), style={'height': '750px'})),
                ], className='bg-primary', inverse=True),
                # , style={'overflow-x':'scroll'}
                # dbc.Card([
                #     dbc.CardHeader(html.H5('Experiments'), style={'text-align':'center'}),
                #     dbc.CardBody(html.P('experiments'), id=id('experiments')),
                #     dbc.CardFooter('Buttons'),
                # ], className='bg-info', style={'height': '450px'}),

            ], width=4),
        ]),

        # Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('', id=id('modal_title'))),
            dbc.ModalBody('', id=id('modal_body')),
            dbc.ModalFooter('', id=id('modal_footer')),
        ], id=id('modal'), size='xl'),

    ], style={'width':'100%'}),
])



# Load Cytoscape & Button Reset
@app.callback(Output(id('cytoscape'), 'elements'),
                Output(id('cytoscape'), 'layout'),
                # Output(id('cytoscape'), 'zoom'),
                # Input(id('interval'), 'n_intervals'),
                Input(id('button_reset'), 'n_clicks'),
                Input('url', 'pathname'))
def generate_cytoscape(n_clicks, pathname):
    project_id = get_session('project_id')
    if project_id is None: return no_update
    
    elements = generate_cytoscape_elements(project_id)
    roots = [e['data']['id'] for e in elements if e['classes'] == 'dataset_api']
    layout={'name': 'breadthfirst',
        'fit': True,
        'roots': roots
    }

    return elements, layout
    
    

def display_metadata(dataset_id):
    dataset = get_document('dataset', dataset_id)
    columns = [col for col, show in dataset['column'].items() if show == True]
    datatype = {col:dtype for col, dtype in dataset['datatype'].items() if col in columns}
    return (
        html.Div([
            html.Div([
                dbc.InputGroup([
                    dbc.InputGroupText("Dataset ID", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Input(disabled=True, value=dataset_id, style={'font-size': '12px', 'text-align':'center'}),
                ], className="mb-3 lg"),
                dbc.InputGroup([
                    dbc.InputGroupText("Index Column", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Input(disabled=True, value=dataset['index'], style={'font-size': '12px', 'text-align':'center'}),
                ], className="mb-3 lg"),
                dbc.InputGroup([
                    dbc.InputGroupText("Target Column", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                    dbc.Input(disabled=True, value=dataset['target'], style={'font-size': '12px', 'text-align':'center'}),
                ], className="mb-3 lg"),
            ]),
            html.Table(
                [
                    html.Tr([
                        html.Th('Column'),
                        html.Th('Datatype'),
                        html.Th('Invalid (%)'),
                        html.Th('Result'),
                    ])
                ] + 
                [
                    html.Tr([
                        html.Td(html.P(col), id={'type':id('col_column'), 'index': i}),
                        html.Td(html.P(dtype)),
                        html.Td(html.P('%', id={'type':id('col_invalid'), 'index': i})),
                        html.Td(html.P('-', id={'type':id('col_result'), 'index': i})),
                    ], id={'type':id('row'), 'index': i}) for i, (col, dtype) in enumerate(datatype.items())
                ],
                style={'width':'100%', 'height':'800px'}, id=id('table_data_profile')
            )
        ])
    )

def display_action(action_id):
    action = get_document('action', action_id)
    return (
        html.Div([
            dbc.InputGroup([
                dbc.InputGroupText("Action ID", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Input(disabled=True, value=action['id'], style={'font-size': '12px', 'text-align':'center'}),
            ], className="mb-3 lg"),
            dbc.InputGroup([
                dbc.InputGroupText("Action", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Input(disabled=True, value=action['action'], style={'font-size': '12px', 'text-align':'center'}),
            ], className="mb-3 lg"),
            dbc.InputGroup([
                dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Textarea(disabled=True, value=action['description'], style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
            ], className="mb-3 lg"),
            dbc.InputGroup([
                dbc.InputGroupText("Action Details", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                dbc.Textarea(disabled=True, value=str(action['action_details']), style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
            ], className="mb-3 lg"),
        ])
    )



# Generate Tabs & Store Selected Node into Session
@app.callback(
    Output(id('tabs_node'), 'children'),
    Output(id('tabs_node'), 'active_tab'),
    Input(id('cytoscape'), 'selectedNodeData'),
    State(id('tabs_node'), 'active_tab')
)
def generate_tabs(selectedNodeData, current_active_tab):
    active_tab = None
    tab1_disabled = False
    tab2_disabled = False
    tab_list = [
        dbc.Tab(label="Data", tab_id="tab1", disabled=tab1_disabled),
        dbc.Tab(label="Metadata", tab_id="tab2", disabled=tab2_disabled),
    ]

    if selectedNodeData is None: return tab_list, active_tab
    
    # Only one action Selected
    if len(selectedNodeData) == 1 and selectedNodeData[0]['type'] == 'action':
        tab1_disabled = True
        active_tab = "tab2"
    
    # All nodes selected are 'dataset' or 'dataset_api'
    if len(selectedNodeData) > 0 and all( (node['type'] == 'dataset' or node['type'] == 'dataset_api') for node in selectedNodeData):
        if len(selectedNodeData) == 1:
            active_tab = current_active_tab if current_active_tab is not None else 'tab1'
        if len(selectedNodeData) > 1:
            tab2_disabled = True
            active_tab = "tab1"
        

        # Only change selected node if only 1 node selected
        if len(selectedNodeData) == 1: 
            store_session('dataset_id', selectedNodeData[0]['id'])

    # Invalid Node Combinations Selected
    else:
        tab1_disabled = True
        tab2_disabled = True
        store_session('dataset_id', None)

    tab_list = [
        dbc.Tab(label="Data", tab_id="tab1", disabled=tab1_disabled),
        dbc.Tab(label="Metadata", tab_id="tab2", disabled=tab2_disabled),
    ]
    
    return tab_list, active_tab


# Generate Node Data
@app.callback(Output(id('node_name'), 'children'),
                Output(id('node_name'), 'contentEditable'),
                Output(id('node_content'), 'children'),
                Input(id('tabs_node'), 'active_tab'),
                State(id('cytoscape'), 'selectedNodeData'),)
def select_node(active_tab, selectedNodeData):
    pprint(selectedNodeData)
    contentEditable = 'false'

    if active_tab == 'tab1':
        # out = [html.Button('View In Tabular Format', id=id('button_tabular'), className='btn btn-info btn-lg', style={'margin-right':'1px'})]
        out = []
        for node in selectedNodeData:
            dataset_data = get_dataset_data(node['id']).to_dict('records')
            out.append(html.Pre(json.dumps(dataset_data, indent=2), style={'height': '750px', 'font-size':'12px', 'overflow-y':'auto', 'overflow-x':'scroll'}))
        name = selectedNodeData[0]['type']
        contentEditable = 'true'

    elif active_tab == 'tab2':
        if selectedNodeData[0]['type'] == 'action': 
            name = selectedNodeData[0]['type']
            out = display_action(selectedNodeData[0]['id'])
        else: 
            name = selectedNodeData[0]['type']
            out = display_metadata(selectedNodeData[0]['id'])

    else:
        name = ''
        out = ''

    return name, contentEditable, out


    # if len(selectedNodeData) == 0 and selectedNodeData[0]['type'] == 'action':
    #     store_session('dataset_id', None)
    #     return no_update, selectedNodeData[0]['type'], display_action(selectedNodeData[0]['id'])
        
    # if all( (node['type'] == 'dataset' or node['type'] == 'dataset_api') for node in selectedNodeData):
    #     store_session('dataset_id', selectedNodeData['id'])
        
    #     return tapNodeData['id'], tapNodeData['type'], display_metadata(tapNodeData['id'])
            
        

# @app.callback(Output(id('node_content'), 'children'),
#                 Input(id('tabs_node'), 'active_tab'))
# def generate_node_tabs(active_tab):
#     if active_tab == 'tab1':
#         out = html.P('asdasd'*100)

#     elif active_tab == 'tab2':
#         out = html.P('22'*100)
#     return out



# Select Node Multiple 
@app.callback(Output('modal_confirm', 'children'),
                Input(id('cytoscape'), 'selectedNodeData'),)
def select_node_multiple(selectedNodeData):
    if selectedNodeData is None or len(selectedNodeData) == 0: return no_update

    if all(node['type'] == 'dataset' or node['type'] == 'dataset_api' for node in selectedNodeData):
        selected_id_list = [node['id'] for node in selectedNodeData]
        store_session('dataset_id_multiple', selected_id_list)

    return no_update



# Add Dataset
@app.callback(Output('url', 'pathname'),
                Input(id('button_upload'), 'n_clicks'))
def button_add(n_clicks):
    if n_clicks is None: return no_update
    return '/apps/upload_dataset'

# Inspect Button
@app.callback(Output(id('modal'), 'is_open'),
                Output(id('modal_title'), 'children'),
                Output(id('modal_body'), 'children'),
                Output(id('modal_footer'), 'children'),
                Input(id('button_inspect'), 'n_clicks'),
                Input(id('cytoscape'), 'tapNodeData'))
def button_inspect_action(n_clicks_inspect, tapNodeData):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '': return no_update
    if tapNodeData is None: return no_update
    
    if triggered == id('button_inspect'):
        node_id = tapNodeData['id']
        modal_title = "Inspect"
        modal_footer = ''

        # Retrieve Dataset Data
        if tapNodeData['type'] == 'dataset' or tapNodeData['type'] == 'dataset_api':
            dataset = get_document('dataset', node_id)
            df = get_dataset_data(node_id)
            modal_body = (dbc.ModalBody([
                        dbc.InputGroup([
                            dbc.InputGroupText("Dataset ID", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Input(disabled=True, value=dataset['id'], style={'font-size': '12px', 'text-align':'center'}),
                        ], className="mb-3 lg"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Textarea(disabled=True, value=dataset['description'], style={'font-size': '12px', 'text-align':'center','padding': '30px 0'}),
                        ], className="mb-3 lg"),
                        html.Div(generate_datatable(id('inspect_modal_datatable'), df.to_dict('records'), df.columns, height='700px')),
                    ]))
        # Retrieve Action Data
        elif tapNodeData['type'] == 'action':
            action = get_document('action', node_id)
            modal_body = (dbc.ModalBody([
                        dbc.InputGroup([
                            dbc.InputGroupText("Action ID", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Input(disabled=True, value=action['id'], style={'font-size': '12px', 'text-align':'center'}),
                        ], className="mb-3 lg"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Action", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Input(disabled=True, value=action['action'], style={'font-size': '12px', 'text-align':'center'}),
                        ], className="mb-3 lg"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Textarea(disabled=True, value=action['description'], style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                        ], className="mb-3 lg"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Action Details", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Textarea(disabled=True, value=str(action['action_details']), style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                        ], className="mb-3 lg"),
                    ]))

        return True, modal_title, modal_body, modal_footer

    else:
        return no_update


# Add Graph
@app.callback(Output('url', 'pathname'),
                Input(id('button_plot_graph'), 'n_clicks'),
                State(id('cytoscape'), 'selectedNodeData'))
def button_plot_graph(n_clicks, selectedNodeData):
    if n_clicks is None: return no_update
    if selectedNodeData is None: return no_update
    if len(selectedNodeData) != 1: return no_update
    if selectedNodeData[0]['type'] == 'action': return no_update

    return '/apps/plot_graph'


# Remove Node
@app.callback(Output('modal_confirm', 'children'),
                Output('url', 'pathname'),
                Input(id('button_remove'), 'n_clicks'),
                State(id('cytoscape'), 'tapNodeData'),
                prevent_initial_call=True)
def button_remove(n_clicks, tapNodeData):
    if n_clicks is None: return no_update
    if tapNodeData is None: return no_update

    remove(get_session('project_id'), tapNodeData['id'])

    return no_update, '/apps/data_lineage'


# Generate options in dropdown and button 
@app.callback(Output(id('dropdown_action'), 'children'),
                Input(id('cytoscape'), 'selectedNodeData'),
                # Input(id('dropdown_action'), 'children')
                )
def generate_dropdown_actions(selected_nodes):
    if selected_nodes is None: return no_update
    
    single = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==False ]
    multiple = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==True ]
    
    # Generate Options
    options = []
    if len(selected_nodes) == 1:
        options = [dbc.DropdownMenuItem(nav['label'], href=nav['value']) for nav in single]
    elif len(selected_nodes) > 1 and all(node['type'] != 'action' for node in selected_nodes):
        options = [dbc.DropdownMenuItem(nav['label'], href=nav['value']) for nav in multiple]

    return options

# # Generate options in dropdown and button 
# @app.callback(Output(id('dropdown_action'), 'options'),
#                 Output(id('dropdown_action'), 'value'),
#                 Output(id('button_action'), 'children'),
#                 Output(id('button_action'), 'href'),
#                 # Output(id('button_action'), 'children'),
#                 Input(id('cytoscape'), 'selectedNodeData'),
#                 Input(id('dropdown_action'), 'value'),
#                 State(id('dropdown_action'), 'options'))
# def generate_dropdown_actions(selected_nodes, action_href, options):
#     if selected_nodes is None: return no_update
#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

#     if triggered == id('cytoscape'):
#         options = []
#         single = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==False ]
#         multiple = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==True ]

#         # Generate Options
#         if len(selected_nodes) == 1:
#             options = [ {'label':nav['label'], 'value':nav['value']} for nav in single ]
#         elif len(selected_nodes) > 1:
#             options = [ {'label':nav['label'], 'value':nav['value']} for nav in multiple ]
        
#         # Set Default selected value
#         default_label, default_action = None, None
#         if len(options) > 0:
#             default_label = options[0]['label']
#             default_action = options[0]['value']

#         return options, default_action, default_label, default_action

#     elif triggered == id('dropdown_action'):
#         label = [o['label'] for o in options if o['value'] == action_href][0]

#         return no_update, no_update, label, action_href


# # Change button_action href based on selected action
# @app.callback(Output(id('button_action'), 'children'),
#                 Output(id('button_action'), 'href'),
#                 Input(id('dropdown_action'), 'value'),
#                 State(id('dropdown_action'), 'options'))
# def button_modify_on_select_action(selected, options):
#     if selected is None: return no_update
#     label = [o['label'] for o in options if o['value'] == selected][0]

#     if label == 'Merge Strategy':
#         return 'Merge', None

#     return label, selected


# @app.callback(Output('modal_confirm', 'children'),
#                 Input(id('button_action'), 'n_clicks'),
#                 State(id('dropdown_action'), 'value'),
#                 State('current_dataset', 'data'),
#                 State(id('cytoscape'), 'selectedNodeData'),
#                 prevent_initial_call=True)
# def button_action(n_clicks, selected, dataset_id, node_id):
#     # merge_nodes()
#     return no_update





# # Perform Action
# @app.callback(Output(id('button_action'), 'children'),
#                 Input(id('button_action'), 'n_clicks'))
# def button_action(n_clicks):
#     if n_clicks is None: return no_update
#     return 'abc'








# Load, Add, Delete, Merge
# @app.callback(Output(id('cytoscape'), 'elements'), 
#                 [Input('url', 'pathname'),
#                 Input(id('button_add_api'), 'n_clicks'), 
#                 State(id('cytoscape'), 'tapNodeData'),
#                 State(id('cytoscape'), 'elements'),
#                 State('dataset_metadata', 'data'),])
# def add_version(pathname, n_clicks, tapNodeData, elements, metadata):
#     triggered = callback_context.triggered[0]['prop_id']

#      # On Page Load
#     if triggered == '.':
#         data = []
#         # for api in metadata['api']:
#         #     pass
       
#     if n_clicks is None: return no_update
#     if tapNodeData is None: return no_update

#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

#     if triggered == id('button_add_api'):
#         new_version_id = str(len(elements)//2)
#         elements += [
#             {
#             'data': {'id': new_version_id, 'label': 'Version '+str(new_version_id)},
#             # 'position': {'x': 150, 'y': 150}
#             },
#             {
#                 'data': {
#                     'id': tapNodeData['id'] + '_' + new_version_id,
#                     'source': tapNodeData['id'],
#                     'target': new_version_id,
#                     'label': 'Edge from ' + str(tapNodeData['id']) + ' to ' + str(new_version_id)
#                 },
#                 # 'classes': 'blob'
#             }
#         ]
#     elif triggered == id('button_remove'):
#         pass

#     return elements



# # Display Selected Version Name
# @app.callback(Output(id('selected_version'), 'children'), 
#                 Input(id('cytoscape'), 'selectedNodeData'))
# def display_selected_version(selected_node_list):
#     if selected_node_list is None or len(selected_node_list) == 0: return 'Selected: None'
#     node_list = [node['label'] for node in selected_node_list]
#     return 'Selected(temporary): ' + ', '.join(node_list)


# # Display Version Data & Difference
# @app.callback(Output(id('tab_1'), 'label'),
#                 Output(id('data_output'), 'children'),
#                 [Input(id('cytoscape'), 'tapNodeData'),
#                 Input(id('cytoscape'), 'selectedNodeData'),
#                 Input(id('cytoscape'), 'tapEdgeData')])
# def displayTapNode(node_data, selectedNodeData, edge_data):
#     triggered = callback_context.triggered[0]['prop_id']
#     if triggered == '.': return no_update
#     triggered = triggered.rsplit('.', 1)[1]

#     if triggered == 'tapNodeData':
#         label = 'Version Data'
#         data = node_data

#     elif triggered == 'selectedNodeData':
#         label = '?'
#         data = selectedNodeData

#     elif triggered == 'tapEdgeData':
#         label = 'Difference'
#         data = edge_data

#     print(triggered)

#     return triggered, json.dumps(data, indent=2)





# @app.callback(Output(id('experiments'), 'children'),
#                 Input('url', 'pathname'),
#                 State('current_dataset', 'data'))
# def generate_experiments(pathname, dataset_id):
#     if dataset_id is None or dataset_id == '': return no_update
#     dataset = get_document('dataset', dataset_id)

#     return [dbc.Card(children=(dbc.CardHeader(experiment['name']), dbc.CardBody(experiment['description'])), color="info", inverse=True) for experiment in dataset['experiment']]
