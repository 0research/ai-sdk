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
    # Dataset Nodes
    {
        'selector': '.raw_userinput',
        'style': {

        }
    },
    {
        'selector': '.raw_restapi',
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
            'content': 'data(action)'
        }
    },
    

]


options_merge = [{'label': o, 'value': o} for o in MERGE_TYPES]

layout = html.Div([
    html.Div([
        dcc.Store(id=id('do_cytoscape_reload'), storage_type='session', data=False),
        dcc.Store(id=id('preview_store'), storage_type='memory'),
        dcc.Store(id=id('dataset_data'), storage_type='memory'),

        # Left Panel
        dbc.Row([
            dbc.Col([
                html.H5('Data Lineage (Data Flow Experiments)', style={'text-align':'center', 'display':'inline-block', 'margin':'0px 0px 0px 40px'}),
                html.Div([
                    html.Button('Load', id=id('button_load'), className='btn btn-secondary btn-lg', style={'margin-right':'1px'}),
                    # html.Button('Hide/Show', id=id('button_hide_show'), className='btn btn-warning btn-lg', style={'margin-right':'1px'}), 
                    dbc.DropdownMenu(label="Action", children=[], id=id('dropdown_action'), size='lg', color='warning', style={'display':'inline-block'}),
                ], style={'float':'right', 'display':'inline-block'}),

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
                                style={'height': '800px','width': '100%'},
                                stylesheet=stylesheet)
            ], width=6),

            # Right Panel
            dbc.Col([
                html.Div([
                    html.Div(dbc.Tabs([], id=id("tabs_node")), style={'float':'left', 'text-align':'left', 'display':'inline-block'}),
                    html.Div([
                        dbc.Button(html.I(n_clicks=0, className='fas fa-check'), id=id('button_perform_action'), className='btn btn-warning', style={'margin-left':'1px'}),
                        dbc.Button(html.I(n_clicks=0, className='fas fa-chart-area'), id=id('button_chart'), className='btn btn-success', style={'margin-left':'1px'}),
                        dbc.Button(html.I(n_clicks=0, className='fas fa-times'), id=id('button_remove'), className='btn btn-danger', style={'margin-left':'1px'}),
                        dbc.Tooltip('Perform Action', target=id('button_perform_action')),
                        dbc.Tooltip('Chart', target=id('button_chart')),
                        dbc.Tooltip('Remove Action or Raw Dataset', target=id('button_remove')),
                    ], style={'float':'right', 'text-align':'right', 'display':'inline-block'}),
                ], style={'display':'inline-block', 'width':'100%'}),
                  
                dbc.Card([
                    # Headers
                    dbc.CardHeader([html.P(id=id('right_header_1'), style={'text-align':'center', 'font-size':'13px', 'font-weight':'bold', 'float':'left', 'width':'100%'})]),
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
                        ]),
                    ], id=id('right_header_2'), style={'display':'none'}),
                    dbc.CardHeader([dbc.Input(id=id('search_json'), placeholder='Search', style={'text-align':'center'})], id=id('right_header_3'), style={'display':'none'}),

                    # Body
                    dbc.CardBody(html.Div([], id=id('right_content'), style={'min-height': '650px'})),
                    dbc.CardBody(html.Div([], id=id('right_content_2'), style={'min-height': '650px', 'display': 'none'})),
                ], className='bg-dark', inverse=True),
                # , style={'overflow-x':'scroll'}
                # dbc.Card([
                #     dbc.CardHeader(html.H5('Experiments'), style={'text-align':'center'}),
                #     dbc.CardBody(html.P('experiments'), id=id('experiments')),
                #     dbc.CardFooter('Buttons'),
                # ], className='bg-info', style={'height': '450px'}),

            ], width=6),
        ]),

        # Modal (View Tabular Form Data)
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('', id=id('modal_title'))),
            dbc.ModalBody('', id=id('modal_body')),
            dbc.ModalFooter('', id=id('modal_footer')),
        ], id=id('modal'), size='xl'),

        # Modal (Select data as API input)
        html.Div([dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id={'type': id('header_value_title'), 'index': 0}), style={'text-align':'center'}),
            dbc.ModalBody(generate_datatable({'type': id('header_value_datatable'), 'index': 0}, height='800px')),
        ], id={'type': id('header_modal'), 'index': 0})], id=id('header_modal_list')),
        html.Div([dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id={'type': id('param_value_title'), 'index': 0}), style={'text-align':'center'}),
            dbc.ModalBody(generate_datatable({'type': id('param_value_datatable'), 'index': 0}, height='800px')),
        ], id={'type': id('param_modal'), 'index': 0})], id=id('param_modal_list')),
        html.Div([dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id={'type': id('body_value_title'), 'index': 0}), style={'text-align':'center'}),
            dbc.ModalBody(generate_datatable({'type': id('body_value_datatable'), 'index': 0}, height='800px')),
        ], id={'type': id('body_modal'), 'index': 0})], id=id('body_modal_list')),

    ], style={'width':'100%'}),
])



