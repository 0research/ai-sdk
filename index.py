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
from apps import (upload, overview, profile, merge_strategy, temporal_evolution, temporal_merge, 
                decomposition, impute_data, remove_duplicate, data_lineage,
                page2, page3, page6, page6,page7, page8, page9, page10)


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
            dbc.Select(options=[], id='dropdown_current_dataset', style={'min-width':'120px'}),
        ]), width={"size": 2, "order": "4", 'offset': 3}),

        dbc.Col(dbc.InputGroup([
            dbc.InputGroupText("Node"),
            dbc.Input(id='display_current_node', disabled=True, style={'text-align':'center'})
        ]), width={"size": 1, "order": "4", 'offset': 0}, style={'margin-right':'30px', 'height':'100%'}),

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
    

sidebar = html.Div([
    dbc.Nav([
        html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'}),

        dbc.NavLink("Upload", href="/apps/upload", active="exact", className="fas fa-upload"),
        dbc.NavLink("Data Lineage", href="/apps/data_lineage", active="exact", className="fas fa-database"),
        dbc.NavLink("Overview", href="/apps/overview", active="exact", className="fas fa-chart-pie"),
        
        html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'}),

        dbc.NavLink("Profile", href="/apps/profile", active="exact", className='fas fa-chess-knight'),
        dbc.NavLink("Merge Strategy", href="/apps/merge_strategy", active="exact", className='fas fa-chess-knight'),
        dbc.NavLink("Temporal Evolution", href="/apps/temporal_evolution", active="exact", className='far fa-clock'),
        dbc.NavLink("Impute Data", href="/apps/impute_data", active="exact", className='fas fa-search-plus'),

        html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'}),

        dbc.NavLink("Workflow", href="/apps/workflow", active="exact", className="fas fa-arrow-alt-circle-right"),
        dbc.NavLink("Remove Duplicate", href="/apps/remove_duplicate", active="exact", className='far fa-copy'),
        dbc.NavLink("Decomposition", href="/apps/decomposition", active="exact", className='fas fa-recycle'),
        dbc.NavLink("Balance Dataset", href="/apps/balance_dataset", active="exact", className='fas fa-chess-knight'),
        dbc.NavLink("Anomaly Detection", href="/apps/anomaly_detection", active="exact", className='fas fa-chess-knight'),
        dbc.NavLink("Split Dataset", href="/apps/split_dataset", active="exact", className='fas fa-recycle'),
        dbc.NavLink("Model Evaluation", href="/apps/model_evaluation", active="exact", className='fas fa-recycle'),
        
        # dcc.Link(' Page 3 | ', href='/apps/page3'),
        # dcc.Link('Page 6 | ', href='/apps/page6'),
        # dcc.Link('Merge Strategy | ', href='/apps/page7'),
        # dcc.Link('Temporal Merge | ', href='/apps/page8'),
        # dcc.Link('Temporal Evolution | ', href='/apps/page9'),
        # dcc.Link('Page 10 | ', href='/apps/page10'),
    ], vertical=True, pills=True),
], style=SIDEBAR_STYLE)


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
    if pathname == '/apps/upload': return upload.layout
    if pathname == '/apps/overview': return overview.layout
    if pathname == '/apps/profile': return profile.layout
    if pathname == '/apps/merge_strategy': return merge_strategy.layout
    if pathname == '/apps/temporal_evolution': return temporal_evolution.layout
    if pathname == '/apps/decomposition': return decomposition.layout
    if pathname == '/apps/impute_data': return impute_data.layout
    if pathname == '/apps/remove_duplicate': return remove_duplicate.layout
    if pathname == '/apps/data_lineage': return data_lineage.layout

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



# Load Current/Selected Dataset
# @app.callback([Output('dropdown_current_dataset', 'value'),
#                 Output('dropdown_current_dataset', 'options'),
#                 Output('current_dataset', 'data')],
#                 [Input('current_dataset', 'data'),
#                 Input('dropdown_current_dataset', 'value')])
# def current_dataset(current_dataset, selected):
#     triggered = callback_context.triggered[0]['prop_id'].rsplit('.', 1)[0]

#     dataset_name_list = [c['name'] for c in client.collections.retrieve()]
#     current_dataset = dataset_name_list[0]  # By Default take first dataset in typesense
#     options = no_update
#     if selected is None: selected = current_dataset
    
    
#     if triggered == 'current_dataset':
#         options = [{'label':name, 'value':name} for name in dataset_name_list]
#     elif triggered == 'dropdown_current_dataset':
#         pass

#     return selected, options, selected

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
    







