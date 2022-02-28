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
stylesheet = [
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

        dcc.Interval(id=id('interval_cytoscape'), interval=500, n_intervals=0),
        
        dbc.Row([
            # Left Panel
            dbc.Col([
                html.Div(id=id('last_saved'), style={'display':'inline-block', 'margin':'1px'}),
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button('Reset Layout', id=id('button_reset_layout'), color='dark', className='btn btn-secondary btn-lg', style={'margin-right':'1px', 'display':'block'}),
                        # html.Button('Hide/Show', id=id('button_hide_show'), className='btn btn-warning btn-lg', style={'margin-right':'1px'}), 
                        dbc.DropdownMenu(label="Action", children=[dbc.Spinner(size="sm"), " Loading..."], id=id('dropdown_action'), size='lg', color='warning', style={'display':'inline-block', 'margin':'1px'}),        
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
                                stylesheet=stylesheet)
            ], width=6),

            # Right Panel
            dbc.Col([
                html.Div([
                    html.Div(dbc.Tabs([
                        dbc.Tab(label="Data", tab_id="tab1", disabled=True),
                        dbc.Tab(label="Metadata", tab_id="tab2", disabled=True),
                        dbc.Tab(label="Config", tab_id="tab3", disabled=True),
                        dbc.Tab(label="Graph", tab_id="tab4", disabled=True),
                        dbc.Tab(label="Logs", tab_id="tab5", disabled=True),
                    ], id=id("tabs_node")), style={'float':'left', 'text-align':'left', 'display':'inline-block'}),

                    
                    # html.Div('Last Run: <TODO>', id=id('last_run_config'), style={'float':'right', 'display':'inline-block'}),

                    html.Div([
                        dbc.Button("Run (Last run: <TODO>)", id=id('run_config'), color='warning', disabled=True),
                    #     dbc.Button(html.I(n_clicks=0, className='far fa-play'), id=id('button_run_config'), disabled=False, className='btn btn-warning', style={'margin-left':'1px', 'display':'block'}),
                    #     dbc.Button(html.I(n_clicks=0, className='fas fa-chart-area'), id=id('button_chart'), disabled=True, className='btn btn-success', style={'margin-left':'1px', 'display': 'none'}),
                    #     dbc.Button(html.I(n_clicks=0, className='fas fa-times'), id=id('button_remove'), disabled=True, className='btn btn-danger', style={'margin-left':'1px', 'display':'none'}),
                    #     dbc.Tooltip('Perform Action', target=id('button_run_config')),
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
                            dbc.Col([
                                dcc.RangeSlider(
                                    id=id('range'),
                                    value=[],
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                            ]),
                            dbc.Col([
                                dbc.Select(options=options_merge, value=options_merge[0]['value'], id=id('merge_type'), style={'text-align':'center'}),
                                dbc.Select(options=[], value=None, id=id('merge_idRef'), style={'text-align':'center', 'display':'none'}),
                            ], id=id('merge_type_container'), style={'display':'none'}, width=4),
                            dbc.Col([
                                dbc.Button(html.I(n_clicks=0, className='fa fa-table'), color='info', outline=True, id=id('button_tabular'), n_clicks=0),
                                dbc.Tooltip('View in Tabular Format', target=id('button_tabular')),
                            ], width=1),
                            dbc.Col([dbc.Input(id=id('search_json'), placeholder='Search', style={'text-align':'center'})], width=12),
                        ]),
                    ], id=id('right_header_2'), style={'display':'none', 'font-size':'14px'}),

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
                    
                    
                    # Right Content 0 (No Active Tab)
                    html.Div([], id=id('right_content_0'), style={'display':'none'}),

                    # Right Content Tab 1 (Data)
                    html.Div([dbc.CardBody()], id=id('right_content_1'), style={'display':'none'}),
                    
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

                    # Right Body Tab 5 (Logs)
                    dbc.Row([
                        dbc.Textarea(id=id('node_log'), placeholder='No Logs Found.', disabled=True, style={'height':'700px', 'font-size': '15px'})
                    ], id=id('right_content_5'), style={'display':'none', 'padding':'20px'}),

                ], className='bg-dark', inverse=True, style={'min-height':'780px', 'max-height':'780px', 'overflow-y':'auto'}),
            
            ], width=6),
        ]),

        # Modal (view dataset)
        dbc.Modal(id=id('modal_dataset'), size='xl'),


    ], style={'width':'100%'}),
])


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