# Tab Content, Add New Datasets
@app.callback(
    Output(id('tabs_node'), 'children'),
    Output(id('tabs_node'), 'active_tab'),
    Output(id('right_content_2'), 'children'),
    Output(id('preview_store'), 'data'),
    Output(id('cytoscape'), 'selectedNodeData'),
    Output(id('do_cytoscape_reload'), 'data'),
    Input(id('cytoscape'), 'selectedNodeData'),
    Input({'type': id('type1'), 'index': ALL}, 'n_clicks'),
    Input({'type': id('type2'), 'index': ALL}, 'n_clicks'),
    Input({'type': id('button_preview'), 'index': ALL}, 'n_clicks'),
    Input({'type': id('button_preview'), 'index': ALL}, 'value'),
    Input({'type': id('button_new_dataset'), 'index': ALL}, 'n_clicks'),
    # New Dataset Inputs
    State({'type': id('name'), 'index': ALL}, 'value'),
    State({'type': id('description'), 'index': ALL}, 'value'),
    State({'type': id('documentation'), 'index': ALL}, 'value'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'isCompleted'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'upload_id'),
    State({'type': id('browse_drag_drop'), 'index': ALL}, 'fileNames'),
    State({'type': id('dropdown_method'), 'index': ALL}, 'value'),
    State({'type': id('url'), 'index': ALL}, 'value'),
    State({'type': id('header_key'), 'index': ALL}, 'value'),
    State({'type': id('header_value'), 'index': ALL}, 'value'),
    State({'type': id('header_value_position'), 'index': ALL}, 'value'),
    State({'type': id('param_key'), 'index': ALL}, 'value'),
    State({'type': id('param_value'), 'index': ALL}, 'value'),
    State({'type': id('param_value_position'), 'index': ALL}, 'value'),
    State({'type': id('body_key'), 'index': ALL}, 'value'),
    State({'type': id('body_value'), 'index': ALL}, 'value'),
    State({'type': id('body_value_position'), 'index': ALL}, 'value'),

    State(id('tabs_node'), 'active_tab'),
    State(id('right_content_2'), 'children'),
)
def generate_tabs(selectedNodeData, n_clicks_userinput_list, n_clicks_restapi_list, n_clicks_preview, dataset_type_list, button_new_dataset,
                    name_list, description_list, documentation_list,
                    isCompleted_list, upload_id_list, fileNames_list,                                               # Tabular / JSON 
                    method_list, url_list, header_key_list, header_value_list, header_value_position_list, param_key_list, param_value_list, param_value_position_list, body_key_list, body_value_list, body_value_position_list,     # REST API
                    active_tab, right_content_2):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    triggered = json.loads(triggered) if triggered.startswith('{') and triggered.endswith('}') else triggered
    tab1_disabled, tab2_disabled, tab3_disabled = True, True, True
    num_selected = len(selectedNodeData)
    preview_store = None
    do_cytoscape_reload = False
    out2 = no_update
    # active_tab = 'tab1' if active_tab is None else active_tab

    # Click Cytoscape Nodes
    if triggered == '' or triggered == id('cytoscape'):
        # If none selected
        if num_selected == 0:
            active_tab = None

        # One Node Selected
        elif num_selected == 1:
            store_session('dataset_id', selectedNodeData[0]['id'])
            if selectedNodeData[0]['type'] == 'action':
                tab2_disabled = False
                tab3_disabled = False
                active_tab = "tab2"
            else:
                tab1_disabled = False
                tab2_disabled = False
                tab3_disabled = False
                active_tab = 'tab1' if active_tab is None else active_tab

        # Multiple Nodes Selected
        elif num_selected > 1:
            if all(node['type'] != 'action' for node in selectedNodeData):
                tab1_disabled = False
                tab2_disabled = False
                tab3_disabled = False
                active_tab = 'tab1' if active_tab is None else active_tab
    
    # Click New Dataset Buttons
    elif triggered['type'] == id('type1') or triggered['type'] == id('type2'):
        tab3_disabled = False
        active_tab = "tab3"
        dataset_type = triggered['type']
        dataset_details, buttons = generate_new_dataset_inputs(id, dataset_type, extra=True)
        out2 = [buttons, html.Hr()] + dataset_details

    # Preview or Upload Button
    elif triggered['type'] == id('button_preview') or triggered['type'] == id('button_new_dataset'):
        tab1_disabled = False
        tab2_disabled = False
        tab3_disabled = False
        active_tab = 'tab1'
        dataset_type = dataset_type_list[0]

        if dataset_type == id('type1') and fileNames_list[0] is not None and isCompleted_list[0] is True: 
            df, details = process_userinput(upload_id_list[0], fileNames_list[0][0])
        elif dataset_type == id('type2'):
            df, details = process_restapi(method_list[0], url_list[0], header_key_list, header_value_list, param_key_list, param_value_list, body_key_list, body_value_list)
            
        dataset = Dataset(
            id=None,
            name=None,
            description=None,
            documentation=None,
            type='raw_userinput',
            details=None, 
            features={col:str(datatype) for col, datatype in zip(df.columns, df.convert_dtypes().dtypes)},
            expectation = {col:None for col in df.columns}, 
            index = [], 
            target = [],
            graphs = [],
        )
        preview_store = {
            'dataset_data': df.to_dict('records'),
            'dataset': dataset,
        }

        # Upload New Dataset
        if triggered['type'] == id('button_new_dataset'): 
            project_id = get_session('project_id')
            source_id = None
            if dataset_type == id('type1'): dataset_type = 'raw_userinput'
            elif dataset_type == id('type2'): dataset_type = 'raw_restapi'

            dataset_id = new_dataset(df, name_list[0], description_list[0], documentation_list[0], dataset_type, details)
            add_dataset(project_id, dataset_id)

            if any(header_value_position_list) != None or any(param_value_position_list) or any(body_value_position_list):
                for header in header_value_position_list:
                    if header is not None and header != '': 
                        source_id = header[0]['id']
                        add_edge(project_id, source_id, dataset_id)

                for param in param_value_position_list:
                    if param is not None and param != '': 
                        source_id = param[0]['id']
                        add_edge(project_id, source_id, dataset_id)
                for body in body_value_position_list:
                    if body is not None and body != '': 
                        source_id = body[0]['id']
                        add_edge(project_id, source_id, dataset_id)

            do_cytoscape_reload = True

    tab_list = [
        dbc.Tab(label="JSON", tab_id="tab1", disabled=tab1_disabled),
        dbc.Tab(label="Metadata", tab_id="tab2", disabled=tab2_disabled),
        dbc.Tab(label="Config", tab_id="tab3", disabled=tab3_disabled),
        # dbc.Tab(label="Experiments", tab_id="tab4", disabled=True),
        # dbc.Tab(label="Experiments", tab_id="tab5", disabled=True),
    ]
    return tab_list, active_tab, out2, preview_store, selectedNodeData, do_cytoscape_reload



