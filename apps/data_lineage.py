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
        
        dcc.Interval(id=id('interval_cytoscape'), interval=500, n_intervals=0),
        
        dbc.Row([
            # Left Panel
            dbc.Col([
                html.Div(id=id('last_saved'), style={'display':'inline-block', 'margin':'1px'}),
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button('Add Source', id=id('button_add_dataset'), color='info', className='cytoscape_buttons'),
                        dbc.Button('Action', id=id('button_new_action'), color='warning', className='cytoscape_buttons'),
                        dbc.Button('Remove', id=id('button_remove'), color='danger', className='cytoscape_buttons'),
                        dbc.Button('Group', id=id('button_group'), color='success', className='cytoscape_buttons'),
                        dbc.Button('Reset', id=id('button_reset_layout'), color='dark', className='cytoscape_buttons'),
                        # dbc.Button('Hide/Show', id=id('button_hide_show'), className='cytoscape_buttons'),
                        dbc.Button('Run', id=id('button_run_cytoscape'), color='primary', className='cytoscape_buttons', disabled=True),     
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
                        dbc.Tab(label="Logs", tab_id="tab5", disabled=True),
                    ], id=id("tabs_node")), style={'float':'left', 'text-align':'left', 'display':'inline-block'}),

                    html.Div([
                        dbc.Button("Revert", id=id('button_last_saved_changes'), color='primary'),
                        dbc.Button('Execute', id=id('button_execute_action'), color='warning'),

                        dbc.Tooltip('Revert to Last Saved Changes', target=id('button_last_saved_changes')),
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
                                dbc.Button(html.I(className='fas fa-plus-circle'), id=id('button_add_feature_modal'), color='light', outline=True),
                                dbc.Button(html.I(className='fas fa-trash'), id=id('button_remove_feature'), color='danger', outline=True),
                                dbc.Button(html.I(className='fas fa-eraser'), id=id('button_clear'), color='info', outline=True),
                                dbc.Button(html.I(className='fa fa-table'), color='secondary', outline=True, id=id('button_display_mode'), n_clicks=0),
                                dbc.Button(html.I(className='fas fa-arrow-right'), id=id('button_run_restapi'), color='warning', outline=True),
                                dbc.Tooltip('Add Feature', target=id('button_add_feature_modal')),
                                dbc.Tooltip('Remove Feature', target=id('button_remove_feature')),
                                
                                dbc.Tooltip('Clear all Changes', target=id('button_clear')),
                                dbc.Tooltip('View in Tabular Format', target=id('button_display_mode')),
                                dbc.Tooltip('Run API', target=id('button_run_restapi')),
                            ], width=4, style={'text-align':'right', 'float':'right'}),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Select(options=options_merge, value=options_merge[0]['value'], id=id('merge_type'), style={'display':'none', 'text-align':'center'}),
                                dbc.Select(options=[], value=None, id=id('merge_idRef'), style={'text-align':'center', 'display':'none'}),
                            ], width=12),
                        ])
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
                    html.Div([
                        html.Div(generate_datatable(id('datatable')), id=id('datatable_container'), style={'display':'none'}),
                        html.Div([
                            dbc.InputGroup([
                                dbc.InputGroupText('Group By ', style={'width':'20%', 'font-weight':'bold', 'font-size':'13px', 'padding-left':'6px'}),
                                html.Div(dcc.Dropdown(id=id('dropdown_groupby_feature'), multi=True, options=[], value=None, persistence=True, style={'color':'black', 'text-align':'center'}), style={'width':'80%'}),
                            ]),
                            dbc.Table([], id=id('table_aggregate_function'), bordered=True, dark=True, hover=True, striped=True, style={'overflow-y': 'auto', 'max-height':'350px'}),
                            dbc.Col(generate_datatable(id('datatable_aggregate'), height='300px')),
                        ], style={'display':'none'}, id=id('aggregate_container'))
                    ], id=id('right_content_1'), style={'display':'none'}),

                    
                    # Right Content Tab 2 (Metadata)
                    html.Div([], id=id('right_content_2'), style={'display':'none'}),

                    # Right Content Tab 3 (Config)
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
                        html.Div(generate_datacatalog_options(id), style={'display':'none', 'overflow-y': 'auto', 'max-height':'500px'}, id=id('config_options_datacatalog')),

                        dbc.CardFooter([dbc.Row(dbc.Col(dbc.Button(children='Save', id=id('button_save'), color='warning', style={'width':'100%', 'font-size':'22px'}), width={'size': 8, 'offset': 2}))])
                    ], id=id('right_content_3'), style={'display': 'none'}),

                    # Right Content Tab 4 (Graph)
                    dbc.Row([
                        dbc.Col(dbc.Button(children='Plot Graph', id=id('button_add_graph'), color='warning', style={'width':'100%', 'font-size':'22px'}), width={"size": 8, "offset": 2}),
                    ], id=id('right_content_4'), style={'display':'none'}),

                    # Right Content Tab 5 (Logs)
                    html.Div([
                        dbc.Card([
                            dbc.CardHeader(html.H6("Logs (TBD)", style={'font-size':'14px', 'font-weight': 'bold', 'text-align':'center', 'margin':'0px'}), style={'padding':'1px', 'margin':'0px'}),
                            dbc.CardBody([], id('log_container')),
                        ], style={'display': 'none'}),
                    ], style={'padding':'1px', 'overflow-y':'auto'}),

                ], className='bg-dark', inverse=True, style={'min-height':'850px', 'max-height':'850px', 'overflow-y':'auto'}),    
            ], width=6), 
        ]),

        # Modal (view dataset)
        dbc.Modal(id=id('modal_dataset'), size='xl'),

        # Modal Select Function
        dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Transform Node")),
                dbc.ModalBody(generate_transform_inputs(id)),
                dbc.ModalFooter(dbc.Button('Add Feature', color='warning', id=id('button_add_feature'), style={'width':'100%'})),
                html.Div([], id=id('add_feature_msg'), style={'text-align':'center', 'color':'red'})
            ],
            id=id('modal_add_feature'),
            is_open=False,
            backdrop=False,
            style={'margin-left':'60px !important'}
        ),

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
    Output(id('merge_type'), 'style'),

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
    s1, s2, s3, s4, s5, s6, s7, s8, s9 = ({'display': 'none'}, {'display': 'none'}, {'display': 'none'},
                                            {'display': 'none'}, {'display': 'none'}, {'display': 'none'},
                                            {'display': 'none', 'text-align':'center'}, {'display': 'hidden'}, {'display': 'none', 'text-align':'center'}
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
                selected_inputs = action['inputs'] if selected_action == 'merge' else action['inputs'][0]
                selected_outputs = action['outputs']

                options_inputs = [{'label': d['name'], 'value':d['id']} for d in dataset_list if d['id'] not in action['outputs']]
                options_outputs = [{'label': d['name'], 'value':d['id']} for d in dataset_list if d['id'] not in action['inputs']]

                if selected_action == 'merge':
                    s9['display'] = 'block'
                if selected_action == 'merge':
                    s2['display'] = 'block'
                if selected_action == 'transform':
                    s2['display'] = 'block'
                
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
            s1, s2, s3, s4, s5, s6, s7, s8, s9
            )





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
            if action['id'] in transform_store:
                if action['details'] != transform_store[action['id']]:
                    action['state'] = 'amber'
                else:
                    pass
                    # TODO save last saved state (convert 'state' into a stack?)
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
            df = df.drop(index_col_name, 1)

            try:
                if action_name == 'merge':
                    action['details'] = {'merge_type':'none', 'idRef': 'none'}

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
                    columns_agg = [c for c in columns_agg if c['id'] != index_col_name]
                    # df = df.drop(index_col_name, 1)
                    dataset_o['features'] = [{
                        'id': c['id'],
                        'name': c['name'],
                        'datatype': str(datatype),
                        'expectation': [],
                    } for c, datatype in zip(columns_agg, df.convert_dtypes().dtypes)]

                    print('\n\nstart')
                    pprint(columns_agg)
                    print('end\n\n')

                elif action_name == 'impute':
                    pass

                action['state'] = 'green'
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
                action['state'] = 'red'
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
            'roots': [e['data']['id'] for e in elements if 'type' in e['data'] and e['data']['type'] == 'raw'],
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
    Output(id('button_last_saved_changes'), 'style'),
    Output(id('button_execute_action'), 'style'),

    Output(id('button_add_feature_modal'), 'style'),
    Output(id('button_remove_feature'), 'style'),
    Output(id('button_clear'), 'style'),

    Output(id('button_display_mode'), 'style'),
    
    Output(id('button_run_restapi'), 'style'),
    Input(id('tabs_node'), 'active_tab'),
    Input(id('dropdown_action'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def display_node_buttons(active_tab, action_name, selectedNodeData):
    if active_tab != 'tab1': return no_update
    num_selected = len(selectedNodeData)
    if num_selected == 0: return no_update

    s1, s2, s3, s4, s5, s6, s7 = ({'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, 
                                    {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
                                )

    if num_selected == 1:
        node_type = selectedNodeData[0]['type']
       
        if node_type == 'action':
            action = get_document('action', selectedNodeData[0]['id'])
            action_name = action_name if action_name is not None else action['name']
            s1['display'] = 'inline-block'
            s2['display'] = 'inline-block'

            if action_name == 'transform':
                s3['display'], s4['display'], s5['display'] = 'inline-block', 'inline-block', 'inline-block'
            elif action_name == 'merge':
                pass

        elif node_type == 'dataset':
            s6['display'] = 'inline-block'
            if selectedNodeData[0]['upload_details'] != {}:
                if selectedNodeData[0]['upload_details']['method'] == 'restapi':
                    s7['display'] = 'inline-block'

    else:
        if all(node['type'] == 'dataset' for node in selectedNodeData):
            s6['display'] = 'inline-block'

    return s1, s2, s3, s4, s5, s6, s7


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

    if num_selected == 1:
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
    elif action_val == 'merge':
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
#     datatable = datatable = generate_datatable(id('datatable_logs'), df.to_dict('records'), columns, height='170px', sort_action='native', filter_action='native')

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
            name, id={'type': id('button_agg_function'), 'index': features[j]['id']+'_'+aggregate_button_name_list[i]}, n_clicks=0, color='light', size='md', outline=True, style={'width':'80px'}
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
    Input({'type': id('button_agg_function'), 'index': ALL}, 'n_clicks'),
    State({'type': id('button_agg_function'), 'index': ALL}, 'id'),
    State(id('dropdown_groupby_feature'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('aggregate_store'), 'data'),
    prevent_initial_call=True,
)
def generate_datatable_aggregate(_, n_clicks_list, id_list, groupby_features, selectedNodeData, aggregate_store):
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
        feature_func_dict = {}
        for i in range(len(selected_list)):
            if selected_list[i] == True:
                feature, agg_func = id_list[i]['index'].rsplit('_', 1)
                if feature in feature_func_dict: feature_func_dict[feature].append(agg_func)
                else: feature_func_dict[feature] = [agg_func]

        action_id = selectedNodeData[0]['id']
        if action_id not in aggregate_store: aggregate_store[action_id] = {}
        aggregate_store[action_id] = {'groupby_features': groupby_features, 'aggregate_dict': ['max']}

        # Group by
        action_id = selectedNodeData[0]['id']
        dataset, df = get_action_source(action_id)
        df = df[1:].reset_index()

        # pprint(feature_func_dict)
        # print(groupby_features)
        # print(df)

        df_agg = df.groupby(groupby_features[0]).sum()
        # df_agg = df.groupby(groupby_features[0]).aggregate(['max']) # TODO

        # Columns
        df_agg.insert(0, df_agg.index.name, df_agg.index)
        # df_agg.insert(0, index_col_name, range(1, len(df_agg)+1))

        features_dict = {}
        for feature_id in df_agg.columns:
            for f in dataset['features']:
                if feature_id == f['id']:
                    features_dict[feature_id] = f['name']
        # columns = [{'id':'no.', 'name':'no.', 'selectable':False}]
        columns = [{"id": c, 'name': c, 'selectable': False} for c in df_agg.columns]

        return df_agg.to_dict('records'), columns, aggregate_store






@app.callback(
    Output(id('merge_idRef'), 'style'),
    Output(id('merge_idRef'), 'options'),
    Output(id('merge_idRef'), 'value'),
    Input(id('merge_type'), 'value'),
    State(id('merge_type'), 'style'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def generate_merge_idRef(merge_type, style, selectedNodeData):
    style_idRef, options_idRef, val_idRef = {'display':'none'}, [], None
    if style['display'] == 'block' and merge_type == 'arrayMergeById':
        if merge_type == 'arrayMergeById':
            style_idRef = {'display':'block', 'text-align':'center'}
            action = get_document('action', selectedNodeData[0]['id'])
            inputs = action['inputs']
            features = set()

            for node_id in inputs:
                data = get_dataset_data(node_id)
                features.update(data.columns)
            options_idRef = [{'label': c, 'value': c} for c in features]
            val_idRef = options_idRef[0]['value']

    return style_idRef, options_idRef, val_idRef



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
            if selected_action == 'merge':
                s1['display'] = 'block'
                datatable_container = generate_datatable(id('datatable'), height='550px')
            elif selected_action == 'transform':
                s1['display'] = 'block'
                datatable_container = generate_datatable(id('datatable'), cell_editable=True, height='600px', sort_action='native', filter_action='native', col_selectable='multi')
            elif selected_action == 'aggregate':
                s1['display'] = 'block'
                s2['display'] = 'block'
                datatable_container = generate_datatable(id('datatable'), height='200px', col_selectable='multi')
            elif selected_action == 'impute': datatable_container = []
            else: datatable_container = []
        elif node_type == 'dataset':
            s1['display'] = 'block'
            datatable_container = generate_datatable(id('datatable'), height='650px')
    elif num_selected > 1 and all(node['type'] == 'dataset' for node in selectedNodeData):
        s1['display'] = 'block'
        datatable_container = generate_datatable(id('datatable'), height='380px')

    return datatable_container, s1, s2






    
    


@app.callback(
    Output(id('modal_add_feature'), 'is_open'),
    Input(id('button_add_feature_modal'), 'n_clicks'),
    prevent_initial_call=True
)
def select_function(n_clicks):
    return True






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
    store_session('dataset_id', selectedNodeData[0]['id'])
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
    
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'vale'),

    Input(id('range_slider'), 'value'),
    Input(id('search2'), 'value'),

    State(id('dropdown_action'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('datatable'), 'data'),
    State(id('datatable'), 'columns'),
)
def datatable_triggers(_, action_inputs, transform_store, 
                        merge_type, merge_idRef,
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
    
    if num_selected == 1:
        node_id = selectedNodeData[0]['id']
        node_type = selectedNodeData[0]['type']

        if node_type == 'action':
            dataset, df = get_action_source(node_id, action_inputs, merge_type, merge_idRef)
            features = dataset['features']

            # Add/Style Session Changes
            if selected_action == 'transform':
                renamable = True
                show_datatype_dropdown = True
                if node_id in transform_store:
                    store = transform_store[node_id]
                    
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
        inputs = [node['id'] for node in selectedNodeData]
        dataset = merge_metadata(inputs, 'objectMerge')
        df = merge_dataset_data(inputs, merge_type, merge_idRef)
        features = dataset['features']

    else:
        return no_update
    
    # Filter Range
    # Search Value

    # Process into Datatable format
    if df.empty:
        print("Empty")
        return [], [], None, None, None
    else:
        df, columns, dropdown_data = generate_datatable_data(df, features, show_datatype_dropdown=show_datatype_dropdown, renamable=renamable)


    return df.to_dict('records'), columns, dropdown_data, style_data_conditional, style_header_conditional



# Transform Node
@app.callback(
    Output(id('transform_store'), 'data'),
    Output(id('add_feature_msg'), 'children'),
    # Output(id('modal_add_feature'), 'is_open'),
    Input('url', 'pathname'),
    Input(id('right_content_1'), 'style'),
    Input(id('button_last_saved_changes'), 'n_clicks'),
    Input(id('button_execute_action'), 'n_clicks'),
    Input(id('button_add_feature'), 'n_clicks'),
    Input(id('button_remove_feature'), 'n_clicks'),
    Input(id('button_clear'), 'n_clicks'),

    State(id('datatable'), 'sort_by'),
    State(id('datatable'), 'filter_query'),
    
    State(id('dropdown_action'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('datatable'), 'data'),
    State(id('datatable'), 'columns'),
    State(id('datatable'), 'active_cell'),
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
def transform_triggers(_, _1, _2, _3, _4, _5, _6,
                sort_by, filter_query,
                selected_action, selectedNodeData, data, columns, active_cell, function_type, transform_store, feature_name,
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
                    f1 = df2[f1a].str.strip().astype(float).astype(datatype1)
                    f2 = df2[f1b].str.strip().astype(float).astype(datatype2)

                    if func1 == 'add': data = f1 + f2
                    elif func1 == 'subtract': data = f1 - f2
                    elif func1 == 'divide': data = f1 / f2
                    elif func1 == 'multiply': data = f1 * f2
                    elif func1 == 'exponent': data = f1 ** f2
                    elif func1 == 'modulus': data = f1 % f2

                    transform_func = func1
                    # dependent_features = [f1, f2]
                    
                elif function_type == 'comparison':
                    pass
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
            
            if store is not no_update:
                store['features'].append({
                    'id':       str(uuid.uuid1()),
                    'name':     feature_name,
                    'datatype': 'Int64',
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
                    break

        # Clear Session
        elif triggered == id('button_clear'):
            print("Clear Transform Session")
            transform_store[action_id] = {}
            transform_store[action_id]['features'] = []
            transform_store[action_id]['others'] = {}

        # Revert to Last Saved Data
        elif triggered == id('button_last_saved_changes'):
            transform_store[action_id] = action['details']

        else:
            transform_store = no_update
        
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


