from dash import dcc
#import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output, State
from pandas import json_normalize
from apps.util import *
from app import app
from app import server 
from app import dbc # https://dash-bootstrap-components.opensource.faculty.ai/docs/quickstart/
from apps.typesense_client import *
from apps import (upload_dataset, upload_api, overview, profile, merge_strategy, temporal_evolution, temporal_merge, 
                decomposition, impute_data, remove_duplicate, data_lineage,
                page2, page3, page6, page6,page7, page8, page9, page10)
import ast


id = id_factory('index')

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 40,
    "left": 0,
    "bottom": 0,
    "width": "14rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "font-size": "0.9em",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# Define path for images used
HOMEPAGELOGO = "../assets/static/polymath-ai-0research-logo.svg"
YOUTUBE = "../assets/static/youtube-icon.svg"
GITHUB = "../assets/static/github-icon.svg"
DOCKER = "../assets/static/docker-icon.svg"
GITHUBACTION = "../assets/static/githubaction-icon.svg"


# Top Navbar
navbar = dbc.Navbar([
    dbc.Row([
        dbc.Col(html.A(html.Img(src=HOMEPAGELOGO, height="30px", id="tooltip-homepagelogo"), href="https://0research.com"),  width={'size':1, "order": "1"}),
        dbc.Col(html.A(dbc.NavbarBrand("AI-SDK", className='font-weight-bold', id="tooltip-navbarbrand"), href="https://ai-sdk.herokuapp.com"),  width={'size':1, "order": "1"}),
        dbc.Col(html.A(html.Img(src=YOUTUBE, height="30px",id="tooltip-youtube"), href="https://www.youtube.com/watch?v=ntN3xPEyy3U"),  width={'size':1, "order": "1"}),
        dbc.Col(dbc.DropdownMenu([
            dbc.DropdownMenuItem('v4', href="http://demo789.0research.com"),
            dbc.DropdownMenuItem('v3', href="http://demo788.0research.com"),
            dbc.DropdownMenuItem('v2', href='http://demo787.0research.com'),
            dbc.DropdownMenuItem('v1', href='http://demo786.0research.com'),
        ], label="Choose Version"), width={"size": 1, "order": "1"}),

        dbc.Col(html.A(html.Img(src=GITHUB, height="30px",id="tooltip-github"), href="https://github.com/0research/ai-sdk"), width={"size": 1, "order": "1"}),
        dbc.Col(html.A(html.Img(src=DOCKER, height="30px",id="tooltip-docker"), href="https://hub.docker.com/r/0research/ai-sdk"), width={"size": 1, "order": "1"}),
        dbc.Col(html.A(html.Img(src=GITHUBACTION, height="30px",id="tooltip-githubaction"), href="https://github.com/marketplace/actions/ai-sdk-action"), width={"size": 1, "order": "1"}),
        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Choose Dataset"),
            dbc.Select(options=[], id='dropdown_current_dataset', style={'min-width':'120px'}, persistence_type='session', persistence=True),
        ]), width={"size": 2, "order": "4", 'offset': 2}),

        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Node"),
            dbc.Input(id='display_current_node', disabled=True, style={'text-align':'center'})
        ]), width={"size": 2, "order": "4", 'offset': 0}, style={'margin-right':'30px', 'height':'100%'}),

        # dbc.Col(dbc.Button("Workflow", href='/apps/workflow', color="info", className="btn btn-info", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'}), width={"size": 1, "order": "4", 'offset':3}),
        # dbc.Col(dbc.Button("Data Lineage", href='/apps/data_lineage', color="primary", className="btn btn-primary", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'}), width={"size": 1, "order": "5", 'offset':0}),
        dbc.Col(dbc.Input(type="search", placeholder="Search...", style={'text-align':'center'}), width={"size": 3, "order": "5", 'offset':0})
    ], className='g-0', style={'width':'100%'}),

    # Tool tips for each Icon
    dbc.Tooltip("0Research Homepage",target="tooltip-homepagelogo"),
    dbc.Tooltip("CloudApp Homepage",target="tooltip-navbarbrand"),
    dbc.Tooltip("Demo Video",target="tooltip-youtube"),
    dbc.Tooltip("Opensource Repo",target="tooltip-github"),
    dbc.Tooltip("Self Hosted Docker",target="tooltip-docker"),
    dbc.Tooltip("Use in GithubAction",target="tooltip-githubaction"),
    ], color="dark", dark=True,)
    


# Sidebar
sidebar_1 = [
    dbc.NavLink("Upload Dataset", href="/apps/upload_dataset", id=id('nav_upload'), active="exact", className="fas fa-upload"),
    dbc.NavLink("Data Lineage", href="/apps/data_lineage", active="exact", className="fas fa-database"),
    dbc.NavLink("Overview", href="/apps/overview", active="exact", className="fas fa-chart-pie"),
]
sidebar_2 = [dbc.NavLink(nav['label'], href=nav['value'], active='exact', className=nav['className']) for nav in sidebar_2_list]
sidebar_3 = [
    dbc.NavLink("Workflow", href="/apps/workflow", active="exact", className="fas fa-arrow-alt-circle-right"),
    dbc.NavLink("Remove Duplicate", href="/apps/remove_duplicate", active="exact", className='far fa-copy'),
    dbc.NavLink("Decomposition", href="/apps/decomposition", active="exact", className='fas fa-recycle'),
    dbc.NavLink("Balance Dataset", href="/apps/balance_dataset", active="exact", className='fas fa-chess-knight'),
    dbc.NavLink("Anomaly Detection", href="/apps/anomaly_detection", active="exact", className='fas fa-chess-knight'),
    dbc.NavLink("Split Dataset", href="/apps/split_dataset", active="exact", className='fas fa-recycle'),
    dbc.NavLink("Model Evaluation", href="/apps/model_evaluation", active="exact", className='fas fa-recycle'),
]
sidebar = html.Div([
    dbc.Nav(
        [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})] +
        sidebar_1 +
        [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})] +
        sidebar_2 +
        [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})] +
        sidebar_3 +
        [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})]
        
        # dcc.Link(' Page 3 | ', href='/apps/page3'),
        # dcc.Link('Page 6 | ', href='/apps/page6'),
        # dcc.Link('Merge Strategy | ', href='/apps/page7'),
        # dcc.Link('Temporal Merge | ', href='/apps/page8'),
        # dcc.Link('Temporal Evolution | ', href='/apps/page9'),
        # dcc.Link('Page 10 | ', href='/apps/page10'),
    , vertical=True, pills=True),
], style=SIDEBAR_STYLE)


def doOne():
    return 'one'

# Layout
def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='current_dataset', storage_type='session'),
        dcc.Store(id='current_node', storage_type='session'),
        sidebar,
        navbar,
        html.Div(id='page-content', style=CONTENT_STYLE),
        #dbc.Container(dbc.Alert("Wrangle Data!", color="success"),className="p-5") #Added by Sagun
    ])
app.layout = serve_layout


@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname.startswith('/apps/upload_dataset'): return upload_dataset.layout
    if pathname.startswith('/apps/upload_api'): return upload_api.layout
    if pathname.startswith('/apps/overview'): return overview.layout
    if pathname.startswith('/apps/profile'): return profile.layout
    if pathname.startswith('/apps/merge_strategy'): return merge_strategy.layout
    if pathname.startswith('/apps/temporal_evolution'): return temporal_evolution.layout
    if pathname.startswith('/apps/decomposition'): return decomposition.layout
    if pathname.startswith('/apps/impute_data'): return impute_data.layout
    if pathname.startswith('/apps/remove_duplicate'): return remove_duplicate.layout
    if pathname.startswith('/apps/data_lineage'): return data_lineage.layout

    # if pathname == '/apps/page3': return page3.layout
    # if pathname == '/apps/temporal_merge': return temporal_merge.layout
    # if pathname == '/apps/page2': return page2.layout
    # if pathname == '/apps/page6': return page6.layout
    # if pathname == '/apps/page7': return page7.layout
    # if pathname == '/apps/page8': return page8.layout
    # if pathname == '/apps/page9': return page9.layout
    # if pathname == '/apps/page10': return page10.layout
    # if pathname == '/apps/git_graph': return git_graph.layout
    else: return merge_strategy.layout



# # If Click Upload, remove Current Dataset/Node
# @app.callback(Output('dropdown_current_dataset', 'value'),
#                 Output('display_current_node', 'value'),
#                 Input(id('nav_upload'), 'n_clicks'))
# def load_dataset_dropdown(n_clicks):
#     if n_clicks is None: return no_update
#     return '', ''



# Load Datasets in dropdown
@app.callback([Output('dropdown_current_dataset', 'options')],
                Input('url', 'pathname'),)
def load_dataset_dropdown(pathname):
    dataset_list = search_documents('dataset', 250)
    options = [{'label': d['id'], 'value': d['id']} for d in dataset_list]
    return options




# Load Last Node ID if change Selected Dataset
@app.callback([Output('display_current_node', 'value')],
                [Input('current_dataset', 'data')])
def load_nodeID(dataset_id):
    if dataset_id is None: return no_update
    dataset = client.collections['dataset'].documents[dataset_id].retrieve()
    node_list = ast.literal_eval(dataset['node'])
    if len(node_list) == 0: return ''
    else: return node_list[-1]


# Save Current Dataset/Node IDs to store
@app.callback([Output('current_dataset', 'data')],
                Input('dropdown_current_dataset', 'value'),)
def load_dataset_dropdown(dataset_id):
    return dataset_id
@app.callback([Output('current_node', 'data')],
                Input('display_current_node', 'value'),)
def load_dataset_dropdown(node_id):
    return node_id


# Selected Dataset
# @app.callback([Output('dropdown_current_dataset', 'options'),
#                 Output('current_dataset', 'data')],
#                 [Input('current_dataset', 'data'),
#                 Input('dropdown_current_dataset', 'value')])
# def current_dataset(current_dataset, selected):
#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

#     options = no_update
#     dataset_name_list = [c['name'] for c in client.collections.retrieve()]
#     if len(dataset_name_list) == 0: current_dataset = None # If no dataset exist
#     else: current_dataset = dataset_name_list[0]   # By Default take first dataset in typesense

#     if selected is None: selected = current_dataset
    
#     if triggered == 'current_dataset':
#         options = [{'label':name, 'value':name} for name in dataset_name_list]
#     elif triggered == 'dropdown_current_dataset':
#         pass
    
#     return options, selected

# @app.callback(Output('current_dataset', 'data'), Input('url', 'pathname'))
# def doSomething(pathname):
#     print('aaaa')
#     return {'abc':'123'}


# # Display_selected_node
# @app.callback(Output('current_node_id', "value"),
#                 [Input('current_dataset', "data"),
#                 Input('current_node', 'data'),])
# def generate_load_node_id(metadata, selected_node):
#     # If New Dataset, Generate random Node number
#     if (metadata['node']) == 0:
#         return 123
#     else:
#         return selected_node


if __name__ == '__main__':
    app.run_server("0.0.0.0", 8889, debug=True)
    