def merge_dataset_data(node_list, merge_type='objectMerge', idRef=None):
    data = get_dataset_data(node_list[0]['id']).to_dict('records')

    try:
        if merge_type in ['objectMerge', 'overwrite']:
            for node in node_list[1:]:
                new_data = get_dataset_data(node['id']).to_dict('records')
                data = [json_merge(row, row_new, merge_type) for row, row_new in zip(data, new_data)]

        elif merge_type == 'arrayMergeByIndex':
            schema = {"mergeStrategy": merge_type}
            for node in node_list[1:]:
                new_data = get_dataset_data(node['id']).to_dict('records')
                data = jsonmerge.merge(data, new_data, schema)

        elif merge_type == 'arrayMergeById':
            schema = {"mergeStrategy": merge_type, "mergeOptions": {"idRef": idRef}}
            for node in node_list[1:]:
                new_data = get_dataset_data(node['id']).to_dict('records')
                data = jsonmerge.merge(data, new_data, schema)

        else:
            data = "TBD"

    except Exception as e:
        print(e)
        data = 'Merge Error'
    
    return data

def merge_dataset(dataset_list, merge_type='objectMerge'):
    dataset = get_document('dataset', dataset_list[0]['id'])
    dataset['changes'] = None
    for node in dataset_list[1:]:
        node['changes'] = None
        dataset = json_merge(dataset, get_document('dataset', node['id']), merge_type)
    return dataset



