# import dash_core_components as dcc
# import dash_html_components as html
# from dash.dependencies import Input, Output, State
# import plotly.express as px
# import pandas as pd
# from app import app
# import collections


# def generate_tabs(tabs_id, tab_labels, tab_id):
#     return dcc.Tabs(
#         id=tabs_id,
#         children=[
#             dcc.Tab(label=label, id=tab_id) for label, value in zip(tab_labels, tab_id)
#         ]
#     )


# # Layout
# tab_labels = ['tab one', 'tab two', 'tab three']
# tab_values = ['tab-' + str(i) for i in range(1, len(tab_labels)+1)]
# layout = html.Div([
#     html.H1('Page2', style={"textAlign": "center"}),
#     generate_tabs('tabs-1', tab_labels, tab_values),
#     html.Div(id='tabs2Div')
# ])


# @app.callback(
#     Output('tabs2Div', 'children'),
#     Input('tabs-1', 'value')
# )
# def render_tabs(active_tab):
#     # Temporarily simulate dynamic tab values & sort
#     import random
#     n_tabs = random.randint(2, 7)
#     tab_labels = random.sample(range(10, 99), n_tabs)
#     tab_values = ['tab--' + str(i) for i in range(n_tabs)]

#     if active_tab == 'tab-1':
#         pass
#     if active_tab == 'tab-2':
#         pass
#     if active_tab == 'tab-3':
#         pass

#     tabs_info = collections.OrderedDict(sorted(dict(zip(tab_labels, tab_values)).items()))

#     return generate_tabs('tabs-2', map(str, list(tabs_info.keys())), list(tabs_info.values()))

