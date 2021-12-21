from os import times_result
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from pandas import json_normalize
from apps.util import *
from app import app
from app import server 
from app import dbc
from apps.typesense_client import *
from apps import (new_project, new_dataset, upload_dataset, join, search, extract_transform, plot_graph, dashboard, profile, merge_strategy, temporal_evolution, temporal_merge, 
                decomposition, impute_data, remove_duplicate, data_lineage,
                page2, page3, page6, page6,page7, page8, page9, test)
import ast
from apps.constants import *



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
    "margin-left": "14rem",
    "margin-right": "10px",
    "padding": "1rem 0rem",
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
            dbc.InputGroupText("Project"),
            dbc.Select(options=[], id='dropdown_current_project', style={'min-width':'120px'}, persistence_type='session', persistence=True),
        ]), width={"size": 2, "order": "4", 'offset': 2}),

        # dbc.Col(dbc.InputGroup([
        #     dbc.InputGroupText("Dataset"),
        #     dbc.Input(id='display_current_dataset', disabled=True, style={'text-align':'center'})
        # ]), width={"size": 2, "order": "4", 'offset': 0}, style={'margin-right':'30px', 'height':'100%'}),

        # dbc.Col(dbc.Button("Workflow", href='/apps/workflow', color="info", className="btn btn-info", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'}), width={"size": 1, "order": "4", 'offset':3}),
        # dbc.Col(dbc.Button("Data Lineage", href='/apps/data_lineage', color="primary", className="btn btn-primary", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'}), width={"size": 1, "order": "5", 'offset':0}),
        dbc.Col(dbc.Input(type="search", id='search', debounce=True, placeholder="Search...", style={'text-align':'center'}), width={"size": 3, "order": "5", 'offset':0})
    ], className='g-0', style={'width':'100%'}, id='navbar_top'),

    # Tool tips for each Icon
    dbc.Tooltip("0Research Homepage",target="tooltip-homepagelogo"),
    dbc.Tooltip("CloudApp Homepage",target="tooltip-navbarbrand"),
    dbc.Tooltip("Demo Video",target="tooltip-youtube"),
    dbc.Tooltip("Opensource Repo",target="tooltip-github"),
    dbc.Tooltip("Self Hosted Docker",target="tooltip-docker"),
    dbc.Tooltip("Use in Github Action",target="tooltip-githubaction"),
], color="dark", dark=True,)
    

# Sidebar
sidebar_0 = [
    dbc.NavLink("New Project", href="/apps/new_project", active="exact", className="fas fa-upload"),
    # dbc.NavLink("New Dataset", href="/apps/new_dataset", active="exact", className="fas fa-upload"),
    dbc.NavLink("Data Catalog", href="/apps/search", active="exact", className="fas fa-upload"),
]
sidebar_1 = [
    dbc.NavLink("Data Lineage", href="/apps/data_lineage", active="exact", className="fas fa-database"),
    dbc.NavLink("Dashboard", href="/apps/dashboard", active="exact", className="fas fa-chart-pie"),
    # dbc.NavLink("Add Dataset", href="/apps/upload_dataset", active="exact", className="fas fa-upload"),
    dbc.NavLink("Plot Graph", href="/apps/plot_graph", active="exact", className="fas fa-upload"),
]
sidebar_2 = [dbc.NavLink(nav['label'], href=nav['value'], active='exact', className=nav['className'], disabled=nav['disabled']) for nav in SIDEBAR_2_LIST]
sidebar_3 = [dbc.NavLink(nav['label'], href=nav['value'], active='exact', className=nav['className']) for nav in SIDEBAR_3_LIST]
sidebar_4 = [
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
        sidebar_0 +
        [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})] +
        sidebar_1 +
        [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})] +
        sidebar_2 +
        [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})] +
        sidebar_3 +
        # [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})] +
        sidebar_4 +
        [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})] 
        
        # dcc.Link(' Page 3 | ', href='/apps/page3'),
        # dcc.Link('Page 6 | ', href='/apps/page6'),
        # dcc.Link('Merge Strategy | ', href='/apps/page7'),
        # dcc.Link('Temporal Merge | ', href='/apps/page8'),
        # dcc.Link('Temporal Evolution | ', href='/apps/page9'),
        # dcc.Link('Page 10 | ', href='/apps/page10'),
    , vertical=True, pills=True, id='sidebar'),
], style=SIDEBAR_STYLE)



