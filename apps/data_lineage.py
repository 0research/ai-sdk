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
from apps.typesense_client import *
import ast
from apps.constants import *
import copy
from pathlib import Path
from datetime import datetime
from dash_extensions import EventListener, WebSocket
from dash_extensions import WebSocket

# import heartrate
# heartrate.trace(browser=True)


app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('data_lineage')
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
        'selector': '.action',
        'style': {
            # 'background-color': 'yellow',
            # 'width': 25,
            # 'height': 25,
            # 'background-image': "/assets/static/api.png"
            'background-color': '#FFFF00',
            'shape': 'rectangle',
            'content': 'data(action_label)'
        }
    },
]

options_merge = [{'label': o, 'value': o} for o in MERGE_TYPES]

layout = html.Div([
    html.Div([
        dcc.Store(id=id('do_cytoscape_reload'), storage_type='session', data=False),
        dcc.Store(id=id('cytoscape_position_store'), storage_type='session', data=[]),
        dcc.Store(id=id('cytoscape_position_store_2'), storage_type='session', data=[]),
        dcc.Store(id=id('new_feature_store'), storage_type='session', data={}),
        dcc.Store(id=id('action_transformnode_session'), storage_type='session', data={}),

        dcc.Interval(id=id('interval_cytoscape'), interval=500, n_intervals=0),
        
        dbc.Row([
            # Left Panel
            dbc.Col([
                html.Div(id=id('last_saved'), style={'display':'inline-block', 'margin':'1px'}),
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button('Execute All', id=id('button_execute'), color='success', disabled=True, style={'margin-right':'2px', 'display':'block'}),
                        dbc.Button('Reset Layout', id=id('button_reset_layout'), color='dark', style={'margin-right':'1px', 'display':'block'}),
                        # html.Button('Hide/Show', id=id('button_hide_show'), color='secondary', style={'margin-right':'1px'}), 
                        dbc.DropdownMenu(label="Action", children=[
                            dbc.DropdownMenuItem('New Data Source', href='#', id={'type': id('button_new_data_source'), 'index': 0}, style={'background-color':'#00FF00', 'padding':'10px'}),
                            dbc.DropdownMenuItem("Merge", id=id('button_merge'), href='#', style={'background-color':'yellow', 'padding':'10px', 'text-align':'center', 'display':'none'}),
                            dbc.DropdownMenuItem('Transform', id=id('button_transform'), href='#', className='action_dropdown', style={'text-align':'center'}),
                            # dbc.DropdownMenuItem('Impute Data', href='/apps/impute_data', className='action_dropdown'),
                            # dbc.DropdownMenuItem(divider=True),
                            dbc.DropdownMenuItem('Remove', href='#', id=id('button_remove'), style={'background-color':'#FF7F7F', 'padding':'10px', 'text-align':'center', 'display':'none'}),
                            dbc.DropdownMenuItem('Group', id=id('button_group'), href='#', className='group_nodes', style={'background-color':'#00FF00', 'padding':'10px', 'text-align':'center', 'display':'none'}),
                        ], id=id('dropdown_cytoscape_action'), size='lg', color='warning', style={'display':'inline-block', 'margin':'1px'}),        
                    ]),
                    dbc.Spinner(html.Div(id="loading-output"), color="danger"),
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
                                style={'height': '800px','width': '100%'},
                                stylesheet=cytoscape_stylesheet)
            ], width=6),

            # Right Panel
            dbc.Col([
                html.Div([
                    html.Div(dbc.Tabs([
                        dbc.Tab(label="Data", tab_id="tab1", disabled=True),
                        dbc.Tab(label="Metadata", tab_id="tab2", disabled=True),
                        dbc.Tab(label="Config", tab_id="tab3", disabled=True),
                        dbc.Tab(label="Graph", tab_id="tab4", disabled=True),
                        dbc.Tab(label="Summary", tab_id="tab6", disabled=False),
                    ], id=id("tabs_node")), style={'float':'left', 'text-align':'left', 'display':'inline-block'}),

                    html.Div([
                        dbc.Button("Run (Last run: <TODO>)", id=id('button_run_config'), color='warning', style={'display': 'none'}),
                    #     dbc.Button(html.I(n_clicks=0, className='fas fa-chart-area'), id=id('button_chart'), disabled=True, className='btn btn-success', style={'margin-left':'1px', 'display': 'none'}),
                    #     dbc.Button(html.I(n_clicks=0, className='fas fa-times'), id=id('button_remove'), disabled=True, className='btn btn-danger', style={'margin-left':'1px', 'display':'none'}),
                        dbc.Tooltip('Run Config', target=id('button_run_config')),
                    #     dbc.Tooltip('Chart', target=id('button_chart')),
                    #     dbc.Tooltip('Remove Action or Raw Dataset', target=id('button_callapi')),
                    ], style={'float':'right', 'text-align':'right', 'display':'inline-block'}),
                ], style={'display':'inline-block', 'width':'100%'}),
                  
                dbc.Card([
                    # Header 1 (All Tabs)
                    dbc.CardHeader(id=id('right_header_1'), style={'text-align':'center', 'font-size':'13px', 'font-weight':'bold', 'float':'left', 'width':'100%'}),

                    # Header 2 (Tab 1 only)
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([dbc.Input(id=id('search_json'), placeholder='Search', style={'text-align':'center'})], width=5),
                            dbc.Col([
                                dcc.RangeSlider(
                                    id=id('range'),
                                    value=[],
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                            ], width=3),
                            dbc.Col([
                                dbc.Button(html.I(className='fas fa-plus-circle'), id=id('button_add_feature_modal'), color='light', outline=True),
                                dbc.Button(html.I(className='fas fa-trash'), id=id('button_remove_feature'), color='danger', outline=True),
                                dbc.Button(html.I(className='fa fa-fast-backward'), id=id('button_default'), color='primary', outline=True),
                                dbc.Button(html.I(className='fas fa-eraser'), id=id('button_clear'), color='info', outline=True),
                                dbc.Button(html.I(className='fa fa-table'), color='secondary', outline=True, id=id('button_display_mode'), n_clicks=0),
                                dbc.Button(html.I(className='fas fa-arrow-circle-right'), id=id('button_execute_action'), color='warning', outline=True, style={'display':'none'}),
                                dbc.Tooltip('Add Feature', target=id('button_add_feature_modal')),
                                dbc.Tooltip('Remove Feature', target=id('button_remove_feature')),
                                dbc.Tooltip('Revert Changes', target=id('button_default')),
                                dbc.Tooltip('Clear All Changes', target=id('button_clear')),
                                dbc.Tooltip('View in Tabular Format', target=id('button_display_mode')),
                                dbc.Tooltip('Execute Action', target=id('button_execute_action')),
                            ], width=4, style={'text-align':'right'}),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Select(options=options_merge, value=options_merge[0]['value'], id=id('merge_type'), style={'text-align':'center'}),
                                dbc.Select(options=[], value=None, id=id('merge_idRef'), style={'text-align':'center', 'display':'none'}),
                            ], id=id('merge_type_container'), style={'display':'none'}, width=12),
                        ])
                    ], id=id('right_header_2'), style={'display':'none', 'font-size':'14px'}),

                    # Header 3 (Tab 1)
                    dbc.CardHeader([
                        dbc.InputGroup([
                            dbc.InputGroupText('Action', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
                            dbc.Select(id=id('dropdown_action'), options=[], value=None, disabled=True, style={'text-align':'center', 'width':'70%'}),
                        ]),
                        dbc.InputGroup([
                            dbc.InputGroupText('Inputs', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
                            html.Div(dcc.Dropdown(id=id('dropdown_action_inputs'), options=[], value=None, multi=False, disabled=True), style={'width':'70%', 'text-align':'center'}),
                        ]),
                    ], id=id('right_header_3'), style={'display':'none', 'font-size':'14px'}),

                    # Header 4 (Tab 3)
                    dbc.CardHeader([
                        dbc.InputGroup([
                            dbc.InputGroupText('Description', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
                            dbc.Textarea(id=id('description'), placeholder='Enter Dataset Description', style={'height':'50px', 'text-align':'center'}, persistence=True, persistence_type='session'),
                        ]),
                        dbc.InputGroup([
                            dbc.InputGroupText('Documentation', style={'width':'30%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'12px'}),
                            dbc.Input(id=id('documentation'), placeholder='Enter Documentation URL (Optional) ', style={'height':'40px', 'min-width':'120px', 'text-align':'center'}, persistence=True, persistence_type='session'),
                        ]),
                    ], id=id('right_header_4'), style={'display':'none', 'font-size':'14px'}),
                    
                    
                    # Right Content 0 (No Active Tab)
                    html.Div([], id=id('right_content_0'), style={'display':'none'}),

                    # Right Content Tab 1 (Data)
                    html.Div(generate_datatable(id('datatable')), id=id('right_content_1'), style={'display':'none'}),
                    
                    # Right Content Tab 2 (Metadata)
                    html.Div([], id=id('right_content_2'), style={'display':'none'}),

                    # Right Body Tab 3 (Config)
                    html.Div([
                        dbc.InputGroup([
                            dbc.InputGroupText('Data Source Type', style={'width':'30%', 'font-weight':'bold', 'font-size': '13px', 'padding-left':'12px'}),
                            dbc.Select(id('select_upload_type'), options=[
                                {"label": "File Upload", "value": "raw_fileupload"},
                                {"label": "Paste Text", "value": "raw_pastetext"},
                                {"label": "Rest API", "value": "raw_restapi"},
                                {"label": "GraphQL", "value": "raw_graphql", 'disabled':True},
                                {"label": "Search Data Catalog", "value": "raw_datacatalog"},
                            ], value='raw_fileupload', style={'text-align':'center', 'font-size':'15px'}),
                        ], id=id('dropdown_datasourcetype_container'), style={'margin-bottom':'10px', 'display': 'none'}),

                        html.Div(generate_manuafilelupload_details(id), style={'display':'none'}, id=id('config_options_fileupload')),
                        html.Div(generate_pastetext(id), style={'display':'none'}, id=id('config_options_pastetext')),
                        html.Div(generate_restapi_details(id), style={'display':'none'}, id=id('config_options_restapi')),
                        html.Div(generate_datacatalog_options(id), style={'display':'none', 'overflow-y': 'auto', 'max-height':'500px'}, id=id('config_options_datacatalog')),

                        dbc.CardFooter([dbc.Row(dbc.Col(dbc.Button(children='Save', id=id('button_save'), color='warning', style={'width':'100%', 'font-size':'22px'}), width={'size': 8, 'offset': 2}))])
                    ], id=id('right_content_3'), style={'display': 'none'}),

                    # Right Body Tab 4 (Graph)
                    dbc.Row([
                        dbc.Col(dbc.Button(children='Plot Graph', id=id('button_add_graph'), color='warning', style={'width':'100%', 'font-size':'22px'}), width={"size": 8, "offset": 2}),
                    ], id=id('right_content_4'), style={'display':'none'}),

                    
                    # Right Body Tab 6 (Summary)
                    dbc.Row([
                        dbc.InputGroup([
                            dbc.InputGroupText('Group By ', style={'width':'20%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
                            html.Div(dcc.Dropdown(id=id('dropdown_groupby_feature'), multi=True, options=[], value=None, persistence=True, style={'color':'black', 'text-align':'center'}), style={'width':'80%'}),
                        ]),
                        dbc.Table([], id=id('table_aggregate_function'), bordered=True, dark=True, hover=True, striped=True, style={'overflow-y': 'auto', 'height':'350px'}),

                        dbc.Col(generate_datatable(id('datatable_aggregate'), height='400px')),

                    ], id=id('right_content_5'), style={'display':'none', 'padding':'20px'}),
                ], className='bg-dark', inverse=True, style={'min-height':'580px', 'max-height':'580px', 'overflow-y':'auto'}),

                # Logs
                html.Div([
                    dbc.Card([
                        dbc.CardHeader(html.H6("Logs (TBD)", style={'font-size':'14px', 'font-weight': 'bold', 'text-align':'center', 'margin':'0px'}), style={'padding':'1px', 'margin':'0px'}),
                        dbc.CardBody([], id('log_container')),
                    ], className='bg-dark', inverse=True),
                ], style={'padding':'1px', 'height':'200px', 'overflow-y':'auto'}),
                
            ], width=6),

            
        ]),

        # Modal (view dataset)
        dbc.Modal(id=id('modal_dataset'), size='xl'),

        # Modal Select Function
        dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Transform Node")),
                dbc.ModalBody(generate_transform_node_inputs(id)),
                dbc.ModalFooter(dbc.Button('Add Feature', color='warning', id=id('button_add_feature'), style={'width':'100%'})),
            ],
            id=id('modal_transform_node'),
            is_open=False,
            backdrop=False,
            style={'margin-left':'60px !important'}
        ),

    ], style={'width':'100%'}),
])