# Generate Node Data
@app.callback(
    Output(id('right_header_1'), 'children'),
    Output(id('dataset_data'), 'data'),
    Output(id('right_content'), 'style'),
    Output(id('right_content_2'), 'style'),
    Output(id('right_header_2'), 'style'),
    Output(id('right_header_3'), 'style'),
    Output(id('merge_type_container'), 'style'),
    Output(id('range'), 'min'),
    Output(id('range'), 'max'),
    Output(id('range'), 'value'),
    Input(id('tabs_node'), 'active_tab'),
    Input(id('range'), 'value'),
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('right_content'), 'style'),
    State(id('right_content_2'), 'style'),
    State(id('preview_store'), 'data'),
    # State(id('name'), 'value'),
)
def select_node(active_tab, range_value, merge_type, merge_idRef, selectedNodeData, out1_display, out2_display, preview_store):
    # pprint(selectedNodeData)
    name, out = [], []
    range_min, range_max = None, None
    num_selected = len(selectedNodeData)
    out1_display['display'] = 'block'
    out2_display['display'] = 'none'
    right_header_2_style, right_header_3_style = {'display': 'none'}, {'display': 'none'}
    merge_type_container_style = {'display': 'none'}
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    
    # Node Names
    if num_selected == 0:
        name = html.Div('Select a Node', className="badge border border-info text-wrap")
    elif num_selected == 1:
        name = dbc.Input(value=selectedNodeData[0]['name'], id={'type':id('node_name'), 'index': selectedNodeData[-1]['id']}, style={'font-size':'14px', 'text-align':'center'}),
        
    elif num_selected > 1:
        for node in selectedNodeData:
            name = name + [dbc.Input(value=str(len(name)+1)+') '+node['name'], disabled=True, style={'margin':'5px', 'text-align':'center'})]
        name = dbc.InputGroup(name)
    else:
        name = []

    # New/Add Dataset when No Active Tab
    if active_tab is None and num_selected == 0:
        out = dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button('Add Existing Dataset', color='warning', outline=True, id=id('button_add'), href='/apps/search', size='lg', style={'font-size': '25px', 'font-weight': 'bold', 'height':'50px', 'margin':'30px 0px 5px 0px'}),
                    dbc.Button('Manually Upload Dataset', color='warning', outline=True, id={'type': id('type1'), 'index': 0}, size='lg', style={'font-size': '25px', 'font-weight': 'bold', 'height':'50px', 'margin':'5px 0px 5px 0px'}),
                    dbc.Button('Use Rest API', color='warning', outline=True, id={'type': id('type2'), 'index': 0}, size='lg', style={'font-size': '25px', 'font-weight': 'bold', 'height':'50px', 'margin':'5px 0px 5px 0px'}),
                ], style={'width':'100%', 'width':'100%'}, vertical=True)
            ], width={'size':10, 'offset':1}),
        ])
    
    # Node Data
    elif active_tab == 'tab1' and all(node['type'] != 'action' for node in selectedNodeData):
        if preview_store is not None:
            data = preview_store['dataset_data']

        elif num_selected == 1:
            data = get_dataset_data(selectedNodeData[-1]['id']).to_dict('records')
            
        elif num_selected > 1:
            merge_type_container_style['display'] = 'block'
            data  = merge_dataset_data(selectedNodeData, merge_type, idRef=merge_idRef)
            
        range_min = 1
        range_max = len(data)
        if triggered != id('range'):
            range_value = [range_min, range_max]
        data = data[range_value[0]-1:range_value[1]]
        out = data
        right_header_2_style['display'] = 'block'
        right_header_3_style['display'] = 'block'
        

    elif active_tab == 'tab2':
        if preview_store is not None:
            dataset = preview_store['dataset']
            out = [display_metadata(dataset, id, disabled=True)]

        elif num_selected == 1:
            if selectedNodeData[0]['type'] == 'action': 
                action = get_document('action', selectedNodeData[0]['id'])
                out = [display_action(action)]
            else:
                dataset = get_document('dataset', selectedNodeData[0]['id'])
                out = [display_metadata(dataset, id, disabled=False)]

        elif num_selected > 1:
            if all(node['type'] == 'action' for node in selectedNodeData): 
                out = []

            elif all(node['type'] != 'action' for node in selectedNodeData): 
                dataset = merge_dataset(selectedNodeData)
                out = [display_metadata(dataset, id, disabled=True)]
    
    elif active_tab == 'tab3':
        out1_display['display'] = 'none'
        out2_display['display'] = 'block'

    else:
        out = []

    return name, out, out1_display, out2_display, right_header_2_style, right_header_3_style, merge_type_container_style, range_min, range_max, range_value


# Merge Type Triggers
@app.callback(
    Output(id('merge_idRef'), 'style'),
    Output(id('merge_idRef'), 'options'),
    Output(id('merge_idRef'), 'value'),
    Input(id('merge_type'), 'value'),
    State(id('dataset_data'), 'data'),
)
def merge_type_triggers(merge_type, dataset_data):
    if merge_type is None: return no_update
    style = {'display':'none', 'text-align':'center'}
    options, value = no_update, no_update
    if merge_type == 'arrayMergeById':
        style['display'] = 'block'
        df = json_normalize(dataset_data)
        options = [{'label': c, 'value': c} for c in df.columns]
        value = df.columns[0]
    return style, options, value



@app.callback(
    Output(id('right_content'), 'children'),
    Input(id('dataset_data'), 'data'),
    Input(id('button_tabular'), 'n_clicks'),
    State(id('tabs_node'), 'active_tab'),
)
def button_remove_feature(data, n_clicks, active_tab):
    if data == []: return no_update
    if active_tab is None:
        out = data
    elif active_tab == 'tab1':
        if n_clicks % 2 == 0: out = display_dataset_data(data, format='json')
        else: out = display_dataset_data(data, format='tabular')
    elif active_tab == 'tab2':
        out = data
    
    return out


