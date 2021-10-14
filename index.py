from dash import dcc
#import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output, State
from pandas import json_normalize
from apps.util import *
from app import app
from app import server 
from app import dbc # https://dash-bootstrap-components.opensource.faculty.ai/docs/quickstart/

from apps import (upload_data, overview, merge_strategy, temporal_evolution, temporal_merge, 
                time_series_decomposition, impute_time_series_missing_data, remove_duplicate, data_explorer,
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

navbar_right = dbc.Row([
    dbc.Col(dbc.Button("Workflow", href='/apps/workflow', color="info", className="btn btn-info", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'})),
    dbc.Col(dbc.Button("Data Explorer", href='/apps/data_explorer', color="primary", className="btn btn-primary", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'})),
    dbc.Col(dbc.Input(type="search", placeholder="Search")) ],
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

# imp_links = dbc.Row([
#     dbc.Col(dbc.Button("Workflow", href='/apps/workflow', color="info", className="btn btn-info", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'})),


navbar = dbc.Navbar([
    html.A(dbc.Row([dbc.Col(html.Img(src=HOMEPAGELOGO, height="30px", id="tooltip-homepagelogo"))], align="center"), href="https://0research.com"), # Link to Home Page of Website href='https://0research.com'
    html.A(dbc.Row([dbc.Col(dbc.NavbarBrand("AI-SDK", className="ml-2",id="tooltip-navbarbrand"))], align="center"), href="https://ai-sdk.herokuapp.com"), # Link to App href='https://ai-sdk.herokuapp.com' 
    html.A(dbc.Row([dbc.Col(html.Img(src=YOUTUBE, height="30px",id="tooltip-youtube"))], align="center"), href="https://www.youtube.com/watch?v=ntN3xPEyy3U"), # Link to Demo Youtuve Video href='https://www.youtube.com/watch?v=ntN3xPEyy3U'
    dbc.Row(html.Label('Choose Version', id="tooltip-choose-video-version", style={'color':'white'})),
    html.A(dbc.Row(dbc.Col([dcc.Dropdown(options=[
        {'label': 'v4', 'value': 'http://demo789.0research.com'},
        {'label': 'v3', 'value': 'http://demo788.0research.com'},
        {'label': 'v2', 'value': 'http://demo787.0research.com'},
        {'label': 'v1', 'value': 'http://demo786.0research.com'}
    ], value='http://demo789.0research.com', clearable=False)]), align="center"), style={'width':'75px'}),
    html.A(dbc.Row([dbc.Col(html.Img(src=GITHUB, height="30px",id="tooltip-github"))], align="center"),href="https://github.com/0research/ai-sdk"), # Link to href='https://github.com/0research/ai-sdk'
    html.A(dbc.Row([dbc.Col(html.Img(src=DOCKER, height="30px",id="tooltip-docker"))], align="center"), href="https://hub.docker.com/r/0research/ai-sdk"), # Link to href='https://hub.docker.com/r/0research/ai-sdk'
    html.A(dbc.Row([dbc.Col(html.Img(src=GITHUBACTION, height="30px",id="tooltip-githubaction"))], align="center"), href="https://github.com/marketplace/actions/ai-sdk-action"), # Link to href='https://github.com/marketplace/actions/ai-sdk-action'

    navbar_right,

    ## Href Links for each Icon
    #dbc.NavLink(target="tooltip-github", href="https://github.com/0research/ai-sdk"),

    ## Tool tips for each Icon
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
        dbc.NavLink("Upload Data", href="/apps/upload_data", active="exact", className="fas fa-upload"),
        dbc.NavLink("Workflow", href="/apps/workflow", active="exact", className="fas fa-arrow-alt-circle-right"),
        dbc.NavLink("Data Explorer", href="/apps/data_explorer", active="exact", className="fas fa-database"),
        html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'}),
        dbc.NavLink("Overview", href="/apps/overview", active="exact", className="fas fa-chart-pie"),
        dbc.NavLink("Merge Strategy", href="/apps/merge_strategy", active="exact", className='fas fa-chess-knight'),
        dbc.NavLink("Temporal Evolution", href="/apps/temporal_evolution", active="exact", className='far fa-clock'),
        dbc.NavLink("Impute Missing Data", href="/apps/impute_time_series_missing_data", active="exact", className='fas fa-search-plus'),
        dbc.NavLink("Remove Duplicate", href="/apps/remove_duplicate", active="exact", className='far fa-copy'),
        dbc.NavLink("Time Series Decomposition", href="/apps/time_series_decomposition", active="exact", className='fas fa-recycle'),
        # dbc.NavLink("Data Lineage", href="/apps/data_explorer", active="exact", className='fas fa-history'),

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
        dcc.Store(id='input_data_store', storage_type='session'),
        sidebar,
        navbar,
        html.Div(id='page-content', style=CONTENT_STYLE),
        #dbc.Container(dbc.Alert("Wrangle Data!", color="success"),className="p-5") #Added by Sagun
    ])



app.layout = serve_layout


@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/upload_data': return upload_data.layout
    if pathname == '/apps/overview': return overview.layout
    if pathname == '/apps/merge_strategy': return merge_strategy.layout
    if pathname == '/apps/temporal_evolution': return temporal_evolution.layout
    if pathname == '/apps/time_series_decomposition': return time_series_decomposition.layout
    if pathname == '/apps/impute_time_series_missing_data': return impute_time_series_missing_data.layout
    if pathname == '/apps/remove_duplicate': return remove_duplicate.layout

    if pathname == '/apps/data_explorer': return data_explorer.layout

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


# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True)
    







