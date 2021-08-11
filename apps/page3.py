# import dash_core_components as dcc
# import dash_html_components as html
# from dash.dependencies import Input, Output, State
# import plotly.express as px
# import pandas as pd
# from app import app
# import json_dash
# import json
# from flatten_json import flatten, unflatten, unflatten_list
# from jsonmerge import Merger
# from pprint import pprint
#
# app.scripts.config.serve_locally = True
# app.css.config.serve_locally = True
#
#
# def generate_tab(label, value):
#     return dcc.Tab(
#                 label=label,
#                 value=value,
#                 className='custom-tab',
#                 selected_className='custom-tab--selected'
#             )
#
#
# def generate_tabs(tabs_id, tab_labels, tab_values):
#     return dcc.Tabs(
#         id=tabs_id,
#         parent_className='custom-tabs',
#         className='custom-tabs-container',
#         children=[
#             generate_tab(label, value) for label, value in zip(tab_labels, tab_values)
#         ]
#     )
#
#
# def get_data(filedir):
#     with open(filedir) as f:
#         data = json.load(f)
#     for i in range(len(data)):
#         data[i]['raw_response'] = json.loads(data[i]['raw_response'])
#
#     return data
#
#
# # Layout
# data = get_data('datasets/cntr1_dataprovider.json')
# tab_labels = ['Original', 'Flattened', 'Overwrite', 'Version', 'Append', 'arrayMergeById', 'arrayMergeByIndex', 'objectMerge']
# tab_values = ['tab-' + str(i) for i in range(1, len(tab_labels)+1)]
# layout = html.Div([
#     html.H1('Merge Strategies', style={"textAlign": "center"}),
#     generate_tabs('tabs-1', tab_labels, tab_values),
#     html.Div(id='jsonEditorDiv', children=[
#         # html.Button('Submit', id='button'),
#         # html.Div(dcc.Input(id='input-box', type='text')),
#         json_dash.jsondash(
#             id = 'json',
#             json = data,
#             height = 700,
#             width = 1000,
#             selected_node = '',
#         ),
#         html.Div('', id='node_selected')
#     ])
# ])
#
#
# def flatten_json(data):
#     for i in range(len(data)):
#         data[i] = flatten(data[i])
#     return data
#
#
# def overwrite_json(data):
#     schema = {'mergeStrategy': 'overwrite'}
#     base = None
#     merger = Merger(schema)
#     for i in range(len(data)):
#         base = merger.merge(base, [data[i]])
#     return base
#
#
# def version_json(data):
#     schema = {'mergeStrategy': 'version'}
#     base = None
#     merger = Merger(schema)
#     for i in range(len(data)):
#         base = merger.merge(base, data[i], merge_options={'version': {'metadata': {'revision': i}}})
#     return base
#
# def append_json(data):
#     schema = {'mergeStrategy': 'append'}
#     base = None
#     merger = Merger(schema)
#     for i in range(len(data)):
#         base = merger.merge(base, [data[i]])
#     return base
#
#
# def arrayMergeById_json(data):
#     schema = {'mergeStrategy': 'arrayMergeById'}
#     base = None
#     merger = Merger(schema)
#     for i in range(len(data)):
#         base = merger.merge(base, [data[i]])
#     return base
#
#
# def arrayMergeByIndex_json(data):
#     schema = {'mergeStrategy': 'arrayMergeByIndex'}
#     base = None
#     merger = Merger(schema)
#     for i in range(len(data)):
#         base = merger.merge(base, [data[i]])
#     return base
#
#
# def objectMerge_json(data):
#     schema = {'mergeStrategy': 'objectMerge'}
#     base = None
#     merger = Merger(schema)
#     for i in range(len(data)):
#         base = merger.merge(base, data[i])
#     return base
#
# @app.callback(
#     Output('json', 'json'),
#     Input('tabs-1', 'value')
# )
# def render_tabs(active_tab):
#     data = get_data('datasets/cntr1_dataprovider.json')
#
#     if active_tab == 'tab-2':
#         data = flatten_json(data)
#     if active_tab == 'tab-3':
#         data = flatten_json(data)
#         data = overwrite_json(data)
#
#     if active_tab == 'tab-4':
#         data = flatten_json(data)
#         data = version_json(data)
#     if active_tab == 'tab-5':
#         data = flatten_json(data)
#         data = append_json(data)
#     if active_tab == 'tab-6':
#         data = flatten_json(data)
#         data = arrayMergeById_json(data)
#     if active_tab == 'tab-7':
#         data = flatten_json(data)
#         data = arrayMergeByIndex_json(data)
#     if active_tab == 'tab-8':
#         data = flatten_json(data)
#         data = objectMerge_json(data)
#
#     # for i in range(len(data)):
#     #     # print(type(data[i]))
#     #     data[i] = unflatten(data[i])
#
#     return data
#
#
#
#
# # @app.callback(Output('json','json'),[Input('button','n_clicks')],[State('input-box', 'value')])
# # def update_output(n_clicks, value):
# #     json = {'testing': value, 'nclicks': n_clicks}
# #     print('finished loading data')
# #     return json