@app.callback(
    Output(id('run_config'), 'disabled'),
    Input(id('cytoscape'), 'selectedNodeData'),
)
def enable_run_button(selectedNodeData):
    if selectedNodeData is None: return True
    if len(selectedNodeData) == 1 and selectedNodeData[0]['type'] == 'raw_restapi':
        return False

@app.callback(
    Output(id('tabs_node'), 'active_tab'),
    Input(id('run_config'), 'n_clicks'),
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

    update_node_log(get_session('project_id'), node['id'], 'Run Config: '+str(details), details['timestamp'])
    r = client.collections[node['id']].documents.import_(jsonl, {'action': 'create'})
    print("HERE: ", node['id'])
    pprint(df)
    pprint(jsonl)
    data = get_dataset_data(node['id'])
    pprint(data)
    pprint(r)
   

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



# Set Active Tab and Enable/Disable Tabs
@app.callback(
    Output(id('tabs_node'), 'active_tab'),
    Output(id('tabs_node'), 'children'),
    Input(id('cytoscape'), 'selectedNodeData'),
    State(id('tabs_node'), 'active_tab'),
    State(id('tabs_node'), 'children'),
)
def enable_disable_tab(selectedNodeData, active_tab, tabs):
    if selectedNodeData is None: return no_update
    num_selected = len(selectedNodeData)
    disabled1, disabled2, disabled3, disabled4, disabled5 = True, True, True, True, True

    if num_selected == 0: 
        active_tab = None
    elif num_selected == 1:
        if selectedNodeData[0]['type'].startswith('action') :active_tab = 'tab2'
        elif selectedNodeData[0]['type'] == 'raw': active_tab = 'tab3'
        else:
            active_tab = 'tab1' if active_tab is None else active_tab
            disabled1, disabled2, disabled3, disabled4, disabled5 = False, False, False, False, False
    elif (num_selected > 1 and 
            all(not node['type'].startswith('action') for node in selectedNodeData) and
            all(node['type'] != 'raw' for node in selectedNodeData)
            ):
        active_tab = 'tab1' if (active_tab != 'tab1' or active_tab != 'tab2') else active_tab
        disabled1, disabled2 = False, False
    
    tabs[0]['props']['disabled'] = disabled1
    tabs[1]['props']['disabled'] = disabled2
    tabs[2]['props']['disabled'] = disabled3
    tabs[3]['props']['disabled'] = disabled4
    tabs[4]['props']['disabled'] = disabled5

    return active_tab, tabs



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
    Output(id('right_header_2'), 'style'),
    Output(id('merge_type_container'), 'style'),
    Output(id('right_header_3'), 'style'),
    Input(id('cytoscape'), 'selectedNodeData'),
    Input(id('tabs_node'), 'active_tab'),
)
def generate_right_header(selectedNodeData, active_tab):
    num_selected = len(selectedNodeData)
    right_header_1 = no_update
    right_header_2_style = {'display': 'none'}
    merge_type_container_style = {'display': 'none'}
    right_header_3_style = {'display': 'none'}

    # Output based on Number of Nodes Selected
    if num_selected == 0: right_header_1 = [dbc.Input(id=id('node_name'), style={'font-size':'14px', 'text-align':'center', 'display':'none'})]

    elif num_selected == 1:
        right_header_1 = [dbc.Input(id=id('node_name'), value=selectedNodeData[0]['name'], style={'font-size':'14px', 'text-align':'center'})]
        if (selectedNodeData[0]['type'].startswith('raw_') or selectedNodeData[0]['type'].startswith('processed')) and active_tab == 'tab1': 
            right_header_2_style['display'] = 'block'
            right_header_3_style['display'] = 'none'
        if active_tab == 'tab3': 
            right_header_3_style['display'] = 'block'

    elif num_selected > 1: 
        right_header_1 = [
            dbc.Input(value='{}) '.format(i+1) + node['name'], disabled=True, style={'margin':'5px', 'text-align':'center'}) for i, node in enumerate(selectedNodeData)
        ] + [dbc.Input(id=id('node_name'), style={'display': 'none'})]

        if all(not node['type'].startswith('action') for node in selectedNodeData) and active_tab == 'tab1':
            right_header_2_style['display'] = 'block'
            merge_type_container_style['display'] = 'block'

    return right_header_1, right_header_2_style, merge_type_container_style, right_header_3_style


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
def generate_right_content_display(active_tab, style0, style1, style2, style3, style4, style5):
    style0['display'], style1['display'], style2['display'], style3['display'], style4['display'], style5['display'] = 'none', 'none', 'none', 'none', 'none', 'none'
    if active_tab is None: style0['display'] = 'block'
    elif active_tab == 'tab1': style1['display'] = 'block'
    elif active_tab == 'tab2': style2['display'] = 'block'
    elif active_tab == 'tab3': style3['display'] = 'block'
    elif active_tab == 'tab4': style4['display'] = 'block'
    elif active_tab == 'tab5': style5['display'] = 'block'

    return style0, style1, style2, style3, style4, style5


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
    Input(id('cytoscape'), 'selectedNodeData'),
    Input(id('right_content_4'), 'style'),
    State(id('right_content_4'), 'children'),
)
def generate_right_content(selectedNodeData, _, right_content_4):
    if len(selectedNodeData) == 0: return no_update
    project_id = get_session('project_id')
    project = get_document('project', project_id)
    right_content_4 = [right_content_4[0]]
    
    if selectedNodeData[0]['id'] in project['graph_dict']:
        for graph_id in project['graph_dict'][selectedNodeData[0]['id']]:
            graph = get_document('graph', graph_id)

            if graph['type'] == 'line': fig = get_line_figure(graph['x'], graph['y'])
            elif graph['type'] == 'bar': fig = get_bar_figure(graph['x'], graph['y'], graph['barmode'])
            elif graph['type'] == 'pie': fig = get_pie_figure(graph['names'], graph['values'])
            elif graph['type'] == 'scatter': fig = get_scatter_figure(graph['x'], graph['y'], graph['color'])

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
    Output(id('right_content_5'), 'children'),
    Input(id('cytoscape'), 'selectedNodeData'),
    Input(id('right_content_5'), 'style'),
)
def generate_right_content(selectedNodeData, _):
    if len(selectedNodeData) == 0: return no_update
    project_id = get_session('project_id')
    project = get_document('project', project_id)
    logs = None
    node_id = selectedNodeData[0]['id']
    logs = ''
    if node_id in project['node_log']:
        for node_log_id in project['node_log'][node_id]:
            node_log = get_document('node_log', node_log_id)
            logs += '{}: {} \n'.format(node_log['timestamp'], node_log['description'])

    right_content_5 = dbc.Textarea(id=id('logs'), placeholder='No Logs Found.', value=logs, disabled=True, style={'height':'700px', 'font-size': '15px'})
    return right_content_5


# Generate Right Content (default, tab1, tab2)
@app.callback(
    Output(id('right_content_0'), 'children'),
    Output(id('right_content_1'), 'children'),
    Output(id('right_content_2'), 'children'),
    
    Output(id('range'), 'min'),
    Output(id('range'), 'max'),
    Output(id('range'), 'value'),
    Output(id('merge_idRef'), 'style'),
    Output(id('merge_idRef'), 'options'),
    Output(id('merge_idRef'), 'value'),
    Output(id('dropdown_datasourcetype_container'), 'style'),
    Input(id('cytoscape'), 'selectedNodeData'),
    Input(id('range'), 'value'),
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'value'),
    Input(id('button_tabular'), 'n_clicks'),
    Input(id('right_content_0'), 'style'),
    Input(id('right_content_1'), 'style'),
    Input(id('right_content_2'), 'style'),
)
def generate_right_content(selectedNodeData, range_value, merge_type, merge_idRef, n_clicks_button_tabular, _, _2, _3):
    num_selected = len(selectedNodeData)
    if num_selected == 0: return no_update

    right_content_0, right_content_1, right_content_2 = no_update, no_update, no_update
    range_min, range_max = None, None
    dropdown_datasourcetype_container_style = {'display': 'none'}
    
    merge_idRef_style = {'display':'none', 'text-align':'center'}
    merge_options, merge_value = no_update, no_update
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

    # Single Node Selected 
    if num_selected == 1:
        store_session('node_id', selectedNodeData[0]['id'])

        # Tab 1 Content
        data = get_dataset_data(selectedNodeData[0]['id'])
        data = data.to_dict('records')

        # Tab 2 Content
        if selectedNodeData[0]['type'].startswith('action'): 
            action = get_document('node', selectedNodeData[0]['id'])
            right_content_2 = [display_action(action)]
        else:
            dataset = get_document('node', selectedNodeData[0]['id'])
            right_content_2 = [display_metadata(dataset, id, disabled=False)]

        if selectedNodeData[0]['type'].startswith('raw'):
            dropdown_datasourcetype_container_style['display'] = 'flex'
    
    # Multiple Nodes Selected (Merge Datasets)
    elif num_selected > 1:
        
        # Tab 1 Content
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
        
        # Tab 2 Content
        if all(node['type'].startswith('action') for node in selectedNodeData): 
            right_content_2 = []

        elif all(not node['type'].startswith('action') for node in selectedNodeData): 
            dataset_id_list = [node['id'] for node in selectedNodeData]
            dataset = merge_metadata(dataset_id_list)
            right_content_2 = [display_metadata(dataset, id, disabled=True)]
        
    range_min = 1
    range_max = len(data)
    if triggered != id('range'):
        range_value = [range_min, range_max]
    data = data[range_value[0]-1:range_value[1]]
    
    if n_clicks_button_tabular % 2 == 0: right_content_1 = display_dataset_data(data, format='json')
    else: right_content_1 = display_dataset_data(data, format='tabular')


    return (right_content_0, right_content_1, right_content_2,
            range_min, range_max, range_value,
            merge_idRef_style, merge_options, merge_value, 
            dropdown_datasourcetype_container_style)






