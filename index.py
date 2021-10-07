import dash_core_components as dcc
#import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from pandas.io.json import json_normalize
from apps.util import *
from app import app
from app import server 
from app import dbc # https://dash-bootstrap-components.opensource.faculty.ai/docs/quickstart/

from apps import (upload_data, merge_strategy, temporal_evolution, temporal_merge, 
                time_series_decomposition, impute_time_series_missing_data, remove_duplicate, data_lineage,
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



sidebar = html.Div([
    html.H5("AI-SDK", className="display-4"),
    html.Hr(),
    dbc.Nav([
        dbc.NavLink("Upload Data", href="/apps/upload_data", active="exact"),
        dbc.NavLink("Merge Strategy", href="/apps/merge_strategy", active="exact"),
        dbc.NavLink("Temporal Evolution", href="/apps/temporal_evolution", active="exact"),
        dbc.NavLink("Impute Missing Data", href="/apps/impute_time_series_missing_data", active="exact"),
        dbc.NavLink("Time Series Decomposition", href="/apps/time_series_decomposition", active="exact"),
        dbc.NavLink("Remove Duplicate", href="/apps/remove_duplicate", active="exact"),
        dbc.NavLink("Data Lineage", href="/apps/data_lineage", active="exact"),

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
        html.Div(id='page-content', style=CONTENT_STYLE),
        #dbc.Container(dbc.Alert("Wrangle Data!", color="success"),className="p-5") #Added by Sagun
    ])

#https://dash-bootstrap-components.opensource.faculty.ai/docs/quickstart/
# To use dash-bootstrap-components you must do two things:
#    1.Link a Bootstrap v4 compatible stylesheet (example code shown below)
#    2.Incorporate dash-bootstrap-components into the layout of your app.(already done in app.py)

# app.layout = dbc.Container(
#     dbc.Alert("Wrangle Data!", color="success"),
#     className="p-5",
# )

app.layout = serve_layout


@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/upload_data': return upload_data.layout
    if pathname == '/apps/merge_strategy': return merge_strategy.layout
    if pathname == '/apps/temporal_evolution': return temporal_evolution.layout
    if pathname == '/apps/time_series_decomposition': return time_series_decomposition.layout
    if pathname == '/apps/impute_time_series_missing_data': return impute_time_series_missing_data.layout
    if pathname == '/apps/remove_duplicate': return remove_duplicate.layout
    if pathname == '/apps/data_lineage': return data_lineage.layout

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



if __name__ == '__main__':
    app.run_server(debug=True)






