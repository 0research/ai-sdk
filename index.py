from os import times_result
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from pandas import json_normalize
from apps.util import *
from app import app
from app import server 
from app import dbc

from apps import (admin_panel, new_project, search, dashboard, data_flow, test)
import ast
from apps.constants import *

from apps import *
from healthcheck import HealthCheck, EnvironmentDump

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for
import urllib.parse


id = id_factory('index')


# Top Navbar
navbar = dbc.Navbar([
    html.Div([
        html.A(html.Img(src=HOMEPAGELOGO, height="30px", id="tooltip-homepagelogo"), href="https://0research.com"),
        html.A(dbc.NavbarBrand("AI-SDK", className='font-weight-bold', id="tooltip-navbarbrand"), href="#"),
        dbc.Tooltip("0Research Homepage",target="tooltip-homepagelogo"),
        dbc.Tooltip("CloudApp Homepage",target="tooltip-navbarbrand"),
    ], className='navbar'),

    html.Div([
        dbc.Input(type="search", id='search', debounce=True, placeholder="Search...", disabled=True, style={'text-align':'center'}),
    ], className='navbar center'),

    html.Div([
        dbc.Button("Login", href="/login", id='login', color='secondary', className='me-1', size='lg', style={'width':'100px', 'font-weight':'bold'}),
    ], className='navbar right'),

], color="dark", dark=True, style={'width':'100%', 'height':'4vh'})
    

# Sidebar
sidebar_0 = [
    dbc.NavLink("Project", href="/apps/new_project", active="exact", className="fas fa-upload"),
    # dbc.NavLink("Admin Panel", href="/apps/admin_panel", active="exact", className="fas fa-upload", disabled=True),
]
sidebar_1 = [
    dbc.NavLink("Data Flow", href="/apps/data_flow", active="exact", className="fas fa-database"),
    dbc.NavLink("Dashboard", href="/apps/dashboard", active="exact", className="fas fa-chart-pie"),
    # dbc.NavLink("Storyboard", href="/apps/storyboard", active="exact", className="fas fa-chart-pie", disabled=True),
]
divider = [html.Hr(style={'border': '1px dotted black', 'margin': '17px 0px 17px 0px'})]

sidebar = html.Div([
    dbc.Nav(
        sidebar_0 + divider +
        sidebar_1 + divider
    , vertical=True, pills=True, id='sidebar'),
], className='sidebar')



# Layout
def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='search_str_store', storage_type='session'),
        dbc.Modal('', id='modal'),
        sidebar,
        navbar,
        html.Div(id='page-content', className='page-content'),
        #dbc.Container(dbc.Alert("Wrangle Data!", color="success"),className="p-5") #Added by Sagun
    ])
app.layout = serve_layout



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



# Search Function
@app.callback(
    Output('url', 'pathname'),
    Output('search_str_store', 'data'),
    Input('search', 'value')
)
def load_project_id(value):
    if value == '' or value is None: return no_update
    return '/apps/search', value










    
server.secret_key = AUTH0_SECRET_KEY
oauth = OAuth(server)
oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{AUTH0_DOMAIN}/.well-known/openid-configuration'
)


@server.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@server.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

@server.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@server.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))



@app.callback(
    Output('login', 'children'),
    Output('login', 'href'),
    Input('url', 'pathname'),
    State('url', 'href'),
)
def toggle_login(pathname, href):
    base = urllib.parse.urljoin(href, '/')
    if 'user' in session:
        return 'Logout', base+'logout'
    else:
        return 'Login', base+'login'



@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if 'user' not in session: return 'Please Login.'

    if pathname.startswith('/apps/new_project'): return new_project.layout
    if pathname.startswith('/apps/data_flow'): return data_flow.layout
    if pathname.startswith('/apps/admin_panel'): return admin_panel.layout
    if pathname.startswith('/apps/dashboard'): return dashboard.layout
    if pathname.startswith('/apps/search'): return search.layout
    if pathname.startswith('/apps/test'): return test.layout

    # if pathname.startswith('/apps/impute_data'): return impute_data.layout
    # if pathname.startswith('/apps/profile'): return profile.layout
    # if pathname.startswith('/apps/plot_graph'): return plot_graph.layout
    # if pathname.startswith('/apps/merge_strategy'): return merge_strategy.layout
    # if pathname.startswith('/apps/temporal_evolution'): return temporal_evolution.layout
    # if pathname.startswith('/apps/decomposition'): return decomposition.layout
    # if pathname.startswith('/apps/remove_duplicate'): return remove_duplicate.layout
    # if pathname == '/apps/test': return test.layout

    else: return new_project.layout


if __name__ == '__main__':
    health = HealthCheck()
    envdump = EnvironmentDump()
    app.server.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: health.run())
    app.server.add_url_rule("/environment", "environment", view_func=lambda: envdump.run())

    client = initialize_typesense()

    port = os.environ.get("PORT", 8050)
    app.run_server("0.0.0.0", port, debug=True, threaded=True)