# @app.callback(
#     Output(id('dropdown_cytoscape_action'), 'children'),
#     Input(id('cytoscape'), 'selectedNodeData'),
# )
# def generate_cytoscape_action(selectedNodeData):
#     if selectedNodeData is None: return no_update
#     num_selected = len(selectedNodeData)
#     action_list = []

#     if num_selected == 0:
#         action_list +[
            
#         ]
#     if num_selected == 1:
#         action_list += [
            
#         ]
#     else:
#         action_list += [
            
#         ]
    

#     return action_list

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
    Input(id("interval_cytoscape"), "n_intervals"),
    State(id('cytoscape_position_store'), 'data'),
)

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
    for i in range(len(project['node_list'])):
        for p in position1:
            if project['node_list'][i]['id'] == p['data']['id']:
                project['node_list'][i]['position'] = p['position']
    upsert('project', project)

    # Get Last saved time
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return f"Last Saved: {dt_string}", position1


# Only display Run Config if Selected Node is a RestAPI
@app.callback(
    Output(id('button_run_config'), 'style'),
    Input(id('cytoscape'), 'selectedNodeData'),
    State(id('button_run_config'), 'style'),
)
def enable_run_button(selectedNodeData, style):
    if selectedNodeData is None: return no_update
    if len(selectedNodeData) == 1 and selectedNodeData[0]['type'] == 'raw_restapi':
        style['display'] = 'block'
    else:
        style['display'] = 'none'
    return style

@app.callback(
    Output(id('tabs_node'), 'active_tab'),
    Input(id('button_run_config'), 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def run_config(n_clicks, selectedNodeData):
    if n_clicks is None: return no_update
    node = get_document('node', selectedNodeData[0]['id'])
    method = node['details']['method']
    url = node['details']['url']
    header = node['details']['header']
    param =node['details']['param']
    body = node['details']['body']
    df, details = process_restapi(method, url, header, param, body)
    jsonl = df.to_json(orient='records', lines=True) # Convert to jsonl

    # Upsert
    r = client.collections[node['id']].documents.import_(jsonl, {'action': 'create'})
    # upsert(node)
    update_node_log(get_session('project_id'), node['id'], 'Run Config: '+str(details), details['timestamp'])

    return 'tab1'


# Load Dataset Config 
@app.callback(
    Output(id('description'), 'value'),
    Output(id('documentation'), 'value'),
    Output(id('select_upload_type'), 'value'),
    Output(id('dropdown_method'), 'value'),
    Output(id('url'), 'value'),
    Output(id('select_upload_type'), 'disabled'),
    Input(id('cytoscape'), 'tapNodeData'),
)
def populate_dataset_config(tapNodeData):
    if tapNodeData is None: return no_update
    description, documentation, method, url, disabled = '', '', 'get', '', False
    
    if tapNodeData['id'] in get_all_collections():
        dataset = get_document('node', tapNodeData['id'])
        description = dataset['description']
        documentation = dataset['documentation']
        if dataset['type'] == 'raw':
            dataset_type = 'raw_fileupload'
        elif dataset['type'] == 'raw_restapi':
            method = dataset['details']['method']
            url = dataset['details']['url']
            dataset_type = dataset['type']
        elif dataset['type'] == 'processed':
            dataset_type = ''
            disabled = True
        else:
            dataset_type = dataset['type']
    else:
        dataset_type = 'raw_fileupload'
    return description, documentation, dataset_type, method, url, disabled



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
    disabled1, disabled2, disabled3, disabled4, disabled5 = True, True, True, True, True
    
    if num_selected == 0: 
        disabled1, disabled2, disabled3, disabled4, disabled5 = True, True, True, False, False
    elif num_selected == 1:
        if not selectedNodeData[0]['type'].startswith('action') and selectedNodeData[0]['type'] != 'raw':
            disabled1, disabled2, disabled3, disabled4, disabled5 = False, False, False, False, False
    elif (num_selected > 1 and 
            all(not node['type'].startswith('action') for node in selectedNodeData) and
            all(node['type'] != 'raw' for node in selectedNodeData)
            ):
        disabled1, disabled2, disabled3, disabled4, disabled5 = False, False, True, False, False
    
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

    if num_selected == 0: 
        active_tab = None
    elif num_selected == 1:
        if selectedNodeData[0]['type'] == 'raw': active_tab = 'tab3'
        elif selectedNodeData[0]['type'].startswith('action'): active_tab = 'tab1'
        else: active_tab = 'tab1' if active_tab is None else active_tab
    elif (num_selected > 1 and 
            all(not node['type'].startswith('action') for node in selectedNodeData) and
            all(node['type'] != 'raw' for node in selectedNodeData)
            ):
        active_tab = 'tab1' if (active_tab == 'tab3') else active_tab

    return active_tab



# Run & Save Data Source
@app.callback(
    Output(id('tabs_node'), 'active_tab'),
    Input(id('button_save'), 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('select_upload_type'), 'value'),
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
        if upload_type == 'raw_fileupload' and fileNames is not None:
            df, details = process_fileupload(upload_id, fileNames[0])
            save_data_source(df, upload_type, details)
            active_tab = 'tab1'
            
        # Paste Text TODO
        elif upload_type == 'raw_pastetext':
            active_tab = 'tab1'

        # RestAPI
        elif upload_type == 'raw_restapi':
            header = dict(zip(header_key_list, header_value_list))
            param = dict(zip(param_key_list, param_value_list))
            body = dict(zip(body_key_list, body_value_list))
            df, details = process_restapi(method, url, header, param, body)
            save_data_source(df, upload_type, details)

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



# Right Header 
@app.callback(
    Output(id('right_header_1'), 'children'),
    Output(id('right_header_1'), 'style'),
    Output(id('right_header_2'), 'style'),
    Output(id('right_header_3'), 'style'),
    Output(id('right_header_4'), 'style'),
    Output(id('merge_type_container'), 'style'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def generate_right_header(active_tab, selectedNodeData):
    num_selected = len(selectedNodeData)
    right_header_1 = no_update
    right_header_1_style, right_header_2_style, right_header_3_style, right_header_4_style = {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
    merge_type_container_style = {'display': 'none'}

    # Output based on Number of Nodes Selected
    if num_selected == 0: right_header_1 = [dbc.Input(id=id('node_name'), style={'font-size':'14px', 'text-align':'center', 'display':'none'})]

    elif num_selected == 1:
        right_header_1_style['display'] = 'block'
        right_header_1 = [dbc.Input(id=id('node_name'), value=selectedNodeData[0]['name'], style={'font-size':'14px', 'text-align':'center'})]

        if active_tab == 'tab1': 
            if selectedNodeData[0]['type'].startswith('action'):
                right_header_2_style['display'] = 'block'
                right_header_3_style['display'] = 'block'
            else:
                right_header_2_style['display'] = 'block'
                
        if active_tab == 'tab3':
            right_header_4_style['display'] = 'block'

    elif num_selected > 1:
        right_header_1 = [
            dbc.Input(value='{}) '.format(i+1) + node['name'], disabled=True, style={'margin':'5px', 'text-align':'center'}) for i, node in enumerate(selectedNodeData)
        ] + [dbc.Input(id=id('node_name'), style={'display': 'none'})]

        if all(not node['type'].startswith('action') for node in selectedNodeData) and active_tab == 'tab1':
            right_header_2_style['display'] = 'block'
            merge_type_container_style['display'] = 'block'

    return right_header_1, right_header_1_style, right_header_2_style, right_header_3_style, right_header_4_style, merge_type_container_style



# Update Dataset Particulars (Name, Description, Documentation)
@app.callback(
    Output('modal', 'children'),
    Input(id('node_name'), 'value'),
    Input(id('description'), 'value'),
    Input(id('documentation'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    prevent_initial_call=True,
)
def update_node_particulars(node_name, description, documentation, selectedNodeData):
    if len(selectedNodeData) != 1: return no_update
    node = get_document('node', selectedNodeData[0]['id'])
    node['name'] = node_name
    node['description'] = description
    node['documentation'] = documentation
    upsert('node', node)



# Right Content Display
@app.callback(
    Output(id('right_content_0'), 'style'),
    Output(id('right_content_1'), 'style'),
    Output(id('right_content_2'), 'style'),
    Output(id('right_content_3'), 'style'),
    Output(id('right_content_4'), 'style'),
    Output(id('right_content_5'), 'style'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('right_content_0'), 'style'),
    State(id('right_content_1'), 'style'),
    State(id('right_content_2'), 'style'),
    State(id('right_content_3'), 'style'),
    State(id('right_content_4'), 'style'),
    State(id('right_content_5'), 'style'),
)
def generate_right_content_display(active_tab, style0, style1, style2, style3, style4, style6):
    style0['display'], style1['display'], style2['display'], style3['display'], style4['display'], style6['display'] = 'none', 'none', 'none', 'none', 'none', 'none'
    if active_tab == 'tab1': style1['display'] = 'block'
    elif active_tab == 'tab2': style2['display'] = 'block'
    elif active_tab == 'tab3': style3['display'] = 'block'
    elif active_tab == 'tab4': style4['display'] = 'block'
    elif active_tab == 'tab6': style6['display'] = 'block'
    else: style0['display'] = 'block'

    return style0, style1, style2, style3, style4, style6


# # Generate Right Content (tab3)
# @app.callback(
#     Output(id('right_content_3'), 'children'),
#     Input(id('cytoscape'), 'selectedNodeData'),
# )
# def generate_right_content(selectedNodeData):
#     pass

# Generate Right Content (tab4)
@app.callback(
    Output(id('right_content_4'), 'children'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('right_content_4'), 'children'),
)
def generate_right_content(active_tab, selectedNodeData, right_content_4):
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')
    project = get_document('project', project_id)
    right_content_4 = [right_content_4[0]]

    if num_selected == 0: node_id_list = project['graph_dict'].keys()
    else: node_id_list = [node['id'] for node in selectedNodeData]

    for node_id in node_id_list:
        if node_id in project['graph_dict']:
            for graph_id in project['graph_dict'][node_id]:
                graph = get_document('graph', graph_id)
                if graph['type'] == 'line': fig = get_line_figure(node_id, graph['x'], graph['y'])
                elif graph['type'] == 'bar': fig = get_bar_figure(node_id, graph['x'], graph['y'], graph['barmode'])
                elif graph['type'] == 'pie': fig = get_pie_figure(node_id, graph['names'], graph['values'])
                elif graph['type'] == 'scatter': fig = get_scatter_figure(node_id, graph['x'], graph['y'], graph['color'])

                right_content_4 += [
                    dbc.Col([
                        dbc.Card([
                            dbc.Button(dbc.CardHeader(graph['name']), id={'type': id('button_graph_id'), 'index': graph_id}, value=graph_id, href='/apps/plot_graph'),
                            dbc.CardBody([
                                dcc.Graph(figure=fig, style={'height':'240px'}),
                            ]),
                        ], color='primary', inverse=True, style={})
                    ], style={'width':'98%', 'display':'inline-block', 'text-align':'center', 'margin':'3px 3px 3px 3px', 'height':'310px'})
                ]
        
    return right_content_4



# Generate Right Content (tab5)
@app.callback(
    Output(id('log_container'), 'children'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def generate_right_content(active_tab, selectedNodeData):
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')
    project = get_document('project', project_id)
    if num_selected == 0: node_id_list = project['node_log'].keys()
    else: node_id_list = [node['id'] for node in selectedNodeData]

    log_list = []
    for node_id in node_id_list:
        if node_id in project['node_log']:
            for node_log_id in project['node_log'][node_id]:
                node_log = get_document('node_log', node_log_id)
                datetime_obj = datetime.strptime(node_log['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
                date = datetime_obj.strftime("%d %M %Y")
                time = datetime_obj.strftime("%H:%M")
                log_list.append([date, time, 'action', 'details'])

    df = pd.DataFrame(log_list, columns=['Date', 'Time', 'Action', 'Details'])
    columns = [{"name": i, "id": i} for i in df.columns]
    datatable = datatable = generate_datatable(id('datatable'), df.to_dict('records'), columns, height='150px', sort_action='native', filter_active='native')

    return datatable


# # Right Content (tab6)
# @app.callback(
#     Output(id('dropdown_groupby_feature'), 'options'),
#     Output(id('dropdown_groupby_feature'), 'value'),
#     Input(id('cytoscape'), 'selectedNodeData'),
# )
# def generate_right_content_5(selectedNodeData):
#     if len(selectedNodeData) != 1: return no_update
#     node = get_document('node', get_session('node_id'))
#     options = [{'label': f, 'value': f} for f in node['features'].keys()]

#     return options, options[0]['value']

# @app.callback(
#     Output(id('table_aggregate_function'), 'children'),
#     Input(id('dropdown_groupby_feature'), 'value'),
# )
# def generate_right_content_5(groupby_features):
#     node = get_document('node', get_session('node_id'))
#     feature_list = list(node['features'].keys())
#     feature_list = [f for f in feature_list if f not in groupby_features]
    
#     # aggregate_button_id_list = [id('button_agg_function{}'.format(i)) for i in range(len(aggregate_button_name_list))]
#     aggregate_button_list = []

#     table_header = [html.Thead(html.Tr([html.Th("Feature", style={'width':'25%'}), html.Th("Function")]))]
#     table_body = [html.Tbody([html.Tr([
#         html.Td(feature_list[j]),
#         html.Td([dbc.Button(name, id={'type': id('button_agg_function'), 'index': feature_list[j]+'_'+aggregate_button_name_list[i]}, n_clicks=0, color='primary', outline=True) for i, name in enumerate(aggregate_button_name_list)]),
#     ]) for j in range(len(feature_list))])]
#     table = table_header + table_body

#     return table


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
    Input({'type': id('button_agg_function'), 'index': ALL}, 'n_clicks'),
    State({'type': id('button_agg_function'), 'index': ALL}, 'id'),
    State(id('dropdown_groupby_feature'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    prevent_initial_call=True,
)
def generate_datatable_aggregate(n_clicks_list, id_list, groupby_features, selectedNodeData):
    if all(n_click == 0 for n_click in n_clicks_list): return no_update

    selected_list = [n_clicks % 2 == 1 for n_clicks in n_clicks_list]
    feature_func_dict = {}

    for i in range(len(selected_list)):
        if selected_list[i] == True:
            feature, agg_func = id_list[i]['index'].rsplit('_', 1)
            if feature in feature_func_dict: feature_func_dict[feature].append(agg_func)
            else: feature_func_dict[feature] = [agg_func]

    node_id = selectedNodeData[0]['id']
    df = get_dataset_data(node_id)
    df_agg = df.groupby(groupby_features).sum() # TODO
    # df_agg = df.groupby(groupby_features).agg({feature: ['sum', 'mean']}) # TODO
    columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]

    pprint(feature_func_dict)
    print(df_agg)

    return df_agg.to_dict('records'), columns




# Generate Right Content (tab1)
@app.callback(
    Output(id('button_execute_action'), 'style'),
    Output(id('dropdown_action'), 'options'),
    Output(id('dropdown_action'), 'value'),
    Output(id('dropdown_action_inputs'), 'options'),
    Output(id('dropdown_action_inputs'), 'value'),
    Output(id('right_content_1'), 'children'),
    Output(id('range'), 'min'),
    Output(id('range'), 'max'),
    Output(id('range'), 'value'),
    Output(id('merge_idRef'), 'style'),
    Output(id('merge_idRef'), 'options'),
    Output(id('merge_idRef'), 'value'),
    Input(id('range'), 'value'),
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'value'),
    Input(id('button_display_mode'), 'n_clicks'),
    Input(id('right_content_1'), 'style'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('button_execute_action'), 'style'),
)
def generate_right_content(range_value, merge_type, merge_idRef, n_clicks_display_mode, _, selectedNodeData, button_execute_action_style):
    num_selected = len(selectedNodeData)
    if num_selected == 0: return no_update

    range_min, range_max = None, None
    merge_idRef_style = {'display':'none', 'text-align':'center'}
    merge_options, merge_value = no_update, no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    
    # One Node Selected 
    if num_selected == 1:
        store_session('node_id', selectedNodeData[0]['id'])
        
        if selectedNodeData[0]['type'].startswith('action_'):
            node_id_list, node, data = get_action_source(selectedNodeData[0]['id'])
            button_execute_action_style['display'] = 'inline-block'

        else:
            button_execute_action_style['display'] = 'none'
            node = get_document('node', selectedNodeData[0]['id'])
            data = get_dataset_data(selectedNodeData[0]['id']).to_dict('records')
    
    # Multiple Nodes Selected (Merge Datasets)
    elif num_selected > 1:
        dataset_id_list = [node['id'] for node in selectedNodeData]

        print("Merge Type: ", merge_type)

        if merge_type == 'arrayMergeById':
            merge_idRef_style['display'] = 'block'

            features = set()
            for dataset_id in dataset_id_list:
                data = get_dataset_data(dataset_id)
                features.update(data.columns)
            
            merge_options = [{'label': c, 'value': c} for c in features]
            merge_value = merge_idRef if merge_idRef is not None else merge_options[0]['value']
            data = merge_dataset_data(dataset_id_list, merge_type, idRef=merge_value)

        else:
            data = merge_dataset_data(dataset_id_list, merge_type)
    
    # Truncate Dataset
    range_min = 1
    range_max = len(data)
    if triggered != id('range'):
        range_value = [range_min, range_max]
    data = data[range_value[0]-1:range_value[1]]
    
    # Generate Datatable Data
    df, columns, dropdown_data = generate_right_content_1_data(node, data)
    datatable = generate_datatable(id('datatable'), df.to_dict('records'), columns, cell_editable=True,
                                height='350px', sort_action='native', filter_active='native', 
                                col_selectable='multi',
                                row_deletable=False, row_selectable=False,
                                dropdown_data=dropdown_data)

    return (button_execute_action_style,
            [], None,
            [], None,
            datatable,
            range_min, range_max, range_value,
            merge_idRef_style, merge_options, merge_value)






# All Cytoscape Related Events
@app.callback(
    Output(id('cytoscape'), 'elements'),
    Output(id('cytoscape'), 'layout'),
    Input(id('button_reset_layout'), 'n_clicks'),
    Input(id('node_name'), 'value'),
    Input({'type': id('button_merge'), 'index': ALL}, 'n_clicks'),
    Input(id('button_transform'), 'n_clicks'),
    Input({'type': id('button_clonemetadata'), 'index': ALL}, 'n_clicks'),
    Input({'type': id('button_truncatedataset'), 'index': ALL}, 'n_clicks'),
    Input('url', 'pathname'),
    Input(id('button_remove'), 'n_clicks'),
    Input(id('do_cytoscape_reload'), 'data'),
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'value'),
    Input({'type': id('button_new_data_source'), 'index': ALL}, 'n_clicks'),
    Input(id('button_group'), 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('tabs_node'), 'active_tab'),
    State({'type':id('col_feature_hidden'), 'index': ALL}, 'value'),
    State({'type':id('col_feature'), 'index': ALL}, 'value'),
    State({'type':id('col_datatype'), 'index': ALL}, 'value'),
    State({'type':id('col_button_remove_feature'), 'index': ALL}, 'n_clicks'),
    State(id('right_content_1'), 'style'),
    State(id('range'), 'value'),
)
def cytoscape_triggers(n_clicks_reset_layout, node_name_input, n_clicks_merge, n_clicks_transform, n_clicks_clonemetadata, n_clicks_truncatedataset, pathname, n_clicks_remove, do_cytoscape_reload, merge_type, merge_idRef,
                        n_clicks_add_data_source_list, n_clicks_group,
                        selectedNodeData, active_tab, feature_list, new_feature_list, datatype_list, button_remove_feature_list,
                        right_content_style,
                        dataset_range):
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')
    merge_idRef = None if merge_idRef is None else merge_idRef

    if num_selected <= 0:
        triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
        # New Data Source
        if triggered == '{"index":0,"type":"data_lineage-button_new_data_source"}' and n_clicks_add_data_source_list[0] != None:
            dataset_id = new_data_source()
            add_dataset(project_id, dataset_id)
    else:
        triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
        dataset_id = selectedNodeData[0]['id']

        # Reload    
        if triggered == id('do_cytoscape_reload'):
            if do_cytoscape_reload == False: return no_update

        # # Action 1 - Clone Metadata (Modify Datatype and Rename)
        # elif triggered == '{"index":0,"type":"data_lineage-button_clonemetadata"}':
        #     if n_clicks_clonemetadata[0] is None: return no_update
        #     dataset = get_document('node', dataset_id)
        #     new_dataset = dataset.copy()
        #     new_dataset['features'] = dict(zip(new_feature_list, datatype_list))
        #     remove_list = [feature for feature, n_clicks in zip(new_feature_list, button_remove_feature_list) if (n_clicks % 2 != 0)]
        #     for feature in remove_list:
        #         new_dataset['features'].pop(feature, None)
        #     changed_feature_dict = {f1:f2 for f1, f2 in zip(feature_list, new_feature_list) if f1 != f2}
            
        #     dataset_data = search_documents(dataset_id)
        #     df = json_normalize(dataset_data)
        #     if changed_feature_dict is not None:
        #         df = df.rename(columns=changed_feature_dict)

        #     action(project_id, dataset_id, 'action_1', new_dataset, df)

        # # Action 2 - Truncated Dataset
        # elif triggered == '{"index":0,"type":"data_lineage-button_truncatedataset"}':
        #     if n_clicks_truncatedataset[0] is None: return no_update
        #     dataset_metadata = get_document('node', dataset_id)
        #     dataset_data = search_documents(dataset_id)
        #     df = json_normalize(dataset_data)
        #     df = df[dataset_range[0]-1:dataset_range[1]]
        #     details = { 'range_before': [0, len(df)], 'range_after': [dataset_range[0]-1, dataset_range[1]] }
        #     action(project_id, dataset_id, 'action_2', dataset_metadata, df)

        # Merge Action
        elif triggered == id('button_merge') and all(not node['type'].startswith('action') for node in selectedNodeData):
            pass
            # if n_clicks_merge[0] is None: return no_update
            # dataset_id_list = [node['id'] for node in selectedNodeData]
            # dataset_data = merge_dataset_data(dataset_id_list, merge_type, idRef=merge_idRef)
            # dataset_metadata = merge_metadata(dataset_id_list, 'objectMerge')
            # details = {'merge_type': merge_type}
            # merge(project_id, dataset_id_list, dataset_data, dataset_metadata, details)

        # Transform Action # TODO
        elif triggered == id('button_transform'):
            print("TRANSFORM")
            source_id_list = [node['id'] for node in selectedNodeData]
            cytoscape_action(source_id_list, 'transform')
            pass
            # if n_clicks_truncatedataset[0] is None: return no_update
            # dataset_metadata = get_document('node', dataset_id)
            # dataset_data = search_documents(dataset_id)
            # df = json_normalize(dataset_data)
            # df = df[dataset_range[0]-1:dataset_range[1]]
            # details = { 'range_before': [0, len(df)], 'range_after': [dataset_range[0]-1, dataset_range[1]] }
            # action(project_id, dataset_id, 'action_2', dataset_metadata, df)

        # Button Group
        elif triggered == id('button_group'):
            pass

        # Button Remove Node
        elif triggered == id('button_remove') and n_clicks_remove is not None:
            remove(project_id, selectedNodeData)
                
    
    elements = generate_cytoscape_elements(project_id)
    layout = {
        'name': 'preset',
        'fit': True,
    }

    if triggered == id('button_group'):
        # pprint(selectedNodeData)
        selected_datasets = [node['id'] for node in selectedNodeData if not node['type'].startswith('action')]

        for i in range(len(elements)):
            if elements[i]['data']['id'] in selected_datasets:
                elements[i]['data']['parent'] = 'parent'
        
        elements.append({'data': {'id': 'parent', 'label': 'Parent'}})
                

    # Reset Button pressed
    if triggered == id('button_reset_layout'):
        layout = {
            'name': 'breadthfirst',
            'fit': True,
            'roots': [e['data']['id'] for e in elements if e['classes'].startswith('raw')],
        }

    return elements, layout


@app.callback(
    Output(id('modal_transform_node'), 'is_open'),
    Input(id('button_add_feature_modal'), 'n_clicks'),
    prevent_initial_call=True
)
def select_function(n_clicks):
    return True


# Style Action Datatable Changes # TODO 1
@app.callback(
    Output(id('datatable'), 'data'),
    Output(id('datatable'), 'columns'),
    Output(id('datatable'), "style_data_conditional"),
    Output(id('datatable'), "dropdown_data"),
    Input(id('action_transformnode_session'), "data"),
    Input(id('cytoscape'), 'selectedNodeData'),
    State(id('datatable'), "dropdown_data"),
)
def style_datatable(action_transformnode_session, selectedNodeData, dropdown_data):
    num_selected = len(selectedNodeData)
    if num_selected != 1: return no_update
    node_id = selectedNodeData[0]['id']
    if node_id not in action_transformnode_session: return no_update
    
    # Add & Style New Features
    node_id_list, node, data = get_action_source(node_id)
    df1 = json_normalize(data)
    df2 = pd.DataFrame(action_transformnode_session[node_id]['add_feature'])
    df = pd.concat([df1, df2], axis=1)
    columns = [{"name": i, "id": i, "selectable": True, 'presentation': 'dropdown'} for i in df.columns]
    # print("HERE")
    # print(df1)
    # print(df2)
    # print(df)
    # pprint(columns)

    # Add Datatable Dropdown on new Features
    dropdown_data = [ {c: {'options': [{'label': datatype, 'value': datatype} for datatype in DATATYPE_LIST], 'clearable': False} for c in df.columns if c != index_col_name }]

    # Style Datatable
    style_data_conditional = [{"if": {"column_id": feature}, "color": "yellow"} for feature in df2.columns ]
    style_data_conditional += [{"if": {"column_id": feature}, "backgroundColor": "red"} for feature in action_transformnode_session[node_id]['remove_feature'] ]
    
    return df.to_dict('records'), columns, style_data_conditional, dropdown_data



# Transform Node Triggers
@app.callback(
    Output(id('action_transformnode_session'), 'data'),
    Input(id('new_feature_store'), 'data'),
    Input(id('button_remove_feature'), 'n_clicks'),
    Input(id('datatable'), 'sort_by'),
    Input(id('button_clear'), 'n_clicks'),
    State(id('datatable'), 'active_cell'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('feature_name'), 'value'),
    State(id('action_transformnode_session'), 'data'),
    prevent_initial_call=True,
)
def transform_node_triggers(new_feature, _, sort_by, _2, active_cell, selectedNodeData, new_feature_name, action_transformnode_session):
    num_selected = len(selectedNodeData)
    if num_selected != 1: return no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    node_id = selectedNodeData[0]['id']

    # Initialize action_transformnode_session format
    if node_id not in action_transformnode_session: action_transformnode_session[node_id] = {}
    if 'add_feature' not in action_transformnode_session[node_id]: action_transformnode_session[node_id]['add_feature'] = {}
    if 'add_feature_function' not in action_transformnode_session[node_id]: action_transformnode_session[node_id]['add_feature_function'] = {}
    if 'remove_feature' not in action_transformnode_session[node_id]: action_transformnode_session[node_id]['remove_feature'] = []
    if 'sort_feature' not in action_transformnode_session[node_id]: action_transformnode_session[node_id]['sort_feature'] = ''
        
    # Update new Features
    if triggered == id('new_feature_store'):
        if new_feature_name not in action_transformnode_session[node_id]['add_feature']: 
            action_transformnode_session[node_id]['add_feature'][new_feature_name] = new_feature['data']
            action_transformnode_session[node_id]['add_feature_function'][new_feature_name] = new_feature['function']
        else:
            print('Feature Name Exist!')
            return no_update
    
    # Update Removed Columns
    elif triggered == id('button_remove_feature') and active_cell is not None:
        selected_feature = active_cell['column_id']
        if selected_feature in action_transformnode_session[node_id]['add_feature']: del action_transformnode_session[node_id]['add_feature'][selected_feature]
        elif selected_feature not in action_transformnode_session[node_id]['remove_feature']: action_transformnode_session[node_id]['remove_feature'].append(selected_feature)
        else: action_transformnode_session[node_id]['remove_feature'].remove(selected_feature)

    # Update Sort Features
    elif triggered == id('datatable') and sort_by is not None:
        sort_by = sort_by[0]
        sort_feature = {'feature': sort_by['column_id'], 'direction': sort_by['direction']}
        action_transformnode_session[node_id]['sort_feature'] = sort_feature
    
    elif triggered == id('button_clear'):
        action_transformnode_session = {}

    else:
        return no_update

    return action_transformnode_session



# Load Dataset Config Options
@app.callback(
    Output(id('config_options_fileupload'), 'style'),
    Output(id('config_options_pastetext'), 'style'),
    Output(id('config_options_restapi'), 'style'),
    Output(id('config_options_datacatalog'), 'style'),
    Output(id('table_datacatalog'), 'children'),
    Input(id('select_upload_type'), 'value'),
    Input(id('search_datacatalog'), 'value'),
    State(id('button_save'), 'style'),
)
def load_dataset_options(dataset_type, search_datacatalog_value, button_save_style):
    style1, style2, style3, style4 = {'display':' none'}, {'display':' none'}, {'display':' none'}, {'display':' none'}
    datacatalog_search_results = no_update

    if dataset_type == 'raw_fileupload':  style1 = {'display':' block'}
    elif dataset_type == 'raw_pastetext': style2 = {'display': 'block'}
    elif dataset_type == 'raw_restapi': style3 = {'display':' block'}
    elif dataset_type == 'raw_datacatalog':
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


# Button Chart
@app.callback(
    Output('url', 'pathname'),
    Input(id('button_add_graph'), 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData')
)
def button_chart(n_clicks, selectedNodeData):
    if n_clicks is None: return no_update
    if selectedNodeData is None: return no_update
    if len(selectedNodeData) != 1: return no_update
    store_session('graph_id', '')

    return '/apps/plot_graph'

# Button Chart for specific ID
@app.callback(
    Output({'type': id('button_graph_id'), 'index': MATCH}, 'n_clicks'),
    Input({'type': id('button_graph_id'), 'index': MATCH}, 'n_clicks'),
    State({'type': id('button_graph_id'), 'index': MATCH}, 'value')
)
def load_graph(n_clicks, graph_id):
    store_session('graph_id', graph_id)
    return no_update 


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
)
def load_restapi_options(tapNodeData, _, _2, _3, _4, _5, _6, header_div, param_div, body_div):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '' or triggered == None: return no_update
    
    if triggered == id('cytoscape') and not tapNodeData['type'].startswith('action'):
        header_div, param_div, body_div = [], [], []
        dataset = get_document('node', tapNodeData['id'])
        if dataset['type'] == 'raw_restapi':
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
        project_name_list = [{'label': get_document('node', dataset_id)['name'], 'value': dataset_id} for dataset_id in [p['id'] for p in project['node_list']] if get_document('node', dataset_id)['type'].startswith('raw')]
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








# Generate List of feature dropdown # TODO
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
    options = [{'label': f['name'], 'value': f['name']} for f in features]
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
    Output(id('conditions'), "style"),
    Input(id('dropdown_function_type'), "value"),
    State(id('arithmetic_inputs'), "style"),
    State(id('comparison_inputs'), "style"),
    State(id('aggregate_inputs'), "style"),
    State(id('slidingwindow_inputs'), "style"),
    State(id('formatdate_inputs'), "style"),
    State(id('cumulative_inputs'), "style"),
    State(id('shift_inputs'), "style"),
    State(id('conditions'), "style"),
)
def function_input_style(function_type, style1, style2, style3, style4, style5, style6, style7, conditions_style):
    style1['display'], style2['display'], style3['display'], style4['display'], style5['display'], style6['display'], style7['display'] = 'none', 'none', 'none', 'none', 'none', 'none', 'none'
    conditions_style['display'] = 'none'
    if function_type == 'arithmetic': style1['display'] = 'flex'
    elif function_type == 'comparison': style2['display'] = 'flex'
    elif function_type == 'aggregate': style3['display'] = 'flex'
    elif function_type == 'slidingwindow': style4['display'] = 'flex'
    elif function_type == 'formatdate': style5['display'] = 'flex'
    elif function_type == 'cumulative': style6['display'] = 'flex'
    elif function_type == 'shift': style7['display'] = 'flex'

    if function_type in ['arithmetic', 'comparison']:
        conditions_style['display'] = 'flex'
        
    return style1, style2, style3, style4, style5, style6, style7, conditions_style



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




# Add Feature (Arithmetic)
@app.callback(
    Output(id('new_feature_store'), 'data'),
    Input(id('button_add_feature'), 'n_clicks'),
    State(id('dropdown_function_type'), 'value'),
    State(id('datatable'), 'data'),
    State(id('dropdown_arithmeticfunction'), 'value'),
    State(id('dropdown_arithmeticfeature1'), 'value'),
    State(id('dropdown_arithmeticfeature2'), 'value'),
    prevent_initial_call=True,
)
def add_feature1(n_clicks, function_type, data, function, feature1, feature2):
    if n_clicks is None: return no_update
    if function_type != 'arithmetic': return no_update
    df = pd.DataFrame(data)[1:].reset_index()
    f1 = df[feature1].astype('int32', errors='ignore')
    f2 = df[feature2].astype('int32', errors='ignore')
    try:
        if function == 'add': feature = f1 + f2
        elif function == 'subtract': feature = f1 - f2
        elif function == 'divide': feature = f1 / f2
        elif function == 'multiply': feature = f1 * f2
        elif function == 'exponent': feature = f1 ** f2
        elif function == 'modulus': feature = f1 % f2
        
        feature.loc[-1] = 'numerical' # TODO 2
        feature.index += 1
        feature = feature.sort_index()
        feature = {'data': list(feature), 'function': 'func1'}
    except:
        feature = 'error'
    
    return feature


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


