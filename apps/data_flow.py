from os import supports_bytes_environ
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, ALL, MATCH, ClientsideFunction
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app
import dash_bootstrap_components as dbc
from dash import dash_table
from dash import no_update, callback_context
import json
from flatten_json import flatten, unflatten, unflatten_list
import jsonmerge
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

import ast
from apps.constants import *
import copy
from pathlib import Path
from datetime import datetime
from dash_extensions import EventListener, WebSocket
from dash_extensions import WebSocket
import traceback

# import heartrate
# heartrate.trace(browser=True)


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('data_flow')
du.configure_upload(app, UPLOAD_FOLDER_ROOT)

# Creating styles
cytoscape_stylesheet = [
    # All Nodes
    {
        'selector': 'node',
        'style': {
            'content': 'data(name)'
        }
    },
    # Edge
    {
        'selector': 'edge',
        'style': {
            'curve-style': 'bezier',
            'target-arrow-color': 'black',
            'target-arrow-shape': 'triangle',
            'line-color': 'black'
        }
    },
    {
        'selector': '.dependent',
        'style': {
            'background-color': '#92a8d1',
        }
    },
    # Dataset Nodes
    {
        'selector': '.raw',
        'style': {

        }
    },
    {
        'selector': '.processed',
        'style': {

        }
    },
    # Action
    {
        'selector': '[type = "action"]',
        'style': {
            # 'background-color': 'amber',
            # 'width': 25,
            # 'height': 25,
            # 'background-image': "/assets/static/api.png"
            # 'background-color': '#FFFF00',
            'shape': 'rectangle',
            'content': 'data(name)'
        }
    },

    # States
    {
        'selector': '[state = "red"]',
        'style': {
            'background-color': '#FF0000',
        }
    },
    {
        'selector': '[state = "amber"]',
        'style': {
            'background-color': '#FFBF00',
        }
    },
    {
        'selector': '[state = "yellow"]',
        'style': {
            'background-color': '#FFBF00',
        }
    },
    {
        'selector': '[state = "green"]',
        'style': {
            'background-color': '#00FF00',
        }
    },

    {
        'selector': '.selected',
        'style': {
            'background-color': '#000000',
        }
    },
]



layout = html.Div([
    html.Div([
        dcc.Store(id=id('cytoscape_position_store'), storage_type='session', data=[]),
        dcc.Store(id=id('cytoscape_position_store_2'), storage_type='session', data=[]),
        dcc.Store(id=id('transform_store'), storage_type='session', data={}),
        dcc.Store(id=id('aggregate_store'), storage_type='session', data={}),
        dcc.Store(id=id('graph_id_store'), storage_type='session', data=''),
        dcc.Interval(id=id('interval_cytoscape'), interval=500, n_intervals=0),
        
        dbc.Row([
            # Left Panel
            dbc.Col([
                html.Div([
                    dbc.Badge(id=id('project_name'), color='primary', className='me-1'),
                    dbc.Badge(id=id('last_saved'), color='secondary', className='me-1'),
                ], style={'display':'inline-block'}),
                
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button('Add Source',    id=id('button_add_dataset'),    color='info',   className='me-1', style={'width':'90px'}),
                        dbc.Button('Action',        id=id('button_new_action'),     color='warning', className='me-1', style={'width':'90px'}),
                        dbc.Button('Remove',        id=id('button_remove'),         color='danger', className='me-1', style={'width':'90px'}),
                        dbc.Button('Group',         id=id('button_group'),          color='success', className='me-1', style={'width':'90px', 'display':'none'}),
                        dbc.Button('Reset',         id=id('button_reset_layout'),   color='dark',   className='me-1', style={'width':'90px'}),
                        # dbc.Button('Hide/Show',   id=id('button_hide_show'),      color='light', className='me-1', style={'width':'90px'}),
                        dbc.Button('Run', id=id('button_run_cytoscape'), color='primary', className='me-1', disabled=True, style={'width':'90px', 'display':'none'}),     
                    ]),
                ], style={'float':'right', 'display':'inline-block'}),

                cyto.Cytoscape(id=id('cytoscape'),
                                minZoom=0.2,
                                maxZoom=2,
                                elements=[], 
                                selectedNodeData=[],
                                layout={
                                    'name': 'preset',
                                    'fit': True,
                                    'directed': True,
                                    'padding': 10,
                                    'zoom': 1,
                                },
                                style={'height': '89vh','width': '100%'},
                                stylesheet=cytoscape_stylesheet)
            ], width=6),

            # Right Panel
            dbc.Col([
                html.Div([
                    html.Div(dbc.Tabs([
                        dbc.Tab(label="Data", tab_id="tab1", disabled=True),
                        dbc.Tab(label="Metadata", tab_id="tab2", disabled=True),
                        dbc.Tab(label="Config", tab_id="tab3", disabled=True),
                        dbc.Tab(label="Graph", tab_id="tab4", disabled=False),
                        dbc.Tab(label="Logs", tab_id="tab5", disabled=False),
                    ], id=id("tabs_node")), style={'float':'left', 'text-align':'left', 'display':'inline-block'}),

                    html.Div([
                        dbc.Button('Plot Graph', id=id('button_open_graph_modal'), color='info', className='me-1', style={'width':'90px'}),
                        dbc.Button("Save", id=id('button_save_changes'), color='success', className='me-1', style={'width':'90px', 'display':'none'}),
                        dbc.Button("Revert", id=id('button_revert_changes'), color='primary', className='me-1', style={'width':'90px'}),
                        dbc.Button('Execute', id=id('button_execute_action'), color='warning', className='me-1', style={'width':'90px'}),
                        dbc.Tooltip('Store Changes', target=id('button_save_changes')),
                        dbc.Tooltip('Revert to Last Saved', target=id('button_revert_changes')),
                        dbc.Tooltip('Execute Action', target=id('button_execute_action')),
                    ], style={'float':'right'}),
                ], style={'display':'inline-block', 'width':'100%'}),
                  
                dbc.Card([
                    # Header 1 (All Tabs)
                    dbc.CardHeader([
                        html.Div([
                            dbc.Input(id=id('dataset_name'), placeholder='Enter Node Name', style={'font-size':'14px', 'text-align':'center'})
                        ], id=id('single_node_header_container'), style={'display': 'none'}),
                        html.Div([], id=id('multiple_node_header_container'), style={'display': 'none'}),
                        html.Div([
                            dbc.InputGroup([
                                dbc.Select(id=id('dropdown_action'), options=option_actions, value=None, style={'width':'80%', 'text-align':'center', 'font-size':'15px', 'font-weight':'bold'}),
                                dbc.InputGroupText('Inputs', style={'width':'50%', 'font-weight':'bold', 'font-size':'13px', 'text-align':'center'}),
                                dbc.InputGroupText('Outputs', style={'width':'50%', 'font-weight':'bold', 'font-size':'13px', 'text-align':'center'}),
                                html.Div(dcc.Dropdown(id=id('dropdown_action_inputs'), options=[], value=None, multi=False), style={'width':'50%', 'text-align':'center'}),
                                html.Div(dcc.Dropdown(id=id('dropdown_action_outputs'), options=[], value=None, disabled=True, multi=True), style={'width':'50%', 'text-align':'center'}),
                            ]),
                        ], id=id('action_header_container'), style={'display': 'none'}),
                    ], id=id('right_header_1'), style={'text-align':'center', 'font-size':'13px', 'font-weight':'bold', 'float':'left', 'width':'100%'}),

                    # Header 2 (Tab 1 only)
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([dbc.Input(id=id('search2'), placeholder='Search', style={'text-align':'center'})], width=5),
                            dbc.Col([
                                dcc.RangeSlider(0,0,1,
                                    id=id('range_slider'),
                                    value=[],
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                            ], id=id('range_slider_container'), style={'display':'hidden'}, width=3),
                            dbc.Col([
                                dbc.Button(html.I(className='fas fa-plus-circle'),  id=id('button_add_feature_modal'),  className='me-1',   color='light',  outline=True, style={'display':'none'}),
                                dbc.Button(html.I(className='fas fa-trash'),        id=id('button_remove_feature'),     className='me-1',   color='danger', outline=True, style={'display':'none'}),
                                dbc.Button(html.I(className='fas fa-eraser'),       id=id('button_clear'),              className='me-1',   color='info',   outline=True, style={'display':'none'}),
                                dbc.Button(html.I(className='fa fa-table'),         id=id('button_display_mode'),       className='me-1',   color='secondary', outline=True, n_clicks=0, style={'display':'none'}),
                                dbc.Button(html.I(className='fas fa-arrow-right'),  id=id('button_run_restapi'),        className='me-1',   color='warning',   outline=True, style={'display':'none'}),
                                dbc.Tooltip('Add Feature', target=id('button_add_feature_modal')),
                                dbc.Tooltip('Remove Feature', target=id('button_remove_feature')),
                                dbc.Tooltip('Clear all Changes', target=id('button_clear')),
                                dbc.Tooltip('View in Tabular Format', target=id('button_display_mode')),
                                dbc.Tooltip('Run API', target=id('button_run_restapi')),
                            ], width=4, style={'text-align':'right', 'float':'right'}),
                        ]),
                        
                    ], id=id('right_header_2'), style={'display':'none', 'font-size':'14px'}),

                    # Join Inputs Container
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText('Merge Type', style={'width':'30%'}),
                            dbc.Select(options=options_join, value=options_join[0]['value'], id=id('join_method'), style={'text-align':'center', 'width':'68%'})
                        ], style={'width':'40%', 'float':'left', 'display':'inline-flex'}),
                        html.Div([], id=id('join_features_container'), style={'width':'58%', 'float':'right', 'display':'inline-block'}),
                    ], id=id('join_details_container'), style={'display':'none', 'border-style':'groove'}),

                    # Merge Inputs Container
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText('Merge Type', style={'width':'30%'}),
                            dbc.Select(options=options_merge, value=options_merge[0]['value'], id=id('merge_type'), style={'text-align':'center', 'width':'68%'})
                        ], style={'width':'40%', 'float':'left', 'display':'inline-flex'}),
                        html.Div([], id=id('merge_idRef_container'), style={'width':'58%', 'float':'right', 'display':'inline-block'}),
                    ], id=id('merge_details_container'), style={'display':'none', 'border-style':'groove'}),

                    

                    # Header 3 (Tab 3)
                    dbc.CardHeader([
                        dbc.InputGroup([
                            dbc.InputGroupText('Description', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
                            dbc.Textarea(id=id('description'), placeholder='Enter Dataset Description', style={'height':'50px', 'text-align':'center'}, persistence=True, persistence_type='session'),
                        ]),
                        dbc.InputGroup([
                            dbc.InputGroupText('Documentation', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
                            dbc.Input(id=id('documentation'), placeholder='Enter Documentation URL (Optional) ', style={'height':'40px', 'min-width':'120px', 'text-align':'center'}, persistence=True, persistence_type='session'),
                        ]),
                    ], id=id('right_header_3'), style={'display':'none', 'font-size':'14px'}),
                    
                    
                    # Right Content
                    html.Div([
                        # None
                        html.Div([], id=id('right_content_0'), style={'display':'none'}),

                        # Tab 1 (Data)
                        html.Div([
                            html.Div(generate_datatable(id('datatable')), id=id('datatable_container'), style={'display':'none'}),
                            html.Div([
                                dbc.InputGroup([
                                    dbc.InputGroupText('Group By ', style={'width':'20%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
                                    html.Div(dcc.Dropdown(id=id('dropdown_groupby_feature'), multi=True, options=[], value=None, persistence=True, style={'color':'black', 'text-align':'center'}), style={'width':'80%'}),
                                ]),
                                dbc.Table([], id=id('table_aggregate_function'), bordered=True, dark=True, hover=True, striped=True, style={'overflow-y': 'auto', 'max-height':'18vh'}),
                                dbc.Col(generate_datatable(id('datatable_aggregate'), height='25vh')),
                            ], style={'display':'none'}, id=id('aggregate_container'))
                        ], id=id('right_content_1'), style={'display':'none'}),

                        
                        # Tab 2 (Metadata)
                        html.Div([], id=id('right_content_2'), style={'display':'none'}),

                        # Tab 3 (Config)
                        html.Div([
                            dbc.InputGroup([
                                dbc.InputGroupText('Data Source Type', style={'width':'30%', 'font-weight':'bold', 'font-size': '13px', 'padding-left':'12px'}),
                                dbc.Select(id('select_upload_method'), options=[
                                    {"label": "File Upload", "value": "fileupload"},
                                    {"label": "Paste Text", "value": "pastetext"},
                                    {"label": "Rest API", "value": "restapi"},
                                    {"label": "GraphQL", "value": "graphql", 'disabled':True},
                                    {"label": "Search Data Catalog", "value": "datacatalog"},
                                ], value='fileupload', style={'text-align':'center', 'font-size':'15px'}),
                            ], style={'margin-bottom':'10px'}),

                            html.Div(generate_manuafilelupload_details(id), style={'display':'none'}, id=id('config_options_fileupload')),
                            html.Div(generate_pastetext(id), style={'display':'none'}, id=id('config_options_pastetext')),
                            html.Div(generate_restapi_details(id), style={'display':'none'}, id=id('config_options_restapi')),
                            html.Div(generate_datacatalog_options(id), style={'display':'none', 'overflow-y': 'auto', 'max-height':'40vh'}, id=id('config_options_datacatalog')),

                            dbc.CardFooter([dbc.Row(dbc.Col(dbc.Button(children='Save', id=id('button_save'), color='warning', style={'width':'100%', 'font-size':'22px'}), width={'size': 8, 'offset': 2}))])
                        ], id=id('right_content_3'), style={'display': 'none'}),

                        # Tab 4 (Graph)
                        dbc.Row([], id=id('right_content_4'), style={'display':'none'}),

                        # Tab 5 (Logs)
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader(html.H6("Logs (TBD)", style={'font-size':'14px', 'font-weight': 'bold', 'text-align':'center', 'margin':'0px'}), style={'padding':'1px', 'margin':'0px'}),
                                dbc.CardBody([], id('log_container')),
                            ], style={'display': 'none'}),
                        ], style={'padding':'1px', 'overflow-y':'auto'}),
                    ], style={'padding':'5px'}),

                ], className='bg-dark', inverse=True, style={'min-height':'89vh', 'max-height':'89vh', 'overflow-y':'auto'}),    
            ], width=6), 
        ]),

        # Left Modal (graph, add_feature)
        dbc.Modal([
            html.Div([
                dbc.ModalHeader('Graph', style={'height':'5vh'}),
                dbc.ModalBody([
                    dcc.Graph(id=id('graph'), style={'height': '32vh'}),
                    html.Div(generate_datatable(id('datatable_graph'), height='20vh'), style={'margin-top':'35px'}),
                    html.Div([
                        html.Div(generate_graph_inputs(id), id=id('graph_inputs'), style={'margin':'10px'}),
                        html.Div([
                            dbc.InputGroup([
                                dbc.InputGroupText("Name", style={'width':'15%', 'font-weight':'bold'}),
                                dbc.Input(id=id('graph_name'), placeholder='Enter Graph Name', style={'text-align':'center'}),
                            ]),
                            dbc.InputGroup([
                                dbc.InputGroupText("Description", style={'width':'15%', 'font-weight':'bold'}),
                                dbc.Textarea(id=id('graph_description'), placeholder='Enter Graph Description', style={'font-size': '12px', 'text-align':'center', 'height':'80px', 'padding': '30px 0'}),
                            ]),
                        ], style={'margin':'10px'}),
                    ], style={'height':'22vh'}),
                ], style={'height':'84vh'}),
                dbc.ModalFooter([
                    dbc.Button('Save Graph', id=id('button_save_graph'), color='primary', style={'width':'100%', 'padding':'0px', 'margin':'1px'})
                ], style={'height':'5vh', 'padding':'2px'}),
            ], id=id('modal_graph'), style={'display':'none'}),

            html.Div([
                dbc.ModalHeader(dbc.ModalTitle("Transform Node"), style={'height':'5vh'}),
                dbc.ModalBody(generate_transform_inputs(id), style={'height':'20vh'}),
                dbc.ModalFooter(dbc.Button('Add Feature', color='warning', id=id('button_add_feature'), style={'width':'100%'})),
                html.Div([], id=id('add_feature_msg'), style={'text-align':'center', 'color':'red'}),
                html.Div([], style={'height':'50vh'}),
            ], id=id('modal_add_feature'), style={'display':'none'}),

        ], id=id('modal_left'), is_open=False, centered=False, backdrop=False),

    ], style={'width':'100%'}),
])


