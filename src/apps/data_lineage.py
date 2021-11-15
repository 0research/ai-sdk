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


def get_current_valid_edges(current_nodes, all_edges):
    """Returns edges that are present in Cytoscape:
    its source and target nodes are still present in the graph.
    """
    valid_edges = []
    node_ids = {n['data']['id'] for n in current_nodes}

    for e in all_edges:
        if e['data']['source'] in node_ids and e['data']['target'] in node_ids:
            valid_edges.append(e)
    return valid_edges
    

# Creating styles
stylesheet = [
    # Edge
    {
        'selector': 'edge',
        'style': {
            # 'label': 'data(id)',
            'source-arrow-shape': 'triangle',
        }
    },

    # API Node
    {
        'selector': '.api',
        'style': {
        #     'background-color': 'black',
        #     # 'width': 25,
        #     # 'height': 25,
        #     # 'background-fit': 'cover',
        #     # 'background-image': "/assets/static/api.png"
            'shape': 'triangle'
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
    # Blob
    # {
        # 'selector': '.blob',
        # 'style': {
        #     'background-color': 'blue',
        #     # 'width': 25,
        #     # 'height': 25,
        #     # 'background-image': "/assets/static/api.png"
        # }
    # },

]




layout = html.Div([
    dcc.Interval(id=id('interval'), interval=1000, n_intervals=0),

    html.Div([
        dbc.Row(dbc.Col(html.H1('Data Lineage (Data Flow Experiments)', style={'text-align':'center'}))),

        dbc.Row([
            dbc.Col([
                html.Button('Upload Dataset', id=id('button_upload'), className='btn btn-success btn-lg', style={'margin-right':'3px'}), 
                html.Button('Inspect', id=id('button_inspect'), className='btn btn-info btn-lg', style={'margin-right':'3px'}), 
                html.Button('Add Graph', id=id('button_add_graph'), className='btn btn-secondary btn-lg', style={'margin-right':'3px'}),
                html.Button('Hide/Show', id=id('button_hide_show'), className='btn btn-warning btn-lg', style={'margin-right':'3px'}), 
                html.Button('Remove Node', id=id('button_remove'), className='btn btn-danger btn-lg', style={'margin-right':'3px'}),

                cyto.Cytoscape(id=id('cytoscape'), 
                                elements=[], 
                                layout={'name': 'cose'},
                                style={'height': '1000px','width': '100%'},
                                stylesheet=stylesheet)
            ], width=9),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5('Action'), style={'text-align':'center'}),
                    dbc.CardHeader(dbc.Select(id=id('dropdown_action'), placeholder='Select at least one Node', style={'min-width':'120px', 'text-align':'center'}, persistence_type='session', persistence=True)),
                    dbc.CardBody(html.P('Inputs'), id=id('action_inputs')),
                    dbc.CardFooter(dbc.Button('', id=id('button_action'), color='primary', style={'width':'100%'})),
                ], className='bg-primary', style={'min-height': '250px'}, inverse=True),
                
                dbc.Card([
                    dbc.CardHeader(html.H5('Experiments'), style={'text-align':'center'}),
                    dbc.CardBody(html.P('experiments'), id=id('experiments')),
                    dbc.CardFooter('Buttons'),
                ], className='bg-info', style={'height': '500px'}),

            ], width=3),
        ]),

        # Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('', id=id('modal_title'))),
            dbc.ModalBody('', id=id('modal_body')),
            dbc.ModalFooter('', id=id('modal_footer')),
        ], id=id('modal'), size='xl'),

    ], style={'width':'100%'}),
])


@app.callback(Output(id('cytoscape'), 'elements'), 
                Input(id('interval'), 'n_intervals'))
def generate_cytoscape(n_intervals):
    project_id = get_session('project_id')
    if project_id is None: return no_update

    return generate_cytoscape_elements(project_id)


# @app.callback(Output(id('experiments'), 'children'),
#                 Input('url', 'pathname'),
#                 State('current_dataset', 'data'))
# def generate_experiments(pathname, dataset_id):
#     if dataset_id is None or dataset_id == '': return no_update
#     dataset = get_document('dataset', dataset_id)

#     return [dbc.Card(children=(dbc.CardHeader(experiment['name']), dbc.CardBody(experiment['description'])), color="info", inverse=True) for experiment in dataset['experiment']]


# Select Node Single
@app.callback(Output('display_current_dataset', 'value'),
                Input(id('cytoscape'), 'tapNodeData'),)
def select_node(tapNodeData):
    if tapNodeData is None: 
        store_session('dataset_id', None)
        return no_update
    pprint(tapNodeData)
    if tapNodeData['type'] == 'dataset':
        store_session('dataset_id', tapNodeData['id'])
        return tapNodeData['id']
    else:
        return no_update

# Select Node Multiple 
@app.callback(Output('modal_confirm', 'children'),
                Input(id('cytoscape'), 'selectedNodeData'),)
def select_node_multiple(selectedNodeData):
    if selectedNodeData is None or len(selectedNodeData) == 0: return no_update

    if all(node['type'] == 'dataset' for node in selectedNodeData):
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
        if tapNodeData['type'] == 'dataset':
            dataset = get_document('dataset', node_id)
            df = get_dataset_data(node_id)
            modal_body = (dbc.ModalBody([
                        dbc.InputGroup([
                            dbc.InputGroupText("Dataset ID", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Textarea(disabled=True, value=dataset['id'], style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                        ], className="mb-3 lg"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Description", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Textarea(disabled=True, value=dataset['description'], style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                        ], className="mb-3 lg"),
                        html.Div(generate_datatable(id('inspect_modal_datatable'), df.to_dict('records'), df.columns, height='700px')),
                    ]))
        # Retrieve Action Data
        elif tapNodeData['type'] == 'action':
            action = get_document('action', node_id)
            modal_body = (dbc.ModalBody([
                        dbc.InputGroup([
                            dbc.InputGroupText("Action ID", style={'width':'120px', 'font-weight':'bold', 'font-size':'12px', 'padding-left':'20px'}),
                            dbc.Textarea(disabled=True, value=action['id'], style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
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
                Input(id('button_add_graph'), 'n_clicks'))
def button_add_graph(n_clicks):
    if n_clicks is None: return no_update
    return '/apps/upload_graph'


# Remove Node
@app.callback(Output('modal_confirm', 'children'),
                Input(id('button_remove'), 'n_clicks'),
                State(id('cytoscape'), 'tapNodeData'),
                prevent_initial_call=True)
def button_remove(n_clicks, tapNodeData):
    if n_clicks is None: return no_update
    if tapNodeData is None: return no_update

    delete(get_session['project_id'], tapNodeData['id'])

    return ''


# Generate options in dropdown and button 
@app.callback(Output(id('dropdown_action'), 'options'),
                Output(id('dropdown_action'), 'value'),
                Output(id('button_action'), 'children'),
                Output(id('button_action'), 'href'),
                # Output(id('button_action'), 'children'),
                Input(id('cytoscape'), 'selectedNodeData'),
                Input(id('dropdown_action'), 'value'),
                State(id('dropdown_action'), 'options'))
def generate_dropdown_actions(selected_nodes, action_href, options):
    if selected_nodes is None: return no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

    if triggered == id('cytoscape'):
        options = []
        single = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==False ]
        multiple = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==True ]

        # Generate Options
        if len(selected_nodes) == 1:
            options = [ {'label':nav['label'], 'value':nav['value']} for nav in single ]
        elif len(selected_nodes) > 1:
            options = [ {'label':nav['label'], 'value':nav['value']} for nav in multiple ]
        
        # Set Default selected value
        default_label, default_action = None, None
        if len(options) > 0:
            default_label = options[0]['label']
            default_action = options[0]['value']

        return options, default_action, default_label, default_action

    elif triggered == id('dropdown_action'):
        label = [o['label'] for o in options if o['value'] == action_href][0]

        return no_update, no_update, label, action_href


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


# @app.callback(Output(id('profile_output'), 'children'),
#               [Input(id('cytoscape'), 'tapNodeData')])
# def displayTapNodeData(data):
#     return json.dumps(data, indent=2)