@app.callback(
    Output({'type': id('col_button_remove_feature'), 'index': MATCH}, 'outline'),
    Input({'type': id('col_button_remove_feature'), 'index': MATCH}, 'n_clicks'),
)
def button_remove_feature(n_clicks):
    if n_clicks is None: return no_update
    if n_clicks % 2 == 0: return True
    else: return False


# Load Cytoscape, Button Reset, Merge
@app.callback(
    Output(id('cytoscape'), 'elements'),
    Output(id('cytoscape'), 'layout'),
    Input(id('button_load'), 'n_clicks'),
    Input(id('button_perform_action'), 'n_clicks'),
    Input('url', 'pathname'),
    Input(id('button_remove'), 'n_clicks'),
    Input(id('do_cytoscape_reload'), 'data'),
    Input({'type': id('node_name'), 'index': ALL}, 'value'),
    Input(id('merge_type'), 'value'),
    Input(id('merge_idRef'), 'value'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('tabs_node'), 'active_tab'),
    State({'type':id('col_feature_hidden'), 'index': ALL}, 'value'),
    State({'type':id('col_feature'), 'index': ALL}, 'value'),
    State({'type':id('col_datatype'), 'index': ALL}, 'value'),
    State({'type':id('col_button_remove_feature'), 'index': ALL}, 'n_clicks'),
)
def cytoscape_triggers(n_clicks_load, n_clicks_merge, pathname, n_clicks_remove, do_cytoscape_reload, node_name, merge_type, merge_idRef, selectedNodeData, active_tab, feature_list, new_feature_list, datatype_list, button_remove_feature_list):
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')
    merge_idRef = None if merge_idRef is None else merge_idRef
    
    if num_selected <= 0:
        pass
    else:
        triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
        dataset_id = selectedNodeData[0]['id']

        # On Page Load and Reset Button pressed
        if triggered == '' or triggered == id('button_load'):
            pass
        
        elif triggered == id('do_cytoscape_reload'):
            if do_cytoscape_reload == False: return no_update
        
        elif triggered == id('button_perform_action'):
            if n_clicks_merge is None: return no_update
            dataset = get_document('dataset', dataset_id)

            # Modify Metadata Action
            if num_selected == 1:
                new_dataset = dataset.copy()
                
                new_dataset['features'] = dict(zip(new_feature_list, datatype_list))

                remove_list = [feature for feature, n_clicks in zip(new_feature_list, button_remove_feature_list) if (n_clicks % 2 != 0)]
                for feature in remove_list:
                    new_dataset['features'].pop(feature, None)

                changed_feature_dict = {f1:f2 for f1, f2 in zip(feature_list, new_feature_list) if f1 != f2}
                action(project_id, dataset_id, 'metadata', 'description', new_dataset, changed_feature_dict)

            # Merge Datasets Action
            elif num_selected > 1:
                dataset_data = merge_dataset_data(selectedNodeData, merge_type, idRef=merge_idRef)
                dataset = merge_dataset(selectedNodeData, merge_type)
                source_id_list = [node['id'] for node in selectedNodeData]
                changes = {'merge_type': merge_type}
                merge(project_id, source_id_list, '', dataset_data, dataset, changes)
            

        # Button Remove Node
        elif triggered == id('button_remove'):
            node_id_list = [node['id'] for node in selectedNodeData]
            remove(project_id, node_id_list)

        # Change Dataset Name
        elif id('node_name') in triggered:
            triggered = json.loads(triggered)
            dataset_id = triggered['index']
            if all(node['type'] != 'action' for node in selectedNodeData):
                dataset = get_document('dataset', dataset_id)
                if dataset['name'] != node_name[0]:
                    dataset['name'] = node_name[0]
                    upsert('dataset', dataset)
                else: 
                    return no_update
            else:
                return no_update
                

    elements = generate_cytoscape_elements(project_id)
    layout={'name': 'breadthfirst',
        'fit': True,
        'roots': [e['data']['id'] for e in elements if e['classes'].startswith('raw_')]
    }
    return elements, layout




# # Save Cytoscape
# @app.callback(
#     Output('modal_confirm', 'children'),
#     Input(id('button_save'), 'n_clicks'),
#     State(id('cytoscape'), 'elements'),
# )
# def save_cytoscape(n_clicks, elements):
#     pprint(elements)
#     return no_update



# Disable/Enable Right Panel Buttons
# @app.callback(
#     Output(id('button_perform_action'), 'disabled'),
#     Output(id('button_chart'), 'disabled'),
#     Output(id('button_remove'), 'disabled'),
#     Input(id('tabs_node'), 'active_tab'),
#     Input('url', 'pathname'),
#     State(id('cytoscape'), 'selectedNodeData'),
# )
# def button_disable_enable(active_tab, pathname, selectedNodeData):
#     button1, button2, button3, button4 = True, True, True, True    
#     num_selected = len(selectedNodeData)