# Layout
def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='search_str_store', storage_type='session'),
        dbc.Modal('', id='modal_confirm'),
        sidebar,
        navbar,
        html.Div(id='page-content', style=CONTENT_STYLE),
        #dbc.Container(dbc.Alert("Wrangle Data!", color="success"),className="p-5") #Added by Sagun
    ])
app.layout = serve_layout


@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname.startswith('/apps/new_project'): return new_project.layout
    if pathname.startswith('/apps/new_dataset'): return new_dataset.layout
    if pathname.startswith('/apps/upload_dataset'): return upload_dataset.layout
    if pathname.startswith('/apps/dashboard'): return dashboard.layout
    if pathname.startswith('/apps/profile'): return profile.layout
    if pathname.startswith('/apps/join'): return join.layout
    if pathname.startswith('/apps/plot_graph'): return plot_graph.layout
    if pathname.startswith('/apps/search'): return search.layout
    
    if pathname.startswith('/apps/impute_data'): return impute_data.layout
    if pathname.startswith('/apps/extract_transform'): return extract_transform.layout
    
    if pathname.startswith('/apps/merge_strategy'): return merge_strategy.layout
    if pathname.startswith('/apps/temporal_evolution'): return temporal_evolution.layout
    if pathname.startswith('/apps/decomposition'): return decomposition.layout
    
    if pathname.startswith('/apps/remove_duplicate'): return remove_duplicate.layout
    if pathname.startswith('/apps/data_lineage'): return data_lineage.layout

    # if pathname == '/apps/page3': return page3.layout
    # if pathname == '/apps/temporal_merge': return temporal_merge.layout
    # if pathname == '/apps/page2': return page2.layout
    # if pathname == '/apps/page6': return page6.layout
    # if pathname == '/apps/page7': return page7.layout
    # if pathname == '/apps/page8': return page8.layout
    # if pathname == '/apps/page9': return page9.layout
    if pathname == '/apps/test': return test.layout
    # if pathname == '/apps/git_graph': return git_graph.layout
    else: return data_lineage.layout



# Highlight Active Navigation
@app.callback(
    Output('sidebar', 'children'),
    Input('url', 'pathname'),
    State('sidebar', 'children'),
)
def highlight_active_nav(pathname, sidebar):
    for i in range(len(sidebar)):
        if 'className' in sidebar[i]['props']:
            if sidebar[i]['props']['href'] == pathname:
                sidebar[i]['props']['className'] + ' active'
    return sidebar


# Load Projects Options in dropdown
@app.callback([Output('dropdown_current_project', 'options')],
                Input('url', 'pathname'),)
def load_dataset_dropdown(pathname):
    dataset_list = search_documents('project', 250)
    options = [{'label': d['id'], 'value': d['id']} for d in dataset_list]
    return options

# Store Project ID Session on selecting dropdown
@app.callback(Output('modal_confirm', 'children'),
                Input('dropdown_current_project', 'value'))
def load_dataset_dropdown(project_id):
    if project_id is None or project_id == '': return no_update
    store_session('project_id', project_id)
    # project_list = search_documents('project', 250)
    
    return no_update

# Load Project ID and Node ID
@app.callback(Output('dropdown_current_project', 'value'),
                Input('url', 'pathname'))
def load_project_id(pathname):
    return get_session('project_id')

# Search Function
@app.callback(
    Output('url', 'pathname'),
    Output('search_str_store', 'data'),
    Input('search', 'value')
)
def load_project_id(value):
    if value == '' or value is None: return no_update
    return '/apps/search', value

if __name__ == '__main__':
    app.run_server("0.0.0.0", 8889, debug=True)
    

