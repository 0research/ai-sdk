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
from jsonmerge import Merger, merge
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

    # Dataset Nodes
    {
        'selector': '.raw_userinput',
        'style': {
        #     'background-color': 'black',
        #     # 'width': 25,
        #     # 'height': 25,
        #     # 'background-fit': 'cover',
        #     # 'background-image': "/assets/static/api.png"
            'content': 'data(name)'
        }
    },
    {
        'selector': '.raw_restapi',
        'style': {
        #     'background-color': 'black',
        #     # 'width': 25,
        #     # 'height': 25,
        #     # 'background-fit': 'cover',
        #     # 'background-image': "/assets/static/api.png"
            'content': 'data(name)'
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
                html.Button('Add Dataset', id=id('button_upload'), className='btn btn-primary btn-lg', style={'margin-right':'1px'}), 
                html.Button('Reset', id=id('button_reset'), className='btn btn-secondary btn-lg', style={'margin-right':'1px'}),
                # html.Button('Hide/Show', id=id('button_hide_show'), className='btn btn-warning btn-lg', style={'margin-right':'1px'}), 

                dbc.DropdownMenu(label="Action", children=[], id=id('dropdown_action'), style={'float':'right'}, size='lg', color='warning'),

                cyto.Cytoscape(id=id('cytoscape'),
                                minZoom=0.2,
                                maxZoom=2,
                                elements=[], 
                                selectedNodeData=[],
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
                    dbc.CardHeader([
                        html.P(id=id('node_name_list'), style={'text-align':'center', 'font-size':'20px', 'font-weight':'bold', 'float':'left', 'width':'75%'}),
                        html.Div([
                            dbc.Button(html.I(n_clicks=0, className='fa fa-table'), id=id('button_tabular'), className='btn btn-info'),
                            dbc.Button(html.I(n_clicks=0, className='fas fa-chart-area'), id=id('button_chart'), className='btn btn-success', style={'margin-left':'1px'}),
                            dbc.Button(html.I(n_clicks=0, className='fas fa-times'), id=id('button_remove'), className='btn btn-danger', style={'margin-left':'1px'}),
                            dbc.Tooltip('View in Tabular Format', target=id('button_tabular')),
                            dbc.Tooltip('Chart', target=id('button_chart')),
                            dbc.Tooltip('Remove Action or Raw Dataset', target=id('button_remove')),
                        ], style={'width': '25%', 'float':'right', 'text-align':'right'}),
                    ]),
                    dbc.CardBody(html.Div(id=id('node_content'), style={'min-height': '750px'})),
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

    

# Generate Tabs & Store Selected Node into Session
@app.callback(
    Output(id('tabs_node'), 'children'),
    Output(id('tabs_node'), 'active_tab'),
    Input(id('cytoscape'), 'selectedNodeData'),
    Input('url', 'pathname'),
    State(id('tabs_node'), 'active_tab')
)
def generate_tabs(selectedNodeData, pathname, active_tab):
    tab1_disabled, tab2_disabled, tab3_disabled = True, True, True

    # One 'action' Selected
    if len(selectedNodeData) == 1 and selectedNodeData[0]['type'] == 'action':
        tab2_disabled = False
        active_tab = "tab2"

    # Single Raw/Processed dataset selected
    elif len(selectedNodeData) == 1 and (selectedNodeData[0]['type'] != 'action'):
        store_session('dataset_id', selectedNodeData[0]['id'])
        active_tab = 'tab1' if (active_tab == 'tab3' or active_tab == 'tab4' or active_tab is None) else active_tab
        tab1_disabled = False
        tab2_disabled = False
    
    # Multiple Raw/Processed dataset selected
    elif len(selectedNodeData) > 1 and all((node['type'] != 'action') for node in selectedNodeData):
        store_session('dataset_id', None)
        active_tab = 'tab3' if (active_tab == 'tab1' or active_tab == 'tab2' or active_tab is None) else active_tab
        tab3_disabled = False
        
    # Invalid Node Combinations Selected
    else:
        active_tab = None
        store_session('dataset_id', None)

    tab_list = [
        dbc.Tab(label="JSON", tab_id="tab1", disabled=tab1_disabled),
        dbc.Tab(label="Metadata", tab_id="tab2", disabled=tab2_disabled),
        dbc.Tab(label="Merged", tab_id="tab3", disabled=tab3_disabled),
        dbc.Tab(label="Merged Metadata", tab_id="tab4", disabled=tab3_disabled),
    ]
    return tab_list, active_tab




# Generate Node Data
@app.callback(Output(id('node_name_list'), 'children'),
                # Output(id('node_name_list'), 'contentEditable'),
                Output(id('node_content'), 'children'),
                Input(id('tabs_node'), 'active_tab'),
                State(id('cytoscape'), 'selectedNodeData'))
def select_node(active_tab, selectedNodeData):
    if len(selectedNodeData) == 0: return '', ''
    pprint(selectedNodeData)
    name, out, base = [], [], []
    

    if active_tab == 'tab1':
        name = html.Div(selectedNodeData[0]['type'], id=id(selectedNodeData[-1]['id']), contentEditable='true', className="badge border border-info text-wrap")
        dataset_data_store = get_dataset_data_store(selectedNodeData[-1]['id']).to_dict('records')
        out = [dbc.Input(id=id('search_json'), placeholder='Search', style={'text-align':'center'})] + [display_dataset_data_store(dataset_data_store)]

    elif active_tab == 'tab2':
        name = html.Div(selectedNodeData[0]['type'], id=id(selectedNodeData[-1]['id']), contentEditable='true', className="badge border border-info text-wrap")
        if selectedNodeData[0]['type'] == 'action': 
            action = get_document('action', selectedNodeData[-1]['id'])
            out = out + [display_action(action)]

        else: 
            dataset = get_document('dataset', selectedNodeData[-1]['id'])
            out = out + [display_metadata(dataset)]
            out = [dbc.CardBody(dbc.Button('Modify Metadata', id=id('button_modify_metadata'), className='btn btn-warning btn-lg', style={'width':'100%'}))] + out

    elif active_tab == 'tab3':
        
        for node in selectedNodeData:
            name = name + [html.Div([
                html.P(str(len(name)+1)+')', style={'display':'inline-block', 'font-size':'13px'}),
                html.P(node['type'], id=id(node['id']), contentEditable='true', style={'margin':'5px', 'display':'inline-block'}),
            ], style={'display':'inline-block'}, className="badge border border-info text-wrap")]
        
        data = get_dataset_data_store(selectedNodeData[0]['id']).to_dict('records')
        for node in selectedNodeData[1:]:
            new_data = get_dataset_data_store(node['id']).to_dict('records')
            data = [json_merge(row, row_new, 'objectMerge') for row, row_new in zip(data, new_data)]

        out = [dbc.Input(id=id('search_json'), placeholder='Search', style={'text-align':'center'})]
        out = out + [display_dataset_data_store(data)]
        out = [dbc.CardBody(dbc.Button('Perform Merge Action', id={'type': id('button_merge'), 'index': 0}, className='btn btn-warning btn-lg', style={'width':'100%'}))] + out
    

    elif active_tab == 'tab4':

        for i, node in enumerate(selectedNodeData):
            name = name + [html.Div([
                html.P(str(len(name)+1)+')', style={'display':'inline-block', 'font-size':'13px'}),
                html.P(node['type'], id=id(node['id']), contentEditable='true', style={'margin':'5px', 'display':'inline-block'}),
            ], style={'display':'inline-block'}, className="badge border border-info text-wrap")]

        dataset = get_document('dataset', selectedNodeData[0]['id'])
        dataset['details'] = None
        for node in selectedNodeData[1:]:
            node['details'] = None
            dataset = json_merge(dataset, get_document('dataset', node['id']), 'objectMerge')

        out = out + [display_dataset_data_store(dataset)]
        out = [dbc.CardBody(dbc.Button('Perform Merge Action', id={'type': id('button_merge'), 'index': 0}, className='btn btn-warning btn-lg', style={'width':'100%'}))] + out

    else:
        name, out  = [], []

    return name, out





# Load Cytoscape & Button Reset
@app.callback(
    Output(id('cytoscape'), 'elements'),
    Output(id('cytoscape'), 'layout'),
    Input(id('button_reset'), 'n_clicks'),
    Input({'type': id('button_merge'), 'index': ALL}, 'n_clicks'),
    Input('url', 'pathname'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def generate_cytoscape(n_clicks_reset, n_clicks_merge, pathname, selectedNodeData):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    project_id = get_session('project_id')

    # On Page Load and Reset Button pressed
    if triggered == '' or triggered == id('button_reset'):
        pass

    # Merge Dataset Metadata and Data
    elif triggered == '{"index":0,"type":"data_lineage-button_merge"}':
        if n_clicks_merge[0] is None: return no_update

        dataset = get_document('dataset', selectedNodeData[0]['id'])
        dataset['details'] = None
        data = get_dataset_data_store(selectedNodeData[0]['id']).to_dict('records')
        for node in selectedNodeData[1:]:
            node['details'] = None
            dataset = json_merge(dataset, get_document('dataset', node['id']), 'objectMerge')
            new_data = get_dataset_data_store(node['id']).to_dict('records')
            data = [json_merge(row, row_new, 'objectMerge') for row, row_new in zip(data, new_data)]

        # data = []
        # for node in selectedNodeData:
        #     data = json_merge(data, get_dataset_data_store(node['id']).to_dict('records'), 'overwrite')     

        source_id_list = [node['id'] for node in selectedNodeData]
        details = { 'merge_type': 'objectMerge'}
        merge(project_id, source_id_list, '', data, dataset, details)

    elements = generate_cytoscape_elements(project_id)
    pprint(elements)
    layout={'name': 'breadthfirst',
        'fit': True,
        'roots': [e['data']['id'] for e in elements if e['classes'].startswith('raw_')]
    }
    return elements, layout






# Add Dataset
@app.callback(Output('url', 'pathname'),
                Input(id('button_upload'), 'n_clicks'))
def button_add(n_clicks):
    if n_clicks is None: return no_update
    return '/apps/search'




# Disable/Enable Right Panel Buttons
@app.callback(
    Output(id('button_tabular'), 'disabled'),
    Output(id('button_chart'), 'disabled'),
    Output(id('button_remove'), 'disabled'),
    Input(id('tabs_node'), 'active_tab'),
    Input('url', 'pathname'),
)
def button_disable_enable(active_tab, pathname):
    if active_tab == 'tab1': return False, False, False
    elif active_tab == 'tab2': return True, True, False
    elif active_tab == 'tab3': return False, True, True
    elif active_tab == 'tab4': return True, True, True
    else: return True, True, True

# View in Tabular Format
@app.callback(
    Output(id('modal'), 'is_open'),
    Output(id('modal_title'), 'children'),
    Output(id('modal_body'), 'children'),
    Output(id('modal_footer'), 'children'),
    Input(id('button_tabular'), 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData')
)
def button_tabular(n_clicks, selectedNodeData):
    if n_clicks is None: return no_update
    if selectedNodeData is None: return no_update
    if len(selectedNodeData) == 0: return no_update

    # Retrieve Dataset Data
    if all(node['type'] != 'action' for node in selectedNodeData):
        if len(selectedNodeData) == 1:
            df = get_dataset_data_store(selectedNodeData[-1]['id'])
            out = df.to_dict('records')
        elif len(selectedNodeData) > 1:
            base = []
            for node in selectedNodeData:
                base = json_merge(base, get_dataset_data_store(node['id']).to_dict('records'), 'overwrite')
            df = json_normalize(base)
            out = base

        modal_title = ""
        modal_footer = ''
        modal_body = html.Div(generate_datatable(id('inspect_modal_datatable'), out, df.columns, height='800px'))  
        return True, modal_title, modal_body, modal_footer

    else:
        return no_update

# Button Chart
@app.callback(Output('url', 'pathname'),
                Input(id('button_chart'), 'n_clicks'),
                State(id('cytoscape'), 'selectedNodeData'))
def button_chart(n_clicks, selectedNodeData):
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










# Select Node Multiple 
# @app.callback(Output('modal_confirm', 'children'),
#                 Input(id('cytoscape'), 'selectedNodeData'),)
# def select_node_multiple(selectedNodeData):
#     if selectedNodeData is None or len(selectedNodeData) == 0: return no_update

#     if all(node['type'] == 'dataset' or node['type'] == 'dataset_api' for node in selectedNodeData):
#         selected_id_list = [node['id'] for node in selectedNodeData]
#         store_session('dataset_id_multiple', selected_id_list)

#     return no_update



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