# Generate Right Header 1,2,3
@app.callback(
    Output(id('dataset_name'), 'value'),
    Output(id('multiple_node_header_container'), 'children'),

    Output(id('dropdown_action'), 'value'),
    Output(id('dropdown_action_inputs'), 'options'),
    Output(id('dropdown_action_inputs'), 'value'),
    Output(id('dropdown_action_outputs'), 'options'),
    Output(id('dropdown_action_outputs'), 'value'),

    Output(id('right_header_1'), 'style'),
    Output(id('right_header_2'), 'style'),
    Output(id('right_header_3'), 'style'),
    Output(id('single_node_header_container'), 'style'),
    Output(id('multiple_node_header_container'), 'style'),
    Output(id('action_header_container'), 'style'),
    Output(id('search2'), 'style'),
    Output(id('range_slider_container'), 'style'),
    Output(id('join_details_container'), 'style'),
    Output(id('merge_details_container'), 'style'),

    Input(id('tabs_node'), 'active_tab'),
    Input(id('dropdown_action'), 'value'),

    State(id('cytoscape'), 'selectedNodeData'),
    prevent_initial_call=True
)
def generate_right_header(active_tab, selected_action, selectedNodeData):
    num_selected = len(selectedNodeData)
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    # if num_selected == 0: return no_update
    dataset_name, options_selected_nodes  = no_update, no_update 
    options_inputs, selected_inputs, options_outputs, selected_outputs = no_update, no_update, no_update, no_update
    s1, s2, s3, s4, s5, s6, s7, s8, s9, s10 = ({'display': 'none'}, {'display': 'none'}, {'display': 'none'},
                                            {'display': 'none'}, {'display': 'none'}, {'display': 'none'},
                                            {'display': 'none', 'text-align':'center'}, {'display': 'hidden'}, {'display':'none'}, {'display': 'none'}
                                        )

    if num_selected != 0:
        s1['display'] = 'block'
        s4['display'] = 'block'

    if active_tab == 'tab1':
        s7['display'] = 'block' # Search Bar

        if num_selected == 1:
            if selectedNodeData[0]['type'] == 'action':
                s6['display'] = 'block'
                s4['display'] = 'none'
                project = get_document('project', get_session('project_id'))
                action = get_document('action', selectedNodeData[0]['id'])

                dataset_list = [get_document('dataset', node['id']) for node in project['dataset_list']]

                if triggered != id('dropdown_action'):
                    selected_action = action['name']
                selected_inputs = action['inputs'] if selected_action in ['join', 'merge'] else action['inputs'][0]
                selected_outputs = action['outputs']

                options_inputs = [{'label': d['name'], 'value':d['id']} for d in dataset_list if d['id'] not in action['outputs']]
                options_outputs = [{'label': d['name'], 'value':d['id']} for d in dataset_list if d['id'] not in action['inputs']]

                if selected_action == 'transform':
                    s2['display'] = 'block'
                if selected_action == 'join':
                    s9['display'] = 'block'
                if selected_action == 'merge':
                    s10['display'] = 'block'
                if selected_action == 'aggregate':
                    pass
                
            else:
                s2['display'] = 'block'
                s4['display'] = 'block'
                s8['display'] = 'block' # Range Slider Container
                dataset_name = selectedNodeData[0]['name']

        elif num_selected > 1 and all(node['type'] == 'dataset' for node in selectedNodeData):
            s5['display'] = 'block'
            s4['display'] = 'none'

            options = [{'label': str(i+1) +') '+ node['name'], 'value':node['id']} for i, node in enumerate(selectedNodeData)]
            values = [node['id'] for node in selectedNodeData]
            options_selected_nodes = [dcc.Dropdown(options=options, value=values, multi=True, disabled=True, style={'text-align':'center'})]
    
    if active_tab == 'tab3':
        dataset_name = selectedNodeData[0]['name']

    
    # # Range Slider TODO 
    # Output(id('range_slider'), 'min'),
    # Output(id('range_slider'), 'max'),
    # Output(id('range_slider'), 'value'),
    # range_min = 1
    # range_max = len(data)
    # range_val = [range_min, range_max]
    # data = data[range_val[0]-1:range_val[1]]
           
    return (dataset_name, options_selected_nodes, 
            selected_action, options_inputs, selected_inputs, options_outputs, selected_outputs,
            s1, s2, s3, s4, s5, s6, s7, s8, s9, s10
            )



@app.callback(
    Output(id('button_new_action'), 'disabled'),
    Output(id('button_new_action'), 'outline'),
    Input(id('cytoscape'), 'selectedNodeData'),
)
def toggle_action_button(selectedNodeData):
    if len(selectedNodeData) == 0: return True, True
    if all(node['type'] == 'dataset' for node in selectedNodeData): return False, False
    else: return True, True


@app.callback(
    Output(id('button_remove'), 'disabled'),
    Output(id('button_remove'), 'outline'),
    Input(id('cytoscape'), 'selectedNodeData'),
)
def toggle_remove_button(selectedNodeData):
    if len(selectedNodeData) == 0: return True, True
    if all(node['type'] == 'dataset' and node['is_source'] == 'True' for node in selectedNodeData) or selectedNodeData[0]['type'] == 'action': return False, False
    else: return True, True