# All Cytoscape Related Events
@app.callback(
    Output(id('cytoscape'), 'elements'),
    Output(id('cytoscape'), 'layout'),
    Input(id('button_reset_layout'), 'n_clicks'),
    Input(id('node_name'), 'value'),
    Input({'type': id('button_merge'), 'index': ALL}, 'n_clicks'),
    Input({'type': id('button_clonemetadata'), 'index': ALL}, 'n_clicks'),
    Input({'type': id('button_truncatedataset'), 'index': ALL}, 'n_clicks'),
    Input('url', 'pathname'),
    Input({'type': id('button_remove'), 'index': ALL}, 'n_clicks'),
    Input(id('do_cytoscape_reload'), 'data'),
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'value'),
    Input({'type': id('button_add_data_source'), 'index': ALL}, 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('tabs_node'), 'active_tab'),
    State({'type':id('col_feature_hidden'), 'index': ALL}, 'value'),
    State({'type':id('col_feature'), 'index': ALL}, 'value'),
    State({'type':id('col_datatype'), 'index': ALL}, 'value'),
    State({'type':id('col_button_remove_feature'), 'index': ALL}, 'n_clicks'),
    State(id('right_content_1'), 'style'),
    State(id('range'), 'value'),
)
def cytoscape_triggers(n_clicks_reset_layout, node_name_input, n_clicks_merge, n_clicks_clonemetadata, n_clicks_truncatedataset, pathname, n_clicks_remove_list, do_cytoscape_reload, merge_type, merge_idRef,
                        n_clicks_add_data_source_list,
                        selectedNodeData, active_tab, feature_list, new_feature_list, datatype_list, button_remove_feature_list,
                        right_content_style,
                        dataset_range):
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')
    merge_idRef = None if merge_idRef is None else merge_idRef

    if num_selected <= 0:
        triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
        # New Data Source
        if triggered == '{"index":0,"type":"data_lineage-button_add_data_source"}' and n_clicks_add_data_source_list[0] != None:
            dataset_id = new_data_source()
            add_dataset(project_id, dataset_id)
    else:
        triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
        dataset_id = selectedNodeData[0]['id']

        # Reload    
        if triggered == id('do_cytoscape_reload'):
            if do_cytoscape_reload == False: return no_update

        # Action 1 - Clone Metadata (Modify Datatype and Rename)
        elif triggered == '{"index":0,"type":"data_lineage-button_clonemetadata"}':
            if n_clicks_clonemetadata[0] is None: return no_update
            dataset = get_document('node', dataset_id)
            new_dataset = dataset.copy()
            new_dataset['features'] = dict(zip(new_feature_list, datatype_list))
            remove_list = [feature for feature, n_clicks in zip(new_feature_list, button_remove_feature_list) if (n_clicks % 2 != 0)]
            for feature in remove_list:
                new_dataset['features'].pop(feature, None)
            changed_feature_dict = {f1:f2 for f1, f2 in zip(feature_list, new_feature_list) if f1 != f2}
            
            dataset_data = search_documents(dataset_id)
            df = json_normalize(dataset_data)
            if changed_feature_dict is not None:
                df = df.rename(columns=changed_feature_dict)

            action(project_id, dataset_id, 'action_1', new_dataset, df)

        # Action 2 - Truncated Dataset
        elif triggered == '{"index":0,"type":"data_lineage-button_truncatedataset"}':
            if n_clicks_truncatedataset[0] is None: return no_update
            dataset_metadata = get_document('node', dataset_id)
            dataset_data = search_documents(dataset_id)
            df = json_normalize(dataset_data)
            df = df[dataset_range[0]-1:dataset_range[1]]
            details = { 'range_before': [0, len(df)], 'range_after': [dataset_range[0]-1, dataset_range[1]] }
            action(project_id, dataset_id, 'action_2', dataset_metadata, df)

        # Action 3 - Merge Datasets Action
        elif triggered == '{"index":0,"type":"data_lineage-button_merge"}' and all(not node['type'].startswith('action') for node in selectedNodeData):
            if n_clicks_merge[0] is None: return no_update
            dataset_id_list = [node['id'] for node in selectedNodeData]
            dataset_data = merge_dataset_data(dataset_id_list, merge_type, idRef=merge_idRef)
            dataset_metadata = merge_metadata(dataset_id_list, 'objectMerge')
            details = {'merge_type': merge_type}
            merge(project_id, dataset_id_list, dataset_data, dataset_metadata, details)

        

        # Button Remove Node
        elif triggered == '{"index":0,"type":"data_lineage-button_remove"}' and n_clicks_remove_list[0] != None:
            remove(project_id, selectedNodeData)
                
    
    elements = generate_cytoscape_elements(project_id)
    layout = {
        'name': 'preset',
        'fit': True,
    }

    # Reset Button pressed
    if triggered == id('button_reset_layout'):
        layout = {
            'name': 'breadthfirst',
            'fit': True,
            'roots': [e['data']['id'] for e in elements if e['classes'].startswith('raw')],
        }

    return elements, layout






