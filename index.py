import dash_core_components as dcc
#import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from pandas.io.json import json_normalize
from apps.util import *
from app import app
from app import server 
from app import dbc # https://dash-bootstrap-components.opensource.faculty.ai/docs/quickstart/

from apps import (upload_data, overview, merge_strategy, temporal_evolution, temporal_merge, 
                time_series_decomposition, impute_time_series_missing_data, remove_duplicate, data_explorer,
                page2, page3, page4, page6, page6,page7, page8, page9, page10)


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
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

search_bar = dbc.Row([
    dbc.Col(dbc.Button("Workflow", href='/apps/workflow', color="info", className="btn btn-info", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'})),
    dbc.Col(dbc.Button("Data Explorer", href='/apps/data_explorer', color="primary", className="btn btn-primary", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'})),
    dbc.Col(dbc.Input(type="search", placeholder="Search")) ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

# imp_links = dbc.Row([
#     dbc.Col(dbc.Button("Workflow", href='/apps/workflow', color="info", className="btn btn-info", active="exact", style={'width':'130px', 'text-decoration':'none', 'font-size':'16px'})),


navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=HOMEPAGELOGO, height="30px", id="tooltip-homepagelogo")), # Link to Home Page of Website href='https://0research.com'
                    dbc.Col(dbc.NavbarBrand("AI-SDK", className="ml-2",id="tooltip-navbarbrand")), # Link to App href='https://ai-sdk.herokuapp.com'
                    dbc.Col(html.Img(src=YOUTUBE, height="30px",id="tooltip-youtube")), # Link to Demo Youtuve Video href='https://www.youtube.com/watch?v=ntN3xPEyy3U'
                    dbc.Col(html.Img(src=GITHUB, height="30px",id="tooltip-github")), # Link to href='https://github.com/0research/ai-sdk'
                    dbc.Col(html.Img(src=DOCKER, height="30px",id="tooltip-docker"),href="https://hub.docker.com/r/0research/ai-sdk"), # Link to href='https://hub.docker.com/r/0research/ai-sdk'
                    dbc.Col(html.Img(src=GITHUBACTION, height="30px",id="tooltip-githubaction")), # Link to href='https://github.com/marketplace/actions/ai-sdk-action'
                ],
                align="center",
                no_gutters=True,
            ),
            #href="https://www.youtube.com/watch?v=ntN3xPEyy3U"
            ), 
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        dbc.Collapse(search_bar, id="navbar-collapse", navbar=True, is_open=False),
        

        ## Href Links for each Icon
        dbc.NavLink(target="tooltip-github", href="https://github.com/0research/ai-sdk"),

        ## Tool tips for each Icon
        dbc.Tooltip("0Research Homepage",target="tooltip-homepagelogo"),
        dbc.Tooltip("CloudApp Homepage",target="tooltip-navbarbrand"),
        dbc.Tooltip("Demo Video",target="tooltip-youtube"),
        dbc.Tooltip("Opensource Repo",target="tooltip-github"),
        dbc.Tooltip("Self Hosted Docker",target="tooltip-docker"),
        dbc.Tooltip("Use in GithubAction",target="tooltip-githubaction"),
    ],
    color="dark",
    dark=True,
)

sidebar = html.Div([
    dbc.Nav([
        html.Hr(),
        dbc.NavLink("Upload Data", href="/apps/upload_data", active="exact", className="fas fa-upload"),
        dbc.NavLink("Overview", href="/apps/overview", active="exact", className="fas fa-chart-pie"),
        dbc.NavLink("Merge Strategy", href="/apps/merge_strategy", active="exact", className='fas fa-chess-knight'),
        dbc.NavLink("Temporal Evolution", href="/apps/temporal_evolution", active="exact", className='far fa-clock'),
        dbc.NavLink("Impute Missing Data", href="/apps/impute_time_series_missing_data", active="exact", className='fas fa-search-plus'),
        dbc.NavLink("Remove Duplicate", href="/apps/remove_duplicate", active="exact", className='far fa-copy'),
        dbc.NavLink("Time Series Decomposition", href="/apps/time_series_decomposition", active="exact", className='fas fa-recycle'),
        # dbc.NavLink("Data Lineage", href="/apps/data_explorer", active="exact", className='fas fa-history'),

        # dcc.Link(' Page 3 | ', href='/apps/page3'),
        # dcc.Link(' Page 4 | ', href='/apps/page4'),
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
    # if pathname == '/apps/page4': return page4.layout
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