# All Cytoscape Related Events
@app.callback(
    Output(id('cytoscape'), 'elements'),
    Output(id('cytoscape'), 'layout'),
    Input(id('dataset_name'), 'value'),

    Input(id('button_execute_action'), 'n_clicks'),
    Input(id('button_add_dataset'), 'n_clicks'),
    Input(id('button_new_action'), 'n_clicks'),
    Input(id('button_remove'), 'n_clicks'),
    Input(id('button_group'), 'n_clicks'),
    Input(id('button_reset_layout'), 'n_clicks'),
    Input(id('button_run_cytoscape'), 'n_clicks'),

    Input(id('transform_store'), 'data'),
    Input(id('aggregate_store'), 'data'),

    State(id('dropdown_action'), 'value'),
    State(id('dropdown_action_inputs'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('cytoscape'), 'elements'),
    State(id('datatable'), 'data'),
    State(id('datatable_aggregate'), 'data'),
    State(id('datatable_aggregate'), 'columns'),
)
def cytoscape_triggers(dataset_name, _1, _2, _3, _4, _5, _6, _7,
                        transform_store, aggregate_store,
                        action_name, action_inputs, selectedNodeData, elements, data, data_agg, columns_agg
):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')
    project = get_document('project', project_id)
    layout = { 'name': 'preset', 'fit': True }

    # Action State
    for a in project['action_list']:
        action = get_document('action', a['id'])
        if action['name'] == 'transform':
            print('ACTION STATE: ', action['state'])
            if action['id'] in transform_store:
                if action['details'] != transform_store[action['id']]:
                    action['state'].append('amber')
                    if len(action['state']) > 2: action['state'].pop(0)
                else:
                    if len(action['state']) == 2:
                        action['state'][1] = action['state'][0]
                upsert('action', action)

    # Change Node Name, Action, Inputs  
    if num_selected == 1:
        node_id = selectedNodeData[0]['id']
        if selectedNodeData[0]['type'] == 'dataset':
            dataset = get_document('dataset', node_id)
        elif selectedNodeData[0]['type'] == 'action':
            action = get_document('action', node_id)
        
        if triggered == id('dataset_name'):
            dataset['name'] = dataset_name
            upsert('dataset', dataset)

        # Execute Action
        elif triggered == id('button_execute_action'):
            action['name'] = action_name
            action['inputs'] = action_inputs if type(action_inputs) is list else [action_inputs]
            dataset_o = get_document('dataset', action['outputs'][0])
            df = json_normalize(data)
            df = df.iloc[1: , :]
            if index_col_name in df: df = df.drop(index_col_name, 1)

            try:
                if action_name == 'join':
                    action['details'] = {'join_method':'left', 'features': []}
                    dataset = merge_metadata(action['inputs'], 'objectMerge')
                    rename_map = {}
                    for i in range(len(dataset['features'])):
                        feature_id = str(uuid.uuid1())
                        rename_map[dataset['features'][i]['id']] = feature_id
                        dataset['features'][i]['id'] = feature_id
                    df.rename(columns=rename_map, inplace=True)
                    dataset_o['features'] = dataset['features']

                elif action_name == 'merge':
                    action['details'] = {'merge_type':'none', 'idRef': 'none'}
                    dataset = merge_metadata(action['inputs'], 'objectMerge')
                    dataset_o['features'] = dataset['features']

                elif action_name == 'transform':
                    action['details'] = transform_store[node_id]
                    dataset_o['features'] = [{
                        'id': f['id'],
                        'name': f['name'],
                        'datatype': f['datatype'],
                        'expectation': [],
                    } for f in transform_store[node_id]['features'] if f['remove'] == False]

                    # # TODO truncate, filter, sort_by
                    # df.iloc[]
                    # dataset_o['filter'] = transform_store[node_id]['features']['others']['filter']
                    # dataset_o['sort_by'] = transform_store[node_id]['features']['others']['sort_by']      

                elif action_name == 'aggregate':
                    action['details'] = aggregate_store[node_id]
                    df = pd.DataFrame(data_agg)
                    df = df.drop(columns=index_col_name, axis=1)
                    row_0 = df.iloc[0].to_dict()
                    df = df.iloc[1: , :]
                    columns_agg = [c for c in columns_agg if c['id'] != index_col_name]
                    dataset_o['features'] = [{
                        'id': c['id'],
                        'name': c['name'],
                        'datatype': row_0[c['id']],
                        'expectation': [],
                    } for c in columns_agg]

                elif action_name == 'impute':
                    pass

                action['state'].append('green')
                if len(action['state']) > 2: action['state'].pop(0)
                upsert('action', action)
                upsert('dataset', dataset_o)
                collection_name_list = [row['name'] for row in client.collections.retrieve()]
                if dataset_o['id'] in collection_name_list:
                    client.collections[dataset_o['id']].delete()
                client.collections.create(generate_schema_auto(dataset_o['id']))
                jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl
                r = client.collections[dataset_o['id']].documents.import_(jsonl, {'action': 'create'})

            except Exception as e:
                print("Exception: ", e)
                action['state'].append('red')
                if len(action['state']) > 2: action['state'].pop(0)
                upsert('action', action)

    # Cytoscape Buttons
    if triggered == id('button_add_dataset'):
        add_dataset(project_id)

    elif triggered == id('button_new_action'):
        if num_selected == 0: return no_update
        if any(node['type'] == 'action' for node in selectedNodeData): return no_update
        source_id_list = [node['id'] for node in selectedNodeData]
        add_action(source_id_list)

    elif triggered == id('button_remove'):
        remove(project_id, selectedNodeData)
    
    elif triggered == id('button_group'):
        pass
        # selected_datasets = [node['id'] for node in selectedNodeData if node['type'] == 'dataset']
        # group_node_id = str(uuid.uuid1())
        # for node in project['group_list']:
        #     if node['id'] in selected_datasets:
        #         pass # add 'parent': node_id to each child node
        # project['group_list'].append({'data': {'id': group_node_id, 'label': 'Group Label'}})
        # upsert('project', project)
    
    elif triggered == id('button_reset_layout'):
        layout = {
            'name': 'breadthfirst',
            'fit': True,
            'roots': [e['data']['id'] for e in elements if 'is_source' in e['data'] and e['data']['is_source'] == 'True'],
        }

    elif triggered == id('button_run_cytoscape'):
        pass

    elements = generate_cytoscape_elements(project_id)

    return elements, layout


# # # Initialize Cytoscape Settings (that cannot be accessed through Dash)
# # app.clientside_callback(
# #     """
# #     function(selectedNodeData) {
# #         console.log(cy.elements)
# #         cy.wheelSensitivity = 1
# #         return ''
# #     }
# #     """,
# #     Output('modal', 'children'),
# #     Input(id('cytoscape'), "selectedNodeData"),
# # )


# Store Cytoscape Position
app.clientside_callback(
    """
    function(n_intervals, position_store) {
        if (position_store == JSON.stringify(cy.nodes().jsons())) {
            return ''
        } else {
            return cy.nodes().jsons()
        }
    }
    """,
    Output(id('cytoscape_position_store'), 'data'),
    Input(id('interval_cytoscape'), 'n_intervals'),
    State(id('cytoscape_position_store'), 'data'),
)

@app.callback(
    Output(id('project_name'), 'children'),
    Input('url', 'pathname'),
)
def display_project_name(pathname):
    project = get_document('project', get_session('project_id'))
    return 'Project: ' + project['id']


@app.callback(
    Output(id("last_saved"), "children"),
    Output(id('cytoscape_position_store_2'), 'data'),
    Input(id('cytoscape_position_store'), "data"),
    State(id('cytoscape_position_store_2'), 'data'),
)
def save_cytoscape_position(position1, position2):
    if position1 is None or position1 == '' or position1 == position2: return no_update


    # Save to Typesense
    project = get_document('project', get_session('project_id'))
    for i in range(len(project['dataset_list'])):
        for p in position1:
            if project['dataset_list'][i]['id'] == p['data']['id']:
                project['dataset_list'][i]['position'] = p['position']
    for i in range(len(project['action_list'])):
        for p in position1:
            if project['action_list'][i]['id'] == p['data']['id']:
                project['action_list'][i]['position'] = p['position']
    upsert('project', project)

    # Get Last saved time
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return f"Last Saved: {dt_string}", position1



# # Modify Action
# @app.callback(
#     Output(id('button_execute_action'), 'disabled'),
#     Input(id('dropdown_action'), 'value'),
#     Input(id('button_execute_action'), 'n_clicks'),
#     State(id('cytoscape'), 'selectedNodeData'),
#     prevent_initial_call=True
# )
# def modify_action(action_name, _, selectedNodeData):
#     if len(selectedNodeData) != 1: return no_update
#     action = get_document('action', selectedNodeData[0]['id'])
#     return True if action['name'] == action_name else False
    
    

@app.callback(
    Output(id('tabs_node'), 'active_tab'),
    Input(id('button_run_restapi'), 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def run_config(n_clicks, selectedNodeData):
    if n_clicks is None: return no_update
    dataset = get_document('dataset', selectedNodeData[0]['id'])
    dataset['upload_details'] = {}
    method = dataset['upload_details']['method']
    url = dataset['upload_details']['url']
    header = dataset['upload_details']['header']
    param =dataset['upload_details']['param']
    body = dataset['upload_details']['body']
    df, details = process_restapi(method, url, header, param, body)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

    # Upsert
    r = client.collections[dataset['id']].documents.import_(jsonl, {'action': 'create'})
    upsert(dataset)
    # update_logs(get_session('project_id'), node['id'], 'Run Config: '+str(details), details['timestamp'])

    return 'tab1'


# Load Dataset Config 
@app.callback(
    Output(id('description'), 'value'),
    Output(id('documentation'), 'value'),
    Output(id('select_upload_method'), 'value'),
    Output(id('dropdown_method'), 'value'),
    Output(id('url'), 'value'),
    Output(id('select_upload_method'), 'disabled'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def populate_dataset_config(active_tab, selectedNodeData):
    if active_tab != 'tab3': return no_update
    description, documentation, upload_method, method, url, disabled = '', '', 'fileupload', 'get', '', False

    dataset = get_document('dataset', selectedNodeData[0]['id'])
    description = dataset['description']
    documentation = dataset['documentation']
    
    if dataset['upload_details'] != {}:
        if dataset['upload_details']['method'] == 'restapi':
            method = dataset['upload_details']['method']
            url = dataset['upload_details']['url']
        if dataset['upload_details']['method'] != {}:
            upload_method = dataset['upload_details']['method']

    return description, documentation, upload_method, method, url, disabled


# Display Node Buttons
@app.callback(
    Output(id('button_open_graph_modal'), 'style'),
    Output(id('button_save_changes'), 'style'),
    Output(id('button_revert_changes'), 'style'),
    Output(id('button_execute_action'), 'style'),

    Output(id('button_add_feature_modal'), 'style'),
    Output(id('button_remove_feature'), 'style'),
    Output(id('button_clear'), 'style'),\
    Output(id('button_display_mode'), 'style'),
    Output(id('button_run_restapi'), 'style'),

    Input(id('tabs_node'), 'active_tab'),
    Input(id('dropdown_action'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),

    State(id('button_open_graph_modal'), 'style'),
    State(id('button_save_changes'), 'style'),
    State(id('button_revert_changes'), 'style'),
    State(id('button_execute_action'), 'style'),

    State(id('button_add_feature_modal'), 'style'),
    State(id('button_remove_feature'), 'style'),
    State(id('button_clear'), 'style'),\
    State(id('button_display_mode'), 'style'),
    State(id('button_run_restapi'), 'style'),
)
def display_node_buttons(active_tab, action_name, selectedNodeData, s1, s2, s3, s4, s5, s6, s7, s8, s9):
    # if active_tab != 'tab1': return no_update
    
    for s in [s1, s2, s3, s4, s5, s6, s7, s8, s9]:
        s['display'] = 'none'

    if len(selectedNodeData) == 1:
        node_type = selectedNodeData[0]['type']
       
        if node_type == 'action':
            action = get_document('action', selectedNodeData[0]['id'])
            action_name = action_name if action_name is not None else action['name']
            # s2['display'] = 'inline-block'
            s3['display'] = 'inline-block'
            s4['display'] = 'inline-block'

            if action_name == 'transform':
                s5['display'], s6['display'], s7['display'] = 'inline-block', 'inline-block', 'inline-block'
            elif action_name == 'merge':
                pass

        elif node_type == 'dataset':
            s1['display'] = 'inline-block'
            s8['display'] = 'inline-block'
            if selectedNodeData[0]['upload_details'] != {}:
                if selectedNodeData[0]['upload_details']['method'] == 'restapi':
                    s9['display'] = 'inline-block'

    else:
        if all(node['type'] == 'dataset' for node in selectedNodeData):
            s8['display'] = 'inline-block'

    return s1, s2, s3, s4, s5, s6, s7, s8, s9


# Enable/Disable Tabs
@app.callback(
    Output(id('tabs_node'), 'children'),
    Input(id('cytoscape'), 'selectedNodeData'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('tabs_node'), 'children'),
)
def enable_disable_tab(selectedNodeData, active_tab, tabs):
    if selectedNodeData is None: return no_update
    num_selected = len(selectedNodeData)
    disabled1, disabled2, disabled3, disabled4, disabled5 = True, True, True, False, False
    if num_selected == 0:
        disabled4, disabled5 = False, False
    elif num_selected == 1:
        if selectedNodeData[0]['type'] == 'action':
            disabled1 = False
            disabled5 = False
        elif selectedNodeData[0]['type'] == 'dataset':
            disabled1 = False
            disabled3 = False
            disabled4 = False
            disabled5 = False
    elif (num_selected > 1 and  all(node['type'] == 'dataset' for node in selectedNodeData)):
        disabled1 = False
    
    tabs[0]['props']['disabled'] = disabled1
    tabs[1]['props']['disabled'] = disabled2
    tabs[2]['props']['disabled'] = disabled3
    tabs[3]['props']['disabled'] = disabled4
    tabs[4]['props']['disabled'] = disabled5

    return tabs

# Set Active Tab
@app.callback(
    Output(id('tabs_node'), 'active_tab'),
    Input(id('cytoscape'), 'selectedNodeData'),
    State(id('tabs_node'), 'active_tab'),
)
def set_active_tab(selectedNodeData, active_tab):
    if selectedNodeData is None: return no_update
    num_selected = len(selectedNodeData)
    active_tab = None
    # if num_selected == 0: 
    #     active_tab = None
    if num_selected == 1:
        if selectedNodeData[0]['type'] == 'action': active_tab = 'tab1'
        elif selectedNodeData[0]['type'] == 'raw' and selectedNodeData[0]['upload_details'] == {}: active_tab = 'tab3'
        else: active_tab = 'tab1' if active_tab is None else active_tab
    elif (num_selected > 1 and all(node['type'] == 'dataset' for node in selectedNodeData) ):
        active_tab = 'tab1' if (active_tab == 'tab3') else active_tab

    return active_tab



# Run & Save Data Source
@app.callback(
    Output(id('tabs_node'), 'active_tab'),
    Input(id('button_save'), 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('select_upload_method'), 'value'),
    State(id('browse_drag_drop'), 'isCompleted'),
    State(id('browse_drag_drop'), 'upload_id'),
    State(id('browse_drag_drop'), 'fileNames'),
    State(id('dropdown_method'), 'value'),
    State(id('url'), 'value'),
    State({'type': id('header_key'), 'index': ALL}, 'value'),
    State({'type': id('header_value'), 'index': ALL}, 'value'),
    State({'type': id('header_value_position'), 'index': ALL}, 'value'),
    State({'type': id('param_key'), 'index': ALL}, 'value'),
    State({'type': id('param_value'), 'index': ALL}, 'value'),
    State({'type': id('param_value_position'), 'index': ALL}, 'value'),
    State({'type': id('body_key'), 'index': ALL}, 'value'),
    State({'type': id('body_value'), 'index': ALL}, 'value'),
    State({'type': id('body_value_position'), 'index': ALL}, 'value'),
)
def upload_data_source(n_clicks_button_save_config,
                    selectedNodeData, upload_type,
                    isCompleted, upload_id, fileNames,                                               # Tabular / JSON 
                    method, url, header_key_list, header_value_list, header_value_position_list, param_key_list, param_value_list, param_value_position_list, body_key_list, body_value_list, body_value_position_list,     # REST API
                    ):
    num_selected = len(selectedNodeData)
    if num_selected == 0: return no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    active_tab = no_update

    if triggered == id('button_save') and n_clicks_button_save_config is not None:
        node_id = selectedNodeData[0]['id']
        project_id = get_session('project_id')

        # Upload Files
        if upload_type == 'fileupload' and fileNames is not None:
            df, details = process_fileupload(upload_id, fileNames[0])
            save_dataset(df, node_id, upload_type, details)
            active_tab = 'tab1'
            
        # Paste Text TODO
        elif upload_type == 'pastetext':
            active_tab = 'tab1'

        # RestAPI
        elif upload_type == 'restapi':
            header = dict(zip(header_key_list, header_value_list))
            param = dict(zip(param_key_list, param_value_list))
            body = dict(zip(body_key_list, body_value_list))
            df, details = process_restapi(method, url, header, param, body)
            save_dataset(df, node_id, upload_type, details)

            # Add Edges if dataset is dependent on other datasets
            if any(header_value_position_list) != None or any(param_value_position_list) or any(body_value_position_list):
                for header in header_value_position_list:
                    if header is not None and header != '': 
                        source_id = header[0]['id']
                        add_edge(project_id, source_id, node_id)

                for param in param_value_position_list:
                    if param is not None and param != '': 
                        source_id = param[0]['id']
                        add_edge(project_id, source_id, node_id)
                for body in body_value_position_list:
                    if body is not None and body != '': 
                        source_id = body[0]['id']
                        add_edge(project_id, source_id, node_id)
                        
            active_tab = 'tab1'
   
    return active_tab









# Toggle Multiple Inputs # TODO 5
@app.callback(
    # Output(id('dropdown_action_inputs'), 'value'),
    Output(id('dropdown_action_inputs'), 'multi'),
    Input(id('dropdown_action'), 'value'),
    State(id('dropdown_action_inputs'), 'value'),
)
def toggle_multi_inputs(action_val, selected_inputs):
    if action_val is None: return no_update
    elif action_val in ['join', 'merge']:
        multi = True
        selected_inputs = no_update
    else:
        if type(selected_inputs) is list and len(selected_inputs) > 0: selected_inputs = selected_inputs[0]
        else: selected_inputs
        multi = False
    return multi


# Update Dataset Particulars (Name, Description, Documentation)
@app.callback(
    Output('modal', 'children'),
    Input(id('description'), 'value'),
    Input(id('documentation'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    prevent_initial_call=True,
)
def update_node_particulars(description, documentation, selectedNodeData):
    if len(selectedNodeData) != 1: return no_update
    dataset = get_document('dataset', selectedNodeData[0]['id'])
    dataset['description'] = description
    dataset['documentation'] = documentation
    upsert('dataset', dataset)



# Right Content Display
@app.callback(
    Output(id('right_content_0'), 'style'),
    Output(id('right_content_1'), 'style'),
    Output(id('right_content_2'), 'style'),
    Output(id('right_content_3'), 'style'),
    Output(id('right_content_4'), 'style'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('right_content_0'), 'style'),
    State(id('right_content_1'), 'style'),
    State(id('right_content_2'), 'style'),
    State(id('right_content_3'), 'style'),
    State(id('right_content_4'), 'style'),
)
def generate_right_content_display(active_tab, style0, style1, style2, style3, style4):
    style0['display'], style1['display'], style2['display'], style3['display'], style4['display']= 'none', 'none', 'none', 'none', 'none'
    if active_tab == 'tab1': style1['display'] = 'block'
    elif active_tab == 'tab2': style2['display'] = 'block'
    elif active_tab == 'tab3': style3['display'] = 'block'
    elif active_tab == 'tab4': style4['display'] = 'block'
    else: style0['display'] = 'block'

    return style0, style1, style2, style3, style4


# # Generate Right Content (tab3)
# @app.callback(
#     Output(id('right_content_3'), 'children'),
#     Input(id('cytoscape'), 'selectedNodeData'),
# )
# def generate_right_content(selectedNodeData):
#     pass





# # Node Logs
# @app.callback(
#     Output(id('log_container'), 'children'),
#     Input(id('tabs_node'), 'active_tab'),
#     State(id('cytoscape'), 'selectedNodeData'),
# )
# def generate_right_content_5(active_tab, selectedNodeData):
#     num_selected = len(selectedNodeData)
#     project_id = get_session('project_id')
#     project = get_document('project', project_id)
#     if num_selected == 0: node_id_list = project['logs'].keys()
#     else: node_id_list = [node['id'] for node in selectedNodeData]

#     log_list = []
#     for node_id in node_id_list:
#         if node_id in project['logs']:
#             for node_log_id in project['logs'][node_id]:
#                 node_log = get_document('logs', node_log_id)
#                 datetime_obj = datetime.strptime(node_log['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
#                 date = datetime_obj.strftime("%d %M %Y")
#                 time = datetime_obj.strftime("%H:%M")
#                 log_list.append([date, time, 'action', 'details'])

#     df = pd.DataFrame(log_list, columns=['Date', 'Time', 'Log Type', 'Details'])
#     columns = [{"name": i, "id": i} for i in df.columns]
#     datatable = datatable = generate_datatable(id('datatable_logs'), df.to_dict('records'), columns, height='18vh', sort_action='native', filter_action='native')

#     return datatable



@app.callback(
    Output(id('dropdown_groupby_feature'), 'options'),
    Output(id('dropdown_groupby_feature'), 'value'),
    Input(id('dropdown_action'), 'value'),
    Input(id('datatable'), 'selected_columns'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def generate_groupby_options(selected_action, selected_columns, selectedNodeData):
    if len(selectedNodeData) != 1 or selectedNodeData[0]['type'] != 'action': return no_update
    if selected_action != 'aggregate': return no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    dataset, df = get_action_source(selectedNodeData[0]['id'])
    options = [{'label': f['name'], 'value': f['id']} for f in dataset['features']]

    if triggered == id('dropdown_action'): value = options[0]['value']
    elif triggered == id('datatable'): value = selected_columns

    return options, value

@app.callback(
    Output(id('table_aggregate_function'), 'children'),
    Input(id('dropdown_groupby_feature'), 'value'),
    State(id('cytoscape'), 'selectedNodeData')
)
def generate_agg_table(groupby_features, selectedNodeData):
    if len(selectedNodeData) != 1 or selectedNodeData[0]['type'] != 'action': return no_update
    dataset, df = get_action_source(selectedNodeData[0]['id'])
    features = list(dataset['features'])
    features = [f for f in features if f['id'] not in groupby_features]
    
    # aggregate_button_id_list = [id('button_agg_function{}'.format(i)) for i in range(len(aggregate_button_name_list))]
    aggregate_button_list = []

    # table_header = [html.Thead(html.Tr([html.Th("Feature", style={'width':'25%'}), html.Th("Function")]))]
    table_body = [html.Tbody([html.Tr([
        html.Td(features[j]['name'], style={'padding':'1px', 'text-align':'center'}),
        html.Td([dbc.Button(
            name, id={'type': id('button_agg_function'), 'index': features[j]['id']+'_'+aggregate_button_name_list[i]},
            n_clicks=0, color='light', size='sm', outline=True, style={'width':'80px', 'height': '25px'}
        ) for i, name in enumerate(aggregate_button_name_list)], style={'padding':'1px', 'text-align':'center'}),
    ]) for j in range(len(features))])]

    return table_body


# Outline true/false Buttons onclick
@app.callback(
    Output({'type': id('button_agg_function'), 'index': MATCH}, 'outline'),
    Input({'type': id('button_agg_function'), 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True,
)
def agg_function_style(n_clicks):
    if n_clicks == 0: return no_update
    if n_clicks % 2 == 0: return True
    else: return False


@app.callback(
    Output(id('datatable_aggregate'), 'data'),
    Output(id('datatable_aggregate'), 'columns'),
    Output(id('aggregate_store'), 'data'),
    Input('url', 'pathname'),
    Input(id('dropdown_groupby_feature'), 'value'),
    Input({'type': id('button_agg_function'), 'index': ALL}, 'n_clicks'),
    State({'type': id('button_agg_function'), 'index': ALL}, 'id'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('aggregate_store'), 'data'),
    prevent_initial_call=True,
)
def generate_datatable_aggregate(_, groupby_features, n_clicks_list, id_list, selectedNodeData, aggregate_store):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

    if triggered == '':
        project = get_document('project', get_session('project_id'))
        aggregate_store = {}
        for a in project['action_list']:
            action_id = a['id']
            action = get_document('action', action_id)
            aggregate_store[action_id] = action['details']

        return no_update, no_update, aggregate_store
    else:
        if all(n_click == 0 for n_click in n_clicks_list): return no_update

        selected_list = [n_clicks % 2 == 1 for n_clicks in n_clicks_list]
        agg_feature_function_dict = {}
        for i in range(len(selected_list)):
            if selected_list[i] == True:
                feature, agg_func = id_list[i]['index'].rsplit('_', 1)
                if feature in agg_feature_function_dict: agg_feature_function_dict[feature].append(agg_func)
                else: agg_feature_function_dict[feature] = [agg_func]

        action_id = selectedNodeData[0]['id']
        if action_id not in aggregate_store: aggregate_store[action_id] = {}
        aggregate_store[action_id] = {'groupby_features': groupby_features, 'aggregate_dict': agg_feature_function_dict}

        # If no function/groupby features selected
        if agg_feature_function_dict == {} or groupby_features == []:
            return [], [], aggregate_store

        # Group by, Aggregate
        action_id = selectedNodeData[0]['id']
        dataset, df = get_action_source(action_id)
        df_agg = df.groupby(groupby_features, as_index=False).agg(agg_feature_function_dict)

        # Columns
        columns = [{'id':index_col_name, 'name': [index_col_name, ''], 'selectable': False}]
        feature_id_name_dict = {f['id']: f['name'] for f in dataset['features']}
        feature_id_list = []
        for header1, header2 in df_agg.columns:
            feature_id = str(uuid.uuid1())
            feature_id_list.append(feature_id)
            columns += [{"id": feature_id, 'name': [feature_id_name_dict[header1], header2], 'selectable': False}]

        df_agg.droplevel(level=1, axis=1)
        df_agg.columns = feature_id_list
        features = [{'id': f_id, 'name':'', 'datatype': str(d)} for f_id, d in df_agg.convert_dtypes().dtypes.apply(lambda x: x.name.lower()).to_dict().items()]
        df_agg, _, _ = generate_datatable_data(df_agg, features)

        return df_agg.to_dict('records'), columns, aggregate_store



@app.callback(
    Output(id('join_features_container'), 'children'),
    Input(id('dropdown_action_inputs'), 'value'),
)
def display_merge_details(action_inputs):
    if action_inputs is None: return no_update
    if type(action_inputs) != list: action_inputs = [action_inputs]

    dataset_list = [get_document('dataset', dataset_id) for dataset_id in action_inputs]
    join_inputs = []
    for dataset in dataset_list:
        join_inputs += [
                    dbc.InputGroup([
                        dbc.InputGroupText(dataset['name'], style={'width':'25%'}),
                        dbc.Select(
                            options=[{'label': f['name'], 'value':f['id']} for f in dataset['features']],
                            value= dataset['features'][0]['id'] if len(dataset['features']) > 0 else None, 
                            id={'type': id('join_keys'), 'index': dataset['id']}, style={'text-align':'center'}
                        ),
                    ])
                ]
            
    return join_inputs


@app.callback(
    Output(id('merge_idRef_container'), 'children'),
    Input(id('merge_type'), 'value'),
    Input(id('dropdown_action_inputs'), 'value'),
)
def display_merge_details(merge_type, action_inputs):
    if action_inputs is None: return no_update
    if type(action_inputs) != list: action_inputs = [action_inputs]

    dataset_list = [get_document('dataset', dataset_id) for dataset_id in action_inputs]
    merge_inputs = []
    
    if merge_type == 'arrayMergeByIndex':
        pass
    elif merge_type == 'objectMerge':
        pass
    if merge_type == 'arrayMergeById':
        for dataset in dataset_list:
            merge_inputs += [
                dbc.InputGroup([
                    dbc.InputGroupText(dataset['name'], style={'width':'25%'}),
                    dbc.Select(
                        options=[{'label': f['name'], 'value':f['id']} for f in dataset['features']],
                        value= dataset['features'][0]['id'] if len(dataset['features']) > 0 else None, 
                        id={'type': id('merge_idRef'), 'index': dataset['id']}, style={'text-align':'center'}
                    ),
                ])
            ]
            
    return merge_inputs







# Right Content 1
@app.callback(
    Output(id('datatable_container'), 'children'),
    Output(id('datatable_container'), 'style'),
    Output(id('aggregate_container'), 'style'),
    Input(id('tabs_node'), 'active_tab'),
    Input(id('dropdown_action'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def generate_right_content_1(active_tab, selected_action, selectedNodeData):
    if active_tab != 'tab1': return no_update
    num_selected = len(selectedNodeData)
    datatable_container = no_update
    s1, s2 = {'display':'none'}, {'display':'none'}
    
    if num_selected == 1:
        node_type = selectedNodeData[0]['type']
        if node_type == 'action':
            if selected_action == 'join':
                s1['display'] = 'block'
                datatable_container = generate_datatable(id('datatable'), height='60vh')
            elif selected_action == 'merge':
                s1['display'] = 'block'
                datatable_container = generate_datatable(id('datatable'), height='60vh')
            elif selected_action == 'transform':
                s1['display'] = 'block'
                datatable_container = generate_datatable(id('datatable'), cell_editable=True, height='65vh', sort_action='native', filter_action='native', col_selectable='multi')
            elif selected_action == 'aggregate':
                s1['display'] = 'block'
                s2['display'] = 'block'
                datatable_container = generate_datatable(id('datatable'), height='20vh', col_selectable='multi')
            elif selected_action == 'impute': datatable_container = []
            else: datatable_container = []
        elif node_type == 'dataset':
            s1['display'] = 'block'
            datatable_container = generate_datatable(id('datatable'), height='75vh')
    elif num_selected > 1 and all(node['type'] == 'dataset' for node in selectedNodeData):
        s1['display'] = 'block'
        datatable_container = generate_datatable(id('datatable'), height='70vh')

    return datatable_container, s1, s2






    
    


# @app.callback(
#     Output(id('modal_add_feature'), 'is_open'),
#     Input(id('button_add_feature_modal'), 'n_clicks'),
#     prevent_initial_call=True
# )
# def select_function(n_clicks):
#     return True






# Load Dataset Config Options
@app.callback(
    Output(id('config_options_fileupload'), 'style'),
    Output(id('config_options_pastetext'), 'style'),
    Output(id('config_options_restapi'), 'style'),
    Output(id('config_options_datacatalog'), 'style'),
    Output(id('table_datacatalog'), 'children'),
    Input(id('select_upload_method'), 'value'),
    Input(id('search_datacatalog'), 'value'),
    State(id('button_save'), 'style'),
)
def load_dataset_options(upload_method, search_datacatalog_value, button_save_style):
    style1, style2, style3, style4 = {'display':' none'}, {'display':' none'}, {'display':' none'}, {'display':' none'}
    datacatalog_search_results = no_update

    if upload_method == 'fileupload':  style1 = {'display':' block'}
    elif upload_method == 'pastetext': style2 = {'display': 'block'}
    elif upload_method == 'restapi': style3 = {'display':' block'}
    elif upload_method == 'datacatalog':
        style4 = {'display':' block'}
        datacatalog_search_results = generate_datacatalog_table(id, search_datacatalog_value)

    return style1, style2, style3, style4, datacatalog_search_results



# Toggle button Tabular
@app.callback(
    Output(id('button_display_mode'), 'outline'),
    Input(id('button_display_mode'), 'n_clicks'),
)
def toggle_button_display_mode(n_clicks):
    if n_clicks is None: return no_update
    if n_clicks % 2 == 0: return True
    else: return False


# Add/Remove Headers, Params, Body
@app.callback(
    Output(id('header_div'), 'children'),
    Output(id('param_div'), 'children'),
    Output(id('body_div'), 'children'),
    Input(id('cytoscape'), 'tapNodeData'),
    Input(id('button_add_header'), 'n_clicks'),
    Input(id('button_remove_header'), 'n_clicks'),
    Input(id('button_add_param'), 'n_clicks'),
    Input(id('button_remove_param'), 'n_clicks'),
    Input(id('button_add_body'), 'n_clicks'),
    Input(id('button_remove_body'), 'n_clicks'),
    State(id('header_div'), 'children'),
    State(id('param_div'), 'children'),
    State(id('body_div'), 'children'),
    prevent_initial_call=True
)
def load_restapi_options(tapNodeData, _, _2, _3, _4, _5, _6, header_div, param_div, body_div):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '' or triggered == None: return no_update
    
    if triggered == id('cytoscape') and tapNodeData['type'] == 'dataset':
        header_div, param_div, body_div = [], [], []
        dataset = get_document('dataset', tapNodeData['id'])
        if dataset['upload_details'] != {}:
            if dataset['upload_details']['method'] == 'restapi':
                for k, v in dataset['details']['header'].items():
                    header_div += generate_restapi_options(id, 'header', len(header_div), k, v)
                for k, v in dataset['details']['param'].items():
                    param_div += generate_restapi_options(id, 'param', len(param_div), k, v)
                for k, v in dataset['details']['body'].items():
                    body_div += generate_restapi_options(id, 'body', len(body_div), k, v)
    
    # Add
    if 'add' in triggered:
        if triggered == id('button_add_header'): header_div += generate_restapi_options(id, 'header', len(header_div))
        elif triggered == id('button_add_param'): param_div += generate_restapi_options(id, 'param', len(param_div))
        elif triggered == id('button_add_body'): body_div += generate_restapi_options(id, 'body', len(body_div))

    # Remove
    if 'remove' in triggered:
        if triggered == id('button_remove_header'): header_div = header_div[:-1]
        elif triggered == id('button_remove_param'): param_div = param_div[:-1]
        elif triggered == id('button_remove_body'): body_div = body_div[:-1]

    # Remove n_clicks
    try:
        for i in range(len(header_div)):
            header_div[i]['props']['children'][0]['props']['children'][2]['props']['n_clicks'] = None
        for i in range(len(param_div)):
            param_div[i]['props']['children'][0]['props']['children'][2]['props']['n_clicks'] = None
        for i in range(len(body_div)):
            body_div[i]['props']['children'][0]['props']['children'][2]['props']['n_clicks'] = None

    except Exception as e:
        print('Exception: ', e)

    return header_div, param_div, body_div



for option_type in ['header', 'param', 'body']:
    # Open Modal
    @app.callback(
        Output({'type':id('{}_modal'.format(option_type)), 'index': MATCH}, 'is_open'),
        Input({'type':id('button_{}_value'.format(option_type)), 'index': MATCH}, 'n_clicks')
    )
    def button_open_modal(n_clicks):
        if n_clicks is None or n_clicks == 0: return no_update
        return True

    # Populate Existing Data Source dropdown
    @app.callback(
        Output({'type': id('{}_datasource_list'.format(option_type)), 'index': MATCH}, 'options'),
        Output({'type': id('{}_datasource_list'.format(option_type)), 'index': MATCH}, 'value'),
        Input({'type': id('button_{}_value'.format(option_type)), 'index': MATCH}, 'n_clicks'),
        State(id('cytoscape'), 'selectedNodeData'),
    )
    def populate_datasource_dropdown(n_clicks, selectedNodeData):
        project = get_document('project', get_session('project_id'))
        project_name_list = [{'label': get_document('dataset', dataset_id)['name'], 'value': dataset_id} for dataset_id in [p['id'] for p in project['dataset_list']]]
        return project_name_list, ''

    # Populate Datatable
    @app.callback(
        Output({'type': id('{}_value_datatable'.format(option_type)), 'index': MATCH}, 'data'),
        Output({'type': id('{}_value_datatable'.format(option_type)), 'index': MATCH}, 'columns'),
        Input({'type': id('{}_datasource_list').format(option_type), 'index': MATCH}, 'value'),
    )
    def populate_datatable(dataset_id):
        if dataset_id == '' or dataset_id is None: return no_update
        df = get_dataset_data(dataset_id)
        columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]
        return df.to_dict('records'), columns

    # Get Selected Inputs from datatable into input
    @app.callback(
        Output({'type':id('{}_value'.format(option_type)), 'index': MATCH}, 'value'),
        Output({'type':id('{}_value'.format(option_type)), 'index': MATCH}, 'valid'),
        Output({'type':id('{}_value_position'.format(option_type)), 'index': MATCH}, 'value'),
        Input({'type':id('{}_value_datatable'.format(option_type)), 'index': MATCH}, 'selected_cells'),
        Input({'type':id('{}_value'.format(option_type)), 'index': MATCH}, 'value'),
        State({'type':id('{}_value_datatable'.format(option_type)), 'index': MATCH}, 'data'),
        State({'type': id('{}_datasource_list'.format(option_type)), 'index': MATCH}, 'value'),
    )
    def select_input(selected_cells, value, data, dataset_id):
        if callback_context.triggered[0]['prop_id'] == '.': return no_update
        if selected_cells is None: return no_update
        if len(selected_cells) <= 0: return no_update
        triggered = json.loads(callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0])
        out, valid, cell_position_list = no_update, None, no_update

        if 'datatable' in triggered['type']:
            out = ''
            if selected_cells is not None:
                df = json_normalize(data)
                for cell in selected_cells:
                    out = out + str(df.loc[cell['row'], cell['column_id']]) + ','
                out = out[:-1]
                valid = True
                cell_position_list = [{'row': cell['row'], 'col': cell['column_id'], 'id': dataset_id} for cell in selected_cells]
            else:
                valid = None

        elif 'value' in triggered['type']:
            cell_position_list = ''
                
        return out, valid, cell_position_list





# Generate List of feature dropdown
@app.callback(
    Output(id('dropdown_arithmeticfeature1'), 'options'),
    Output(id('dropdown_arithmeticfeature2'), 'options'),

    Output(id('dropdown_comparisonfeature1'), 'options'),
    Output(id('dropdown_comparisonfeature2'), 'options'),

    Output(id('dropdown_aggregatefeatures'), 'options'),
    Output(id('dropdown_formatdatefeature'), 'options'),
    Output(id('dropdown_cumulativefeature'), 'options'),

    Output(id('dropdown_slidingwindow_feature'), 'options'),
    Output(id('dropdown_slidingwindow_size'), 'options'),

    Output(id('dropdown_shift_size'), 'options'),
    Output(id('dropdown_shift_feature'), 'options'),

    Input(id('button_add_feature_modal'), 'n_clicks'),
    State(id('datatable'), 'columns'),
    State(id('datatable'), 'data'),
    prevent_initial_call=True
)
def generate_feature_dropdown(n_clicks, features, data):
    if n_clicks is None: return no_update
    options = [{'label': f['name'], 'value': f['id']} for f in features]
    options = [o for o in options if o['label'] != index_col_name]
    options_slidingwindow_size = [{'label': i, 'value': i} for i in range(2, len(data)-1)]
    options_shift_size = [{'label': i, 'value': i} for i in range(2, len(data)-1)]
    options_custom = options + [{'label': 'Custom Input', 'value': '_custom'}]
    return options, options_custom, options, options_custom, options, options, options, options, options_slidingwindow_size, options_shift_size, options




# Display Custom Inputs
@app.callback(
    Output(id('custom_input'), 'style'),
    Input(id('dropdown_arithmeticfeature2'), 'value'),
    Input(id('dropdown_comparisonfeature2'), 'value'),
    Input(id('dropdown_function_type'), 'value'),
    State(id('custom_input'), 'style'),
)
def display_custom_inputs(arithmetic_feature, comparison_feature, function_type, style):
    style['display'] = 'none'
    if arithmetic_feature == '_custom' and function_type == 'arithmetic': style['display'] = 'flex'
    if comparison_feature == '_custom' and function_type == 'comparison': style['display'] = 'flex'
    return style


# Function Input Visibility
@app.callback(
    Output(id('arithmetic_inputs'), "style"),
    Output(id('comparison_inputs'), "style"),
    Output(id('aggregate_inputs'), "style"),
    Output(id('slidingwindow_inputs'), "style"),
    Output(id('formatdate_inputs'), "style"),
    Output(id('cumulative_inputs'), "style"),
    Output(id('shift_inputs'), "style"),
    Output(id('condition'), "style"),
    Input(id('dropdown_function_type'), "value"),
    State(id('arithmetic_inputs'), "style"),
    State(id('comparison_inputs'), "style"),
    State(id('aggregate_inputs'), "style"),
    State(id('slidingwindow_inputs'), "style"),
    State(id('formatdate_inputs'), "style"),
    State(id('cumulative_inputs'), "style"),
    State(id('shift_inputs'), "style"),
    State(id('condition'), "style"),
)
def function_input_style(function_type, style1, style2, style3, style4, style5, style6, style7, condition_style):
    style1['display'], style2['display'], style3['display'], style4['display'], style5['display'], style6['display'], style7['display'] = 'none', 'none', 'none', 'none', 'none', 'none', 'none'
    condition_style['display'] = 'none'
    if function_type == 'arithmetic': style1['display'] = 'flex'
    elif function_type == 'comparison': style2['display'] = 'flex'
    elif function_type == 'aggregate': style3['display'] = 'flex'
    elif function_type == 'slidingwindow': style4['display'] = 'flex'
    elif function_type == 'formatdate': style5['display'] = 'flex'
    elif function_type == 'cumulative': style6['display'] = 'flex'
    elif function_type == 'shift': style7['display'] = 'flex'

    if function_type in ['arithmetic', 'comparison']:
        condition_style['display'] = 'flex'
        
    return style1, style2, style3, style4, style5, style6, style7, condition_style



# Select Datatable Column
@app.callback(
    Output(id('datatable'), "selected_columns"),
    Input(id('datatable'), "active_cell"),
    State(id('datatable'), "selected_columns"),
)
def auto_select_column(active_cell, selected_columns):
    if active_cell is None: return no_update
    active_column = active_cell['column_id']
    if active_column in selected_columns: selected_columns.remove(active_column)
    else: selected_columns.append(active_column)
    return selected_columns






# Right Content Datatable
@app.callback(
    Output(id('datatable'), 'data'),
    Output(id('datatable'), 'columns'),
    Output(id('datatable'), "dropdown_data"),
    Output(id('datatable'), "style_data_conditional"),
    Output(id('datatable'), "style_header_conditional"),

    Input(id('datatable_container'), 'children'),
    Input(id('dropdown_action_inputs'), 'value'),
    Input(id('transform_store'), "data"),
    
    Input(id('join_method'), 'value'),
    Input({'type': id('join_keys'), 'index': ALL}, 'value'),
    Input(id('merge_type'), 'value'),
    Input({'type': id('merge_idRef'), 'index': ALL}, 'value'),

    Input(id('range_slider'), 'value'),
    Input(id('search2'), 'value'),

    State(id('dropdown_action'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('datatable'), 'data'),
    State(id('datatable'), 'columns'),
)
def datatable_triggers(_, action_inputs, transform_store, 
                        join_method, join_keys, merge_type, merge_idRef_list,
                        range_val, search_val,
                        selected_action, selectedNodeData, data, columns
):
    num_selected = len(selectedNodeData)
    triggered = callback_context.triggered[0]['prop_id']
    if num_selected == 0: return no_update
    if triggered == '.': return no_update
    style_data_conditional, style_header_conditional = [], []
    
    show_datatype_dropdown = False
    renamable = False
    merge_idRef_list = None if merge_idRef_list is None else ['/'+idRef for idRef in merge_idRef_list]
    
    # print("\ntriggered", merge_idRef_list)
    # pprint(callback_context.triggered)
    
    if num_selected == 1:
        node_id = selectedNodeData[0]['id']
        node_type = selectedNodeData[0]['type']

        if node_type == 'action':
            dataset, df = get_action_source(node_id, action_inputs, 'join', join_method, join_keys)
            features = dataset['features']

            # Add/Style Session Changes
            if selected_action == 'transform':
                renamable = True
                show_datatype_dropdown = True
                if node_id in transform_store:
                    store = transform_store[node_id]
                    
                    if 'features' in store:
                        for feature in store['features']:
                            if feature['new'] == True:
                                df[feature['id']] = feature['data']
                                style_data_conditional += [{"if": {"column_id": feature['id']}, "backgroundColor": "#8B8000"}]
                                features.append(feature)
                            
                            feature_saved = None
                            for f in dataset['features']:
                                if f['id'] == feature['id']:
                                    feature_saved = f
                            if feature_saved is not None:
                                if feature['remove'] == True:
                                    style_data_conditional += [{"if": {"column_id": feature['id']}, "backgroundColor": "red"}]
                                    style_header_conditional += [{"if": {"column_id": feature['id']}, "backgroundColor": "red"}]
                                if feature['name'] != feature_saved['name']:
                                    for i in range(len(features)):
                                        if features[i]['id'] == feature['id']:
                                            features[i]['name'] = feature['name']
                                    style_header_conditional += [{"if": {"column_id": feature['id']}, "backgroundColor": "#8B8000"}]
                                if feature['datatype'] != feature_saved['datatype']:
                                    for i in range(len(features)):
                                        if features[i]['id'] == feature['id']:
                                            features[i]['datatype'] = feature['datatype']
                                    style_data_conditional += [{"if": {"column_id": feature['id'], 'row_index': 0}, "backgroundColor": "#8B8000"}]
                    
                    # # TODO modify df to fit these values
                    # store['others']['filter']
                    # store['others']['truncate']
                    # store['others']['sort_by']

        else:
            dataset = get_document('dataset', node_id)
            df = get_dataset_data(node_id)
            features = dataset['features']

    elif num_selected > 1 and all(node['type'] == 'dataset' for node in selectedNodeData):
        # inputs = [node['id'] for node in selectedNodeData]
        # dataset = merge_metadata(inputs, 'objectMerge')
        # df = merge_dataset_data(inputs, merge_type, merge_idRef_list)
        # features = dataset['features']
        pass

    else:
        return no_update
    
    # Filter Range
    # Search Value

    # Process into Datatable format
    if not df.empty:
        df, columns, dropdown_data = generate_datatable_data(df, features, show_datatype_dropdown=show_datatype_dropdown, renamable=renamable)
        data = df.to_dict('records')
        print(df)
        print(len(df))
    else:
        print("Empty Dataframe")
        data, dropdown_data = [], []
    
    return data, columns, dropdown_data, style_data_conditional, style_header_conditional



# Transform Node
@app.callback(
    Output(id('transform_store'), 'data'),
    Output(id('add_feature_msg'), 'children'),
    # Output(id('datatable'), 'selected_columns'),
    Input('url', 'pathname'),
    Input(id('right_content_1'), 'style'),
    Input(id('button_save_changes'), 'n_clicks'),
    Input(id('button_revert_changes'), 'n_clicks'),
    Input(id('button_execute_action'), 'n_clicks'),
    Input(id('button_add_feature'), 'n_clicks'),
    Input(id('button_remove_feature'), 'n_clicks'),
    Input(id('button_clear'), 'n_clicks'),
    Input(id('datatable'), 'data_previous'),

    State(id('datatable'), 'sort_by'),
    State(id('datatable'), 'filter_query'),
    
    State(id('dropdown_action'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('datatable'), 'data'),
    State(id('datatable'), 'columns'),
    State(id('datatable'), 'active_cell'),
    State(id('datatable'), 'selected_columns'),
    State(id('dropdown_function_type'), 'value'),
    State(id('transform_store'), 'data'),
    State(id('feature_name'), 'value'),

    State(id('dropdown_arithmeticfunction'), 'value'),
    State(id('dropdown_arithmeticfeature1'), 'value'),
    State(id('dropdown_arithmeticfeature2'), 'value'),

    State(id('dropdown_comparisonfunction'), 'value'),
    State(id('dropdown_comparisonfeature1'), 'value'),
    State(id('dropdown_comparisonfeature2'), 'value'),

    State(id('dropdown_aggregate_function'), 'value'),
    State(id('dropdown_aggregatefeatures'), 'value'),

    State(id('dropdown_slidingwindow_function'), 'value'),
    State(id('dropdown_slidingwindow_size'), 'value'),
    State(id('dropdown_slidingwindow_feature'), 'value'),

    State(id('dropdown_dateformat'), 'value'),
    State(id('dropdown_formatdatefeature'), 'value'),

    State(id('dropdown_cumulativefeature'), 'value'),

    State(id('dropdown_shift_size'), 'value'),
    State(id('dropdown_shift_feature'), 'value'),
)
def transform_triggers(_, _1, _2, _3, _4, _5, _6, _7, data_previous,
                sort_by, filter_query,
                selected_action, selectedNodeData, data, columns, active_cell, selected_columns, function_type, transform_store, feature_name,
                func1, f1a, f1b,
                func2, f2a, f2b,
                func3, f3a,
                func4, f4a, f4b,
                f5a, f5b,
                f6a,
                f7a, f7b
):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    add_feature_msg = ''

    # print('\ntriggered: ')
    # pprint(callback_context.triggered)

    # On Page Load instantiate transform_store 
    if triggered == '':
        project = get_document('project', get_session('project_id'))
        transform_store = {}
        for a in project['action_list']:
            action_id = a['id']
            action = get_document('action', action_id)
            transform_store[action_id] = action['details']
            
    else:
        if len(selectedNodeData) != 1 or selectedNodeData[0]['type'] != 'action' or selected_action != 'transform':  return no_update
        if data == []: return no_update
        df = json_normalize(data)
        df.set_index(index_col_name, inplace=True)
        columns = [c for c in columns if c['name'] != index_col_name]
        action_id = selectedNodeData[0]['id']
        action = get_document('action', action_id)
        
        if action_id not in transform_store: transform_store[action_id] = {}
        store = transform_store[action_id]
        if 'features'   not in store:   store['features'] = []
        if 'others'     not in store:   store['others'] = {}
        feature_id_list = [f['id'] for f in store['features']]
        for c in columns:
            if c['id'] not in feature_id_list:
                store['features'].append({
                    'id':                   c['id'],
                    'name':                 '',
                    'datatype':             '',
                    'new':                  False,
                    'data':                 None,
                    'remove':               False,
                    'condition':            [],
                    'function':             '',
                    'dependent_features':   []
                })

        if 'truncate'   not in store['others']: store['others']['truncate'] = []
        if 'filter'     not in store['others']: store['others']['filter'] = {}
        if 'sort_by'    not in store['others']: store['others']['sort_by'] = {}
        
        # Store Feature Name, Datatype, sort_by column
        row_0 = df.iloc[0].to_dict()
        columns2 = {c['id']:c['name'] for c in columns}

        for i in range(len(store['features'])):
            feature_id = store['features'][i]['id']
            store['features'][i]['name'] = columns2[feature_id]
            store['features'][i]['datatype'] = row_0[feature_id]
            
            # Condition
        
        # Truncate, Filter, Sort_by
        # store['others']['truncate'] = ___
        store['others']['filter'] = filter_query
        store['others']['sort_by'] = sort_by

        # Add Feature
        if triggered == id('button_add_feature'):
            df2 = df[1:].reset_index()
            try:
                if feature_name in [c['name'] for c in columns]:
                    store = no_update
                    add_feature_msg = 'Feature Name Exist!'

                elif function_type == 'arithmetic':
                    for feature in store['features']:
                        if feature['id'] == f1a: datatype1 = feature['datatype']
                        if feature['id'] == f1b: datatype2 = feature['datatype']
                    f1 = df2[f1a].astype(datatype1, errors='raise')
                    f2 = df2[f1b].astype(datatype2, errors='raise')

                    if func1 == 'add': data = f1 + f2
                    elif func1 == 'subtract': data = f1 - f2
                    elif func1 == 'divide': data = f1 / f2
                    elif func1 == 'multiply': data = f1 * f2
                    elif func1 == 'exponent': data = f1 ** f2
                    elif func1 == 'modulus': data = f1 % f2

                    transform_func = func1
                    datatype_out = 'int64'
                    # dependent_features = [f1, f2]
                    
                elif function_type == 'comparison':
                    for feature in store['features']:
                        if feature['id'] == f2a: datatype1 = feature['datatype']
                        if feature['id'] == f2b: datatype2 = feature['datatype']

                    f1 = df2[f2a].astype(datatype1, errors='raise')
                    f2 = df2[f2b].astype(datatype2, errors='raise')

                    if func2 == 'gt':   data = f1.gt(f2, fill_value='')
                    elif func2 == 'lt': data = f1.lt(f2, fill_value='')
                    elif func2 == 'ge': data = f1.ge(f2, fill_value='')
                    elif func2 == 'le': data = f1.le(f2, fill_value='')
                    elif func2 == 'eq': data = f1.eq(f2, fill_value='')
                    elif func2 == 'ne': data = f1.ne(f2, fill_value='')

                    transform_func = func2
                    datatype_out = 'bool'
                    # dependent_features = [f1, f2]

                elif function_type == 'aggregate':
                    pass
                elif function_type == 'slidingwindow':
                    pass
                elif function_type == 'formatdate':
                    pass
                elif function_type == 'cumulative':
                    pass
                elif function_type == 'shift':
                    pass

            except Exception as e:
                store = no_update
                add_feature_msg = str(e)
                print(traceback.format_exc())
            
            if store is not no_update:
                store['features'].append({
                    'id':       str(uuid.uuid1()),
                    'name':     feature_name,
                    'datatype': datatype_out,
                    'new':      True,
                    'data':     list(data),
                    'remove':   False,
                    'condition':[],
                    'function': transform_func,
                    'dependent_features': []
                })

        # Remove Feature
        elif triggered == id('button_remove_feature') and active_cell is not None:
            selected_feature_id = active_cell['column_id']

            for i in range(len(store['features'])):
                if store['features'][i]['id'] == selected_feature_id:
                    if store['features'][i]['new'] == True:
                        del store['features'][i]
                    else:
                        store['features'][i]['remove'] = not store['features'][i]['remove']

            # selected_columns = []

        # Clear Session
        elif triggered == id('button_clear'):
            print("Clear Transform Session")
            transform_store[action_id] = {}
            transform_store[action_id]['features'] = []
            transform_store[action_id]['others'] = {}

        # Revert to Last Saved Data
        elif triggered == id('button_revert_changes'):
            transform_store[action_id] = action['details']

    return transform_store, add_feature_msg






# # Add Feature (Comparison)
# @app.callback(
#     Output(id('new_feature_store'), 'data'),
#     Input(id('button_add_feature'), 'n_clicks'),
#     State(id('dropdown_function_type'), 'value'),
#     State(id('datatable'), 'data'),
#     State(id('dropdown_comparisonfunction'), 'value'),
#     State(id('dropdown_comparisonfeature1'), 'value'),
#     State(id('dropdown_comparisonfeature2'), 'value'),
#     prevent_initial_call=True,
# )
# def add_feature2(n_clicks, function_type, data, function, feature1, feature2):
#     if n_clicks is None: return no_update
#     if function_type != 'comparison': return no_update
#     df = pd.DataFrame(data)
#     try:
#         if function == 'gt': feature = df[feature1].gt(df[feature2])
#         elif function == 'lt': feature = df[feature1].lt(df[feature2])
#         elif function == 'ge': feature = df[feature1].ge(df[feature2])
#         elif function == 'le': feature = df[feature1].le(df[feature2])
#         elif function == 'eq': feature = df[feature1].eq(df[feature2])
#         elif function == 'ne': feature = df[feature1].ne(df[feature2])
#     except: 
#         feature = 'error'

#     return feature

# # Add Feature (aggregate)
# @app.callback(
#     Output(id('new_feature_store'), 'data'),
#     Input(id('button_add_feature'), 'n_clicks'),
#     State(id('dropdown_function_type'), 'value'),
#     State(id('dropdown_aggregate_function'), 'value'),
#     State(id('datatable'), 'data'),
#     State(id('dropdown_aggregatefeatures'), 'value'),
#     prevent_initial_call=True,
# )
# def add_feature3(n_clicks, function_type, func, data, features):
#     if n_clicks is None: return no_update
#     if function_type != 'aggregate': return no_update
#     df = pd.DataFrame(data)
#     try:
#         if func == 'sum': feature = df[features].sum(axis=1)
#         elif func == 'avg': feature = df[features].mean(axis=1)
#         elif func == 'min': feature = df[features].min(axis=1)
#         elif func == 'max': feature = df[features].max(axis=1)
#     except:
#         feature = 'error'
#     return feature

# # Add Feature (Sliding Window)
# @app.callback(
#     Output(id('new_feature_store'), 'data'),
#     Input(id('button_add_feature'), 'n_clicks'),
#     State(id('dropdown_function_type'), 'value'),
#     State(id('datatable'), 'data'),
#     State(id('dropdown_slidingwindow_function'), 'value'),
#     State(id('dropdown_slidingwindow_size'), 'value'),
#     State(id('dropdown_slidingwindow_feature'), 'value'),
#     prevent_initial_call=True,
# )
# def add_feature4(n_clicks, function_type, data, func, window_size, feature):
#     if n_clicks is None: return no_update
#     if function_type != 'slidingwindow': return no_update
#     df = pd.DataFrame(data)
#     try:
#         window = df[feature].rolling(int(window_size))
#         if func == 'sum': feature = window.sum()
#         elif func == 'avg': feature = window.mean()
#         elif func == 'min': feature = window.min()
#         elif func == 'max': feature = window.max()
#     except:
#         feature = 'error'

#     return feature

# # Add Feature (Format Date)
# @app.callback(
#     Output(id('new_feature_store'), 'data'),
#     Input(id('button_add_feature'), 'n_clicks'),
#     State(id('dropdown_function_type'), 'value'),
#     State(id('datatable'), 'data'),
#     State(id('dropdown_dateformat'), 'value'),
#     State(id('dropdown_formatdatefeature'), 'value'),
#     prevent_initial_call=True,
# )
# def add_feature5(n_clicks, function_type, data, date_format, feature):
#     if n_clicks is None: return no_update
#     if function_type != 'formatdate': return no_update
#     df = pd.DataFrame(data)

#     try:
#         pass
#     except:
#         pass

#     return feature

# # Add Feature (Cumulative)
# @app.callback(
#     Output(id('new_feature_store'), 'data'),
#     Input(id('button_add_feature'), 'n_clicks'),
#     State(id('dropdown_function_type'), 'value'),
#     State(id('datatable'), 'data'),
#     State(id('dropdown_cumulativefeature'), 'value'),
#     prevent_initial_call=True,
# )
# def add_feature5(n_clicks, function_type, data, feature):
#     if n_clicks is None: return no_update
#     if function_type != 'cumulative': return no_update
#     df = pd.DataFrame(data)
#     feature = df[feature].cumsum()

#     return feature

# # Add Feature (Shift)
# @app.callback(
#     Output(id('new_feature_store'), 'data'),
#     Input(id('button_add_feature'), 'n_clicks'),
#     State(id('dropdown_function_type'), 'value'),
#     State(id('datatable'), 'data'),
#     State(id('dropdown_shift_size'), 'value'),
#     State(id('dropdown_shift_feature'), 'value'),
#     prevent_initial_call=True,
# )
# def add_feature7(n_clicks, function_type, data, size, features):
#     if n_clicks is None: return no_update
#     if function_type != 'shift': return no_update
#     df = pd.DataFrame(data)
#     feature = df[features].shift(int(size))

#     return feature.squeeze()




''' Plot Graph '''

# Generate Right Content (tab4)
@app.callback(
    Output(id('right_content_4'), 'children'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def generate_right_content(active_tab, selectedNodeData):
    if active_tab != 'tab4': return no_update
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')
    project = get_document('project', project_id)
    right_content_4 = []

    if num_selected == 0: dataset_id_list = project['graph_dict'].keys()
    else: dataset_id_list = [dataset['id'] for dataset in selectedNodeData]

    for dataset_id in dataset_id_list:
        if dataset_id in project['graph_dict']:
            for graph_id in project['graph_dict'][dataset_id]:
                graph = get_document('graph', graph_id)
                df = get_dataset_data(dataset_id)
                if graph['type'] == 'line': fig = get_line_figure(df, graph['x'], graph['y'])
                elif graph['type'] == 'bar': fig = get_bar_figure(df, graph['x'], graph['y'], graph['barmode'])
                elif graph['type'] == 'pie': fig = get_pie_figure(df, graph['names'], graph['values'])
                elif graph['type'] == 'scatter': fig = get_scatter_figure(df, graph['x'], graph['y'], graph['color'])

                right_content_4 += [
                    dbc.Col([
                        dbc.Card([
                            dbc.Button(dbc.CardHeader(graph['name']), id={'type': id('button_graph_id'), 'index': graph_id}, value=graph_id),
                            dbc.CardBody([
                                dcc.Graph(figure=fig, style={'height':'20vh'}),
                            ]),
                        ], color='primary', inverse=True, style={})
                    ], style={'width':'98%', 'display':'inline-block', 'text-align':'center', 'margin':'3px 3px 3px 3px', 'height':'25vh'})
                ]
        
    return right_content_4


# @app.callback(
#     Output(id('graph_id_store'), 'data'),
#     Input(id('button_open_graph_modal_existing'), 'n_clicks'),
#     Input(id('button_open_graph_modal_existing'), 'value')
# )
# def open_existing_graph(n_clicks):
#     if n_clicks is None: return no_update
#     return 

@app.callback(
    Output(id('graph_id_store'), 'data'),
    Input({'type': id('button_graph_id'), 'index': ALL}, 'n_clicks'),
    State({'type': id('button_graph_id'), 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def load_graph(a, b):
    if len(callback_context.triggered) != 1: return no_update
    triggered = json.loads(callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0])
    graph_id = triggered['index']
    return graph_id 
    

# Left Modal
@app.callback(
    Output(id('modal_left'), 'is_open'),
    Output(id('modal_graph'), 'style'),
    Output(id('modal_add_feature'), 'style'),
    Output(id('tabs_node'), 'active_tab'),
    Input(id('button_open_graph_modal'), 'n_clicks'),
    Input(id('button_add_feature_modal'), 'n_clicks'),
    Input(id('graph_id_store'), 'data'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('modal_left'), 'is_open'),
    prevent_initial_call=True
)
def button_chart(n_clicks1, n_clicks2, graph_id, selectedNodeData, is_open):
    if len(callback_context.triggered) != 1: return no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    active_tab = no_update
    s1, s2 = {'display':'none'}, {'display':'none'}
    is_open = not is_open

    if triggered == id('button_open_graph_modal') or triggered == id('graph_id_store'):
        if triggered == id('button_open_graph_modal'): store_session('graph_id', '')
        else: store_session('graph_id', graph_id)
        active_tab = 'tab4'
        s1['display'] = 'block'

    elif triggered == id('button_add_feature_modal'):
        # is_open = not is_open
        s2['display'] = 'block'
    
    else:
        is_open = False

    return is_open, s1, s2, active_tab


# Generate Graph Inputs from Graph Session
@app.callback(
    Output(id('dropdown_graph_type'), 'value'),
    Output(id('line_x'), 'options'),
    Output(id('line_y'), 'options'),
    Output(id('line_x'), 'value'),
    Output(id('line_y'), 'value'),

    Output(id('bar_x'), 'options'),
    Output(id('bar_y'), 'options'),
    Output(id('bar_x'), 'value'),
    Output(id('bar_y'), 'value'),
    Output(id('bar_barmode'), 'value'),

    Output(id('pie_names'), 'options'),
    Output(id('pie_values'), 'options'),
    Output(id('pie_names'), 'value'),
    Output(id('pie_values'), 'value'),

    Output(id('scatter_x'), 'options'),
    Output(id('scatter_y'), 'options'),
    Output(id('scatter_color'), 'options'),
    Output(id('scatter_x'), 'value'),
    Output(id('scatter_y'), 'value'),
    Output(id('scatter_color'), 'value'),

    Output(id('datatable_graph'), 'data'),
    Output(id('datatable_graph'), 'columns'),

    Output(id('graph_name'), 'value'),
    Output(id('graph_description'), 'value'),

    Input(id('modal_graph'), 'style'),
    State(id('cytoscape'), 'selectedNodeData')
)
def generate_graph_inputs_options(style, selectedNodeData):
    if style['display'] == 'none': return no_update
    if len(selectedNodeData) != 1: return no_update
    return graph_inputs_options_callback(selectedNodeData[0]['id'], get_session('graph_id'))

# Make Selected Graph type Inputs visible
@app.callback(
    Output(id('line_input_container'), 'style'),
    Output(id('bar_input_container'), 'style'),
    Output(id('pie_input_container'), 'style'),
    Output(id('scatter_input_container'), 'style'),
    Input(id('dropdown_graph_type'), 'value'),
    Input('url', 'pathname')
)
def generate_graph_inputs_visibility(graph_type, pathname):
    return graph_input_visibility_callback(graph_type)

# Graph Callbacks
@app.callback(
    Output(id('graph'), 'figure'),
    Input(id('line_input_container'), 'style'),
    Input(id('bar_input_container'), 'style'),
    Input(id('pie_input_container'), 'style'),
    Input(id('scatter_input_container'), 'style'),

    Input(id('line_x'), 'value'),
    Input(id('line_y'), 'value'),
    
    Input(id('bar_x'), 'value'),
    Input(id('bar_y'), 'value'),
    Input(id('bar_barmode'), 'value'),
    
    Input(id('pie_names'), 'value'),
    Input(id('pie_values'), 'value'),
    
    Input(id('scatter_x'), 'value'),
    Input(id('scatter_y'), 'value'),
    Input(id('scatter_color'), 'value'),

    State(id('datatable_graph'), 'data'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def display_graph(style1, style2, style3, style4, 
                        line_x, line_y,
                        bar_x, bar_y, bar_barmode,
                        pie_names, pie_values,
                        scatter_x, scatter_y, scatter_color,
                        data, selectedNodeData):
    if len(selectedNodeData) == 0: return no_update
    df = pd.DataFrame(data)
    dataset = get_document('dataset', selectedNodeData[0]['id'])
    labels = {f['id']:f['name'] for f in dataset['features']}
    if style1['display'] != 'none':
        return get_line_figure(df, line_x, line_y, labels)
    elif style2['display'] != 'none':
        return get_bar_figure(df, bar_x, bar_y, bar_barmode)
    elif style3['display'] != 'none':
        return get_pie_figure(df, pie_names, pie_values)
    elif style4['display'] != 'none':
        return get_scatter_figure(df, scatter_x, scatter_y, scatter_color)

# Save Graph
@app.callback(
    Output(id('modal_left'), 'is_open'),
    Output(id('tabs_node'), 'active_tab'),
    Input(id('button_save_graph'), 'n_clicks'),
    State(id('dropdown_graph_type'), 'value'),
    State(id('graph_inputs'), 'children'),
    State(id('graph_name'), 'value'),
    State(id('graph_description'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def save_graph(n_clicks, graph_type, graph_inputs, name, description, selectedNodeData):
    if n_clicks is None: return no_update

    if graph_type == 'line':
        x = graph_inputs[1]['props']['children'][0]['props']['children'][1]['props']['value']
        y = graph_inputs[1]['props']['children'][0]['props']['children'][3]['props']['children']['props']['value']
        graph = {'type': 'line', 'x': x, 'y': y}

    elif graph_type == 'bar':
        x = graph_inputs[2]['props']['children'][0]['props']['children'][1]['props']['value']
        y = graph_inputs[2]['props']['children'][0]['props']['children'][3]['props']['children']['props']['value']
        barmode = graph_inputs[1]['props']['children'][0]['props']['children'][5]['props']['children']['props']['value']
        graph = {'type': 'bar', 'x': x, 'y': y, 'barmode': barmode }

    elif graph_type == 'pie':
        names = graph_inputs[3]['props']['children'][0]['props']['children'][1]['props']['value']
        values = graph_inputs[3]['props']['children'][0]['props']['children'][3]['props']['value']
        graph = {'type': 'pie', 'names': names, 'values': values }

    elif graph_type == 'scatter':
        x = graph_inputs[4]['props']['children'][0]['props']['children'][1]['props']['value']
        y = graph_inputs[4]['props']['children'][0]['props']['children'][3]['props']['value']
        color = graph_inputs[3]['props']['children'][0]['props']['children'][5]['props']['value']
        graph = {'type': 'scatter', 'x': x, 'y': y, 'color': color}
    
    if get_session('graph_id') == '':
        graph_id = str(uuid.uuid1())
        log_description = 'Create Graph: {}'.format(graph_id)
    else:
        graph_id = get_session('graph_id')
        log_description = 'Update Graph: {}'.format(graph_id)

    project_id = get_session('project_id')
    dataset_id = selectedNodeData[0]['id']
    graph['id'] = graph_id
    graph['name'] = name
    graph['description'] = description
    
    upsert_graph(project_id, dataset_id, graph)
    # update_logs(project_id, dataset_id, log_description + graph_id)

    is_open = False
    return is_open, 'tab4'
""" -------------------------------------------------------------------------------- """