# # Disable/Enable Right Panel Buttons
# @app.callback(
#     Output(id('button_save'), 'disabled'),
#     Output(id('button_chart'), 'disabled'),
#     Output(id('button_remove'), 'disabled'),
#     Input(id('cytoscape'), 'selectedNodeData'),
# )
# def button_disable_enable(selectedNodeData):
#     button1, button2, button3 = True, True, True
#     num_selected = len(selectedNodeData)

#     if num_selected == 1:
#         button1, button2, button3 = False, False, False
#     elif num_selected > 1:
#         pass

#     return button1, button2, button3 


# Preview Dataset from Data Catalog
@app.callback(
    Output(id('modal_dataset'), 'children'),
    Output(id('modal_dataset'), 'is_open'),
    Input({'type':id('col_button_preview'), 'index': ALL}, 'n_clicks'),
    State({'type':id('col_button_preview'), 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def preview_dataset(n_clicks_list, node_id_list):
    triggered = json.loads(callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0])
    index = triggered['index']
    if n_clicks_list[index] is None: return no_update
    node_id = node_id_list[index]

    df = get_dataset_data(node_id)
    return [
        # dbc.ModalHeader(dbc.ModalTitle('')),
        dbc.ModalBody(generate_datatable(id('preview_dataset_datatable'), df.to_dict('records'), df.columns, height='800px')),
        # dbc.ModalFooter(''),
    ], True


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



# Remove Feature
@app.callback(
    Output({'type': id('col_button_remove_feature'), 'index': MATCH}, 'outline'),
    Input({'type': id('col_button_remove_feature'), 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True,
)
def button_remove_feature(n_clicks):
    if n_clicks is None: return no_update
    if n_clicks % 2 == 0: return True
    else: return False

# Toggle button Tabular
@app.callback(
    Output(id('button_tabular'), 'outline'),
    Input(id('button_tabular'), 'n_clicks'),
)
def toggle_button_tabular(n_clicks):
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



# Generate options in dropdown and button 
@app.callback(
    Output(id('dropdown_action'), 'children'),
    Input(id('cytoscape'), 'selectedNodeData'),
    # Input(id('dropdown_action'), 'children')
)
def generate_dropdown_actions(selectedNodeData):
    if selectedNodeData is None: return no_update
    
    # Generate Options
    options = []
    if len(selectedNodeData) == 0:
        options = [dbc.DropdownMenuItem('Add Data Source', href='#', id={'type': id('button_add_data_source'), 'index': 0}, style={'background-color':'#90ee90', 'padding':'10px'})]
    if len(selectedNodeData) == 1:
        if selectedNodeData[0]['type'] == 'raw':
            options = [
                dbc.DropdownMenuItem('No Data Source', href='#', className='action_dropdown', disabled=True),
                dbc.DropdownMenuItem('Remove', href='#', id={'type': id('button_remove'), 'index': 0}, style={'background-color':'#FF7F7F', 'padding':'10px', 'text-align':'center'}),
            ]
        else:
            options = [
                dbc.DropdownMenuItem('Truncate Dataset', id={'type': id('button_truncatedataset'), 'index': 0}, href='#', className='action_dropdown'),
                dbc.DropdownMenuItem('Clone Metadata', id={'type': id('button_clonemetadata'), 'index': 0}, href='#', className='action_dropdown'),
                dbc.DropdownMenuItem('Feature Engineering', href='/apps/feature_engineering', className='action_dropdown'),
                dbc.DropdownMenuItem('Impute Data', href='/apps/impute_data', className='action_dropdown'),
                
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem('Remove', href='#', id={'type': id('button_remove'), 'index': 0}, style={'background-color':'#FF7F7F', 'padding':'10px', 'text-align':'center'}),
            ]
        
    elif len(selectedNodeData) > 1 and all(not node['type'].startswith('action') for node in selectedNodeData):
        options = [dbc.DropdownMenuItem("Merge Datasets", href='#', style={'background-color':'yellow', 'padding':'10px'}, id={'type': id('button_merge'), 'index': 0})]

    return options