#     if num_selected == 1:
#         if active_tab == 'tab1':
#             button1, button2, button3, button4 = True, False, False, False
#         elif active_tab == 'tab2':
#             button1, button2, button3, button4 = True, False, False, False
    
#     elif num_selected > 1:
#         pass

#     return button1, button2, button3, button4 


# View in Tabular Format
# @app.callback(
#     Output(id('modal'), 'is_open'),
#     Output(id('modal_title'), 'children'),
#     Output(id('modal_body'), 'children'),
#     Output(id('modal_footer'), 'children'),
#     Input(id('button_tabular'), 'n_clicks'),
#     State(id('cytoscape'), 'selectedNodeData')
# )
# def button_tabular(n_clicks, selectedNodeData):
#     if n_clicks is None: return no_update
#     if selectedNodeData is None: return no_update
#     if len(selectedNodeData) == 0: return no_update

#     # Retrieve Dataset Data
#     if all(node['type'] != 'action' for node in selectedNodeData):
#         if len(selectedNodeData) == 1:
#             df = get_dataset_data(selectedNodeData[-1]['id'])
#             out = df.to_dict('records')
#         elif len(selectedNodeData) > 1:
#             base = []
#             for node in selectedNodeData:
#                 base = json_merge(base, get_dataset_data(node['id']).to_dict('records'), 'overwrite')
#             df = json_normalize(base)
#             out = base

#         modal_title = ""
#         modal_footer = ''
#         modal_body = html.Div(generate_datatable(id('inspect_modal_datatable'), out, df.columns, height='800px'))  
#         return True, modal_title, modal_body, modal_footer

#     else:
#         return no_update

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
@app.callback(Output('url', 'pathname'),
                Input(id('button_chart'), 'n_clicks'),
                State(id('cytoscape'), 'selectedNodeData'))
def button_chart(n_clicks, selectedNodeData):
    if n_clicks is None: return no_update
    if selectedNodeData is None: return no_update
    if len(selectedNodeData) != 1: return no_update
    if selectedNodeData[0]['type'] == 'action': return no_update

    return '/apps/plot_graph'



# Add/Remove Headers, Params, Body
@app.callback(
    Output(id('header_div'), 'children'),
    Output(id('param_div'), 'children'),
    Output(id('body_div'), 'children'),
    Output(id('header_modal_list'), 'children'),
    Output(id('param_modal_list'), 'children'),
    Output(id('body_modal_list'), 'children'),
    Input(id('button_add_header'), 'n_clicks'),
    Input(id('button_remove_header'), 'n_clicks'),
    Input(id('button_add_param'), 'n_clicks'),
    Input(id('button_remove_param'), 'n_clicks'),
    Input(id('button_add_body'), 'n_clicks'),
    Input(id('button_remove_body'), 'n_clicks'),
    State(id('header_div'), 'children'),
    State(id('param_div'), 'children'),
    State(id('body_div'), 'children'),
    State(id('header_modal_list'), 'children'),
    State(id('param_modal_list'), 'children'),
    State(id('body_modal_list'), 'children'),
)
def button_add_header(_, _2, _3, _4, _5, _6, header_div, param_div, body_div, header_modal_list, param_modal_list, body_modal_list):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '' or triggered == None: return no_update

    # Add
    if 'add' in triggered: 
        if triggered == id('button_add_header'):
            new = copy.deepcopy(header_div[-1])
            new2 = copy.deepcopy(header_modal_list[-1])
            num_inputs = len(header_div)
        elif triggered == id('button_add_param'):
            new = copy.deepcopy(param_div[-1])
            new2 = copy.deepcopy(param_modal_list[-1])
            num_inputs = len(param_div)
        elif triggered == id('button_add_body'):
            new = copy.deepcopy(body_div[-1])
            new2 = copy.deepcopy(body_modal_list[-1])
            num_inputs = len(body_div)

        new['props']['children'][0]['props']['id']['index'] = num_inputs
        new['props']['children'][1]['props']['id']['index'] = num_inputs
        new['props']['children'][2]['props']['id']['index'] = num_inputs
        new['props']['children'][3]['props']['id']['index'] = num_inputs
        new['props']['children'][0]['props']['value'] = ''
        new['props']['children'][1]['props']['value'] = ''
        new['props']['children'][3]['props']['value'] = ''
        new['props']['children'][1]['props']['valid'] = None
        new2['props']['id']['index'] = num_inputs
        new2['props']['children'][0]['props']['children']['props']['id']['index'] = num_inputs
        new2['props']['children'][1]['props']['children']['props']['children'][0]['props']['children'][0]['props']['id']['index'] = num_inputs
        new2['props']['children'][1]['props']['children']['props']['children'][0]['props']['children'][0]['props']['selected_cells'] = []

        if triggered == id('button_add_header'):
            header_div = header_div + [new]
            header_modal_list = header_modal_list + [new2]
        elif triggered == id('button_add_param'):
            param_div =  param_div + [new]
            param_modal_list = param_modal_list + [new2]
        elif triggered == id('button_add_body'):
            body_div = body_div + [new]
            body_modal_list = body_modal_list + [new2]

    # Remove
    if triggered == id('button_remove_header'):
        if len(header_div) > 1: header_div = header_div[:-1]
        if len(header_modal_list) > 1: header_modal_list = header_modal_list[:-1]
    elif triggered == id('button_remove_param'):
        if len(param_div) > 1: param_div = param_div[:-1]
        if len(param_modal_list) > 1: param_modal_list = param_modal_list[:-1]
    elif triggered == id('button_remove_body'):
        if len(body_div) > 1: body_div = body_div[:-1]
        if len(body_modal_list) > 1: body_modal_list = body_modal_list[:-1]

    # Remove n_clicks
    for i in range(len(header_div)):
        header_div[i]['props']['children'][2]['props']['n_clicks'] = None
    for i in range(len(param_div)):
        param_div[i]['props']['children'][2]['props']['n_clicks'] = None
    for i in range(len(body_div)):
        body_div[i]['props']['children'][2]['props']['n_clicks'] = None

    return header_div, param_div, body_div, header_modal_list, param_modal_list, body_modal_list








# Open Modal
@app.callback(
    Output({'type':id('header_modal'), 'index': MATCH}, 'is_open'),
    Output({'type':id('header_value_title'), 'index': MATCH}, 'children'),
    Output({'type':id('header_value_datatable'), 'index': MATCH}, 'data'),
    Output({'type':id('header_value_datatable'), 'index': MATCH}, 'columns'),
    Input({'type':id('button_header_value'), 'index': MATCH}, 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def button_open_modal(n_clicks, selectedNodeData):
    num_selected = len(selectedNodeData)
    if callback_context.triggered[0]['value'] is None: return no_update
    if num_selected != 1: return no_update

    df = get_dataset_data(selectedNodeData[0]['id'])
    columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]
    return True, selectedNodeData[0]['name'], df.to_dict('records'), columns

@app.callback(
    Output({'type':id('param_modal'), 'index': MATCH}, 'is_open'),
    Output({'type':id('param_value_title'), 'index': MATCH}, 'children'),
    Output({'type':id('param_value_datatable'), 'index': MATCH}, 'data'),
    Output({'type':id('param_value_datatable'), 'index': MATCH}, 'columns'),
    Input({'type':id('button_param_value'), 'index': MATCH}, 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def button_open_modal(n_clicks, selectedNodeData):
    num_selected = len(selectedNodeData)
    if callback_context.triggered[0]['value'] is None: return no_update
    if num_selected != 1: return no_update
    
    df = get_dataset_data(selectedNodeData[0]['id'])
    columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]
    return True, selectedNodeData[0]['name'], df.to_dict('records'), columns

@app.callback(
    Output({'type':id('body_modal'), 'index': MATCH}, 'is_open'),
    Output({'type':id('body_value_title'), 'index': MATCH}, 'children'),
    Output({'type':id('body_value_datatable'), 'index': MATCH}, 'data'),
    Output({'type':id('body_value_datatable'), 'index': MATCH}, 'columns'),
    Input({'type':id('button_body_value'), 'index': MATCH}, 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def button_open_modal(n_clicks, selectedNodeData):
    num_selected = len(selectedNodeData)
    if callback_context.triggered[0]['value'] is None: return no_update
    if num_selected != 1: return no_update
    
    df = get_dataset_data(selectedNodeData[0]['id'])
    columns = [{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns]
    return True, selectedNodeData[0]['name'], df.to_dict('records'), columns



# Get Selected Inputs in Modal into Header, Paramter, Body values
@app.callback(
    Output({'type':id('header_value'), 'index': MATCH}, 'value'),
    Output({'type':id('header_value'), 'index': MATCH}, 'valid'),
    Output({'type':id('header_value_position'), 'index': MATCH}, 'value'),
    # Output({'type':id('header_value_datatable'), 'index': MATCH}, 'selected_cells'),
    Input({'type':id('header_value_datatable'), 'index': MATCH}, 'selected_cells'),
    Input({'type':id('header_value'), 'index': MATCH}, 'value'),
    State({'type':id('header_value_datatable'), 'index': MATCH}, 'data'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def button_select_input(selected_cells, header_value, data, selectedNodeData):
    if callback_context.triggered[0]['prop_id'] == '.': return no_update
    if selected_cells is None: return no_update
    if len(selected_cells) <= 0: return no_update
    triggered = json.loads(callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0])
    out, valid, position = no_update, None, no_update

    if triggered['type'] == id('header_value'):
        position = ''

    elif triggered['type'] == id('header_value_datatable'):
        out = ''
        if selected_cells is not None:
            df = json_normalize(data)
            for cell in selected_cells:
                out = out + str(df.iloc[cell['row'], cell['column']]) + ','
            out = out[:-1]
            valid = True
            position = [{'row': cell['row'], 'col': cell['column'], 'id': selectedNodeData[0]['id']} for cell in selected_cells]
        else:
            valid = None
            
    return out, valid, position

@app.callback(
    Output({'type':id('param_value'), 'index': MATCH}, 'value'),
    Output({'type':id('param_value'), 'index': MATCH}, 'valid'),
    Output({'type':id('param_value_position'), 'index': MATCH}, 'value'),
    Input({'type':id('param_value_datatable'), 'index': MATCH}, 'selected_cells'),
    Input({'type':id('param_value'), 'index': MATCH}, 'value'),
    State({'type':id('param_value_datatable'), 'index': MATCH}, 'data'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def button_select_input(selected_cells, header_value, data, selectedNodeData):
    if callback_context.triggered[0]['prop_id'] == '.': return no_update
    if selected_cells is None: return no_update
    if len(selected_cells) <= 0: return no_update
    triggered = json.loads(callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0])
    out, valid, position = no_update, None, no_update

    if triggered['type'] == id('param_value'):
        position = ''

    elif triggered['type'] == id('param_value_datatable'):
        out = ''
        if selected_cells is not None:
            df = json_normalize(data)
            for cell in selected_cells:
                out = out + str(df.iloc[cell['row'], cell['column']]) + ','
            out = out[:-1]
            valid = True
            position = [{'row': cell['row'], 'col': cell['column'], 'id': selectedNodeData[0]['id']} for cell in selected_cells]
        else:
            valid = None
            
    return out, valid, position

@app.callback(
    Output({'type':id('body_value'), 'index': MATCH}, 'value'),
    Output({'type':id('body_value'), 'index': MATCH}, 'valid'),
    Output({'type':id('body_value_position'), 'index': MATCH}, 'value'),
    Input({'type':id('body_value_datatable'), 'index': MATCH}, 'selected_cells'),
    Input({'type':id('body_value'), 'index': MATCH}, 'value'),
    State({'type':id('body_value_datatable'), 'index': MATCH}, 'data'),
    State(id('cytoscape'), 'selectedNodeData'),
)
def button_select_input(selected_cells, header_value, data, selectedNodeData):
    if callback_context.triggered[0]['prop_id'] == '.': return no_update
    if selected_cells is None: return no_update
    if len(selected_cells) <= 0: return no_update
    triggered = json.loads(callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0])
    out, valid, position = no_update, None, no_update

    if triggered['type'] == id('body_value'):
        position = ''

    elif triggered['type'] == id('body_value_datatable'):
        out = ''
        if selected_cells is not None:
            df = json_normalize(data)
            for cell in selected_cells:
                out = out + str(df.iloc[cell['row'], cell['column']]) + ','
            out = out[:-1]
            valid = True
            position = [{'row': cell['row'], 'col': cell['column'], 'id': selectedNodeData[0]['id']} for cell in selected_cells]
        else:
            valid = None
            
    return out, valid, position



# # Button Preview/Add
# @app.callback(
#     Output({'type': id('button_preview'), 'index': 0}, 'n_clicks'),
#     Input({'type': id('browse_drag_drop'), 'index': ALL}, 'isCompleted'),
#     State({'type': id('button_preview'), 'index': 0}, 'n_clicks'),
# )
# def drag_drop(isCompleted, n_clicks):
#     if len(isCompleted) == 0: return no_update
#     if isCompleted[0] is True:
#         # if n_clicks is None: n_clicks = 0
#         return 1



# Generate options in dropdown and button 
@app.callback(
    Output(id('dropdown_action'), 'children'),
    Input(id('cytoscape'), 'selectedNodeData'),
    # Input(id('dropdown_action'), 'children')
)
def generate_dropdown_actions(selected_nodes):
    if selected_nodes is None: return no_update
    
    single = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==False ]
    multiple = [ nav for nav in SIDEBAR_2_LIST  if nav['multiple']==True ]
    
    # Generate Options
    options = []
    if len(selected_nodes) == 0:
        options = [dbc.DropdownMenuItem('Add Data Source', href='#', id=id('button_add_data_source'))]
    if len(selected_nodes) == 1:
        options = [dbc.DropdownMenuItem(nav['label'], href=nav['value']) for nav in single]
        options.append(dbc.DropdownMenuItem(divider=True))
        options.append(dbc.DropdownMenuItem('Remove', href='#', id=id('button_remove'), style={'background-color':'red', 'padding':'1px 0px 1px 0px', 'text-align':'center'}))
    elif len(selected_nodes) > 1 and all(node['type'] != 'action' for node in selected_nodes):
        options = [dbc.DropdownMenuItem(nav['label'], href=nav['value']) for nav in multiple]

    return options



