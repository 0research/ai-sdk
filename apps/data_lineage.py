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
import copy

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

id = id_factory('data_lineage')

    

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
            'shape': 'rectangle',
            'content': 'data(action)'
        }
    },
    

]


layout = html.Div([
    html.Div([
        dcc.Store(id=id('new_dataset_type_store'), storage_type='session', data=id('type1')),
        dbc.Row([
            dbc.Col([
                html.H5('Data Lineage (Data Flow Experiments)', style={'text-align':'center', 'display':'inline-block', 'margin':'0px 0px 0px 40px'}),
                html.Div([
                    # html.Button('Add Dataset', id=id('button_upload'), className='btn btn-primary btn-lg', style={'margin-right':'1px'}), 
                    html.Button('Reset', id=id('button_reset'), className='btn btn-secondary btn-lg', style={'margin-right':'1px'}),
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

            dbc.Col([
                html.Div([
                    html.Div(dbc.Tabs([], id=id("tabs_node")), style={'float':'left', 'text-align':'left', 'display':'inline-block'}),
                    html.Div([
                        dbc.Button(html.I(n_clicks=0, className='fas fa-check'), id=id('button_perform_action'), className='btn btn-warning', style={'margin-left':'1px'}),
                        dbc.Button(html.I(n_clicks=0, className='fa fa-table'), id=id('button_tabular'), className='btn btn-info', style={'margin-left':'1px'}),
                        dbc.Button(html.I(n_clicks=0, className='fas fa-chart-area'), id=id('button_chart'), className='btn btn-success', style={'margin-left':'1px'}),
                        dbc.Button(html.I(n_clicks=0, className='fas fa-times'), id=id('button_remove'), className='btn btn-danger', style={'margin-left':'1px'}),
                        dbc.Tooltip('Perform Action', target=id('button_perform_action')),
                        dbc.Tooltip('View in Tabular Format', target=id('button_tabular')),
                        dbc.Tooltip('Chart', target=id('button_chart')),
                        dbc.Tooltip('Remove Action or Raw Dataset', target=id('button_remove')),
                    ], style={'float':'right', 'text-align':'right', 'display':'inline-block'}),
                ], style={'display':'inline-block', 'width':'100%'}),
                
                dbc.Card([
                    dbc.CardHeader([html.P(id=id('node_name_list'), style={'text-align':'center', 'font-size':'13px', 'font-weight':'bold', 'float':'left', 'width':'100%'})]),
                    dbc.CardBody(html.Div(id=id('node_content'), style={'min-height': '750px'})),
                    dbc.CardBody(html.Div(id=id('node_content2'), style={'min-height': '750px', 'display': 'none'})),
                ], className='bg-primary', inverse=True),
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
        html.Div([dbc.Modal([], id={'type': id('header_modal'), 'index': 0})], id=id('header_modal_list')),
        html.Div([dbc.Modal([], id={'type': id('param_modal'), 'index': 0})], id=id('param_modal_list')),
        html.Div([dbc.Modal([], id={'type': id('body_modal'), 'index': 0})], id=id('body_modal_list')),

    ], style={'width':'100%'}),
])


    

# Generate Tabs & Store Selected Node into Session
@app.callback(
    Output(id('tabs_node'), 'children'),
    Output(id('tabs_node'), 'active_tab'),
    Output(id('node_content2'), 'children'),
    Input(id('cytoscape'), 'selectedNodeData'),
    Input({'type': id('type1'), 'index': ALL}, 'n_clicks'),
    Input({'type': id('type2'), 'index': ALL}, 'n_clicks'),
    State(id('tabs_node'), 'active_tab'),
)
def generate_tabs(selectedNodeData, n_clicks_userinput_list, n_clicks_restapi_list, active_tab):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    tab1_disabled, tab2_disabled, tab3_disabled = True, True, True
    num_selected = len(selectedNodeData)
    new_dataset_type_store = no_update
    out2 = no_update
    # active_tab = 'tab1' if active_tab is None else active_tab

    # Click Cytoscape Nodes
    if triggered == '' or triggered == id('cytoscape'):
        # If none selected
        if num_selected == 0:
            active_tab = None

        # One Node Selected
        elif num_selected == 1:
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
    
    # Click Add/New Dataset Buttons
    else:
        tab3_disabled = False
        active_tab = "tab3"
        dataset_type = json.loads(triggered)['type']
        dataset_details, buttons = generate_new_dataset_inputs(id, dataset_type, extra=True)
        out2 = [buttons, html.Hr()] + dataset_details

    tab_list = [
        dbc.Tab(label="JSON", tab_id="tab1", disabled=tab1_disabled),
        dbc.Tab(label="Metadata", tab_id="tab2", disabled=tab2_disabled),
        dbc.Tab(label="New Dataset", tab_id="tab3", disabled=tab3_disabled),
    ]
    return tab_list, active_tab, out2






# Generate Node Data
@app.callback(
    Output(id('node_name_list'), 'children'),
    Output(id('node_content'), 'children'),
    Output(id('node_content'), 'style'),
    Output(id('node_content2'), 'style'),
    Input(id('tabs_node'), 'active_tab'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('new_dataset_type_store'), 'data'),
    State(id('node_content'), 'style'),
    State(id('node_content2'), 'style'),
)
def select_node(active_tab, selectedNodeData, dataset_type, out1_display, out2_display):
    # pprint(selectedNodeData)
    name, out = [], []
    num_selected = len(selectedNodeData)
    out1_display['display'] = 'block'
    out2_display['display'] = 'none'
    # Node Names
    if num_selected == 0:
        name = html.Div('Select a Node', className="badge border border-info text-wrap")
    elif num_selected == 1:
        name = html.Div(selectedNodeData[0]['name'], contentEditable='true', id={'type':id('node_name'), 'index': selectedNodeData[-1]['id']}, className="badge border border-info text-wrap")
    elif num_selected > 1:
        for node in selectedNodeData:
            name = name + [html.Div([
                html.P(str(len(name)+1)+')', style={'display':'inline-block', 'font-size':'10px'}),
                html.P(node['name'], id={'type':id('node_name'), 'index': node['id']}, style={'margin':'5px', 'display':'inline-block'}),
            ], style={'display':'inline-block'}, className="badge border border-info text-wrap")]
    else:
        name = []

    # New/Add Dataset when No Active Tab
    if active_tab is None and num_selected == 0:
        out = dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button('Use Existing Dataset', color='warning', outline=True, id=id('button_add'), href='/apps/search', size='lg', style={'font-size': '25px', 'font-weight': 'bold', 'height':'50px', 'margin':'30px 0px 5px 0px'}),
                    dbc.Button('Manually Upload Dataset', color='warning', outline=True, id={'type': id('type1'), 'index': 0}, size='lg', style={'font-size': '25px', 'font-weight': 'bold', 'height':'50px', 'margin':'5px 0px 5px 0px'}),
                    dbc.Button('Use Rest API', color='warning', outline=True, id={'type': id('type2'), 'index': 0}, size='lg', style={'font-size': '25px', 'font-weight': 'bold', 'height':'50px', 'margin':'5px 0px 5px 0px'}),
                ], style={'width':'100%', 'width':'100%'}, vertical=True)
            ], width={'size':10, 'offset':1}),
        ])
    
    # Node Data
    elif active_tab == 'tab1' and all(node['type'] != 'action' for node in selectedNodeData):
        if num_selected == 1:
            data = get_dataset_data(selectedNodeData[-1]['id']).to_dict('records')
            
        elif num_selected > 1:
            options_merge = [{'label': o, 'value': o} for o in MERGE_TYPES]
            data = get_dataset_data(selectedNodeData[0]['id']).to_dict('records')
            for node in selectedNodeData[1:]:
                new_data = get_dataset_data(node['id']).to_dict('records')
                data = [json_merge(row, row_new, 'objectMerge') for row, row_new in zip(data, new_data)]
                out = [dbc.Select(options=options_merge, value=options_merge[0]['value'], placeholder='Select Merge Type', style={'text-align':'center'})]

        out = out + [dbc.Input(id=id('search_json'), placeholder='Search', style={'text-align':'center'})] + [display_dataset_data_store(data)]

    elif active_tab == 'tab2':
        if num_selected == 1:
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
                dataset = get_document('dataset', selectedNodeData[0]['id'])
                dataset['changes'] = None
                for node in selectedNodeData[1:]:
                    node['changes'] = None
                    dataset = json_merge(dataset, get_document('dataset', node['id']), 'objectMerge')
                out = [display_metadata(dataset, id, disabled=True)]
    
    elif active_tab == 'tab3':
        out1_display['display'] = 'none'
        out2_display['display'] = 'block'

    else:
        out = []

    return name, out, out1_display, out2_display





@app.callback(
    Output({'type': id('col_button_remove_feature'), 'index': MATCH}, 'className'),
    Input({'type': id('col_button_remove_feature'), 'index': MATCH}, 'n_clicks')
)
def button_remove_feature(n_clicks):
    if n_clicks % 2 == 0: return 'btn btn-outline-danger'
    else: return 'btn btn-danger'


# Load Cytoscape, Button Reset, Merge
@app.callback(
    Output(id('cytoscape'), 'elements'),
    Output(id('cytoscape'), 'layout'),
    Input(id('button_reset'), 'n_clicks'),
    Input(id('button_perform_action'), 'n_clicks'),
    Input('url', 'pathname'),
    Input(id('button_remove'), 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
    State(id('tabs_node'), 'active_tab'),
    State({'type':id('col_feature_hidden'), 'index': ALL}, 'value'),
    State({'type':id('col_feature'), 'index': ALL}, 'value'),
    State({'type':id('col_datatype'), 'index': ALL}, 'value'),
    State({'type':id('col_button_remove_feature'), 'index': ALL}, 'n_clicks'),
)
def generate_cytoscape(n_clicks_reset, n_clicks_merge, pathname, n_clicks_remove, selectedNodeData, active_tab, feature_list, new_feature_list, datatype_list, button_remove_feature_list):
    num_selected = len(selectedNodeData)
    project_id = get_session('project_id')

    if num_selected <= 0:
        pass
    else:
        triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
        dataset_id = selectedNodeData[0]['id']
        

        # On Page Load and Reset Button pressed
        if triggered == '' or triggered == id('button_reset'):
            pass

        
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
                dataset['changes'] = None
                data = get_dataset_data(selectedNodeData[0]['id']).to_dict('records')
                for node in selectedNodeData[1:]:
                    node['changes'] = None
                    dataset = json_merge(dataset, get_document('dataset', node['id']), 'objectMerge')
                    new_data = get_dataset_data(node['id']).to_dict('records')
                    data = [json_merge(row, row_new, 'objectMerge') for row, row_new in zip(data, new_data)]

                source_id_list = [node['id'] for node in selectedNodeData]
                changes = { 'merge_type': 'objectMerge'}
                merge(project_id, source_id_list, '', data, dataset, changes)
            

        # Button Remove Node
        elif triggered == id('button_remove') and num_selected == 1:
            remove(project_id, selectedNodeData[0]['id'])

        # Change Dataset Name TODO
        elif triggered == id('aa'):
            pass
            # Input({'type': id('node_name'), 'index': ALL }, 'children'),


    elements = generate_cytoscape_elements(project_id)
    layout={'name': 'breadthfirst',
        'fit': True,
        'roots': [e['data']['id'] for e in elements if e['classes'].startswith('raw_')]
    }
    return elements, layout






# Disable/Enable Right Panel Buttons
# @app.callback(
#     Output(id('button_perform_action'), 'disabled'),
#     Output(id('button_tabular'), 'disabled'),
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
            df = get_dataset_data(selectedNodeData[-1]['id'])
            out = df.to_dict('records')
        elif len(selectedNodeData) > 1:
            base = []
            for node in selectedNodeData:
                base = json_merge(base, get_dataset_data(node['id']).to_dict('records'), 'overwrite')
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



# Add/Remove Headers, Params, Body
@app.callback(
    Output(id('header_div'), 'children'),
    Output(id('params_div'), 'children'),
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
    State(id('params_div'), 'children'),
    State(id('body_div'), 'children'),
    State(id('header_modal_list'), 'children'),
    State(id('param_modal_list'), 'children'),
    State(id('body_modal_list'), 'children'),
)
def button_add_header(_, _2, _3, _4, _5, _6, header_div, params_div, body_div, header_modal_list, param_modal_list, body_modal_list):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    print("ASASAS")
    # Add
    if triggered == id('button_add_header'):
        new = copy.deepcopy(header_div[-1])
        new2 = copy.deepcopy(header_modal_list[-1])
        new['props']['children'][0]['props']['id']['index'] = len(header_div)
        new['props']['children'][1]['props']['id']['index'] = len(header_div)
        new['props']['children'][2]['props']['id']['index'] = len(header_div)
        new['props']['children'][0]['props']['value'] = ''
        new['props']['children'][1]['props']['value'] = ''
        # for i in range(len(header_div)):
        #     header_div[i]['props']['children'][2]['props']['n_clicks'] = 0
        new2['props']['id']['index'] = len(header_modal_list)
        header_div = header_div + [new]
        header_modal_list = header_modal_list + [new2]

    elif triggered == id('button_add_param'):
        new = copy.deepcopy(params_div[-1])
        new2 = copy.deepcopy(param_modal_list[-1])
        new['props']['children'][0]['props']['id']['index'] = len(params_div)
        new['props']['children'][1]['props']['id']['index'] = len(params_div)
        new['props']['children'][2]['props']['id']['index'] = len(params_div)
        new['props']['children'][0]['props']['value'] = ''
        new['props']['children'][1]['props']['value'] = ''
        new2['props']['id']['index'] = len(param_modal_list)
        params_div =  params_div + [new]
        param_modal_list = param_modal_list + [new2]

    elif triggered == id('button_add_body'):
        new = copy.deepcopy(body_div[-1])
        new2 = copy.deepcopy(body_modal_list[-1])
        new['props']['children'][0]['props']['id']['index'] = len(body_div)
        new['props']['children'][1]['props']['id']['index'] = len(body_div)
        new['props']['children'][2]['props']['id']['index'] = len(body_div)
        new['props']['children'][0]['props']['value'] = ''
        new['props']['children'][1]['props']['value'] = ''
        new2['props']['id']['index'] = len(body_modal_list)
        body_div = body_div + [new]
        body_modal_list = body_modal_list + [new2]

    # Remove
    elif triggered == id('button_remove_header'):
        if len(header_div) > 1: header_div = header_div[:-1]
        if len(header_modal_list) > 1: header_modal_list = header_modal_list[:-1]
    elif triggered == id('button_remove_param'):
        if len(params_div) > 1: params_div = params_div[:-1]
        if len(param_modal_list) > 1: param_modal_list = param_modal_list[:-1]
    elif triggered == id('button_remove_body'):
        if len(body_div) > 1: body_div = body_div[:-1]
        if len(body_modal_list) > 1: body_modal_list = body_modal_list[:-1]

    return header_div, params_div, body_div, header_modal_list, param_modal_list, body_modal_list





# Open Modal
@app.callback(
    Output({'type':id('header_modal'), 'index': ALL}, 'is_open'),
    Output({'type':id('header_modal'), 'index': ALL}, 'children'),
    Input({'type':id('button_header_value'), 'index': ALL}, 'n_clicks'),
    State(id('cytoscape'), 'selectedNodeData'),
    State({'type':id('header_modal'), 'index': ALL}, 'is_open'),
    State({'type':id('header_modal'), 'index': ALL}, 'children'),
)
def button_open_modal(n_clicks_list, selectedNodeData, modal_is_open_list, modal_list):
    
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0] if len(callback_context.triggered) == 1 else None
    print('TRIGGERED: ' , triggered, n_clicks_list)
    num_selected = len(selectedNodeData)
    if triggered == '' or triggered is None or num_selected != 1: return no_update
    triggered = json.loads(triggered)
    index = triggered['index']
    if n_clicks_list[index] is None: return no_update

    

    modal_is_open_list[index] = True
    df = get_dataset_data(selectedNodeData[0]['id'])
    modal_list[index] = [
        dbc.ModalHeader(dbc.ModalTitle(selectedNodeData[0]['name']), style={'text-align':'center'}),
        dbc.ModalBody(generate_datatable({'type': id('datatable_select_inputs'), 'index': index}, df.to_dict('records'), df.columns, height='800px')),
        # dbc.ModalFooter(dbc.Button('Add Inputs', color='primary', outline=True, id=id('button_add_inputs'), style={'width':'100%'})),
    ]
    return modal_is_open_list, modal_list

@app.callback(
    Output({'type':id('param_value'), 'index': MATCH}, 'value'),
    Input({'type':id('button_param_value'), 'index': MATCH}, 'n_clicks'),
)
def button_open_modal(_):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '': return no_update
    return True
@app.callback(
    Output({'type':id('body_value'), 'index': MATCH}, 'value'),
    Input({'type':id('button_body_value'), 'index': MATCH}, 'n_clicks'),
)
def button_open_modal(_):
    triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]
    if triggered == '': return no_update
    return True


# Open Modal
@app.callback(
    Output({'type':id('header_value'), 'index': MATCH}, 'value'),
    Input({'type':id('datatable_select_inputs'), 'index': MATCH}, 'selected_cells'),
    State({'type':id('datatable_select_inputs'), 'index': MATCH}, 'data'),
)
def button_select_input(selected_cells, data):
    if selected_cells is None: return no_update
    df = json_normalize(data)
    out = ''
    for cell in selected_cells:
        out = out + str(df.iloc[cell['row'], cell['column']]) + ','
    return out[:-1]




# Button Preview/Add
@app.callback(
    Output(id('button_preview'), 'n_clicks'),
    Input({'type': id('browse_drag_drop'), 'index': ALL}, 'isCompleted'),
    State(id('button_preview'), 'n_clicks'),
)
def drag_drop(isCompleted, n_clicks):
    if len(isCompleted) == 0: return no_update
    if isCompleted[0] is True:
        # if n_clicks is None: n_clicks = 0
        return 1



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





