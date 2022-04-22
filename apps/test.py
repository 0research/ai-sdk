import pandas as pd
import dash_bootstrap_components as dbc
import json
from app import app
import dash_cytoscape as cyto
from dash import Dash, no_update, html, Input, Output, dash_table
from dash.exceptions import PreventUpdate
from dash_extensions import EventListener
from collections import OrderedDict
from apps.util import *

df = pd.DataFrame(OrderedDict([
    ('climate', ['Sunny', 'Snowy', 'Sunny', 'Rainy']),
    ('temperature', [13, 43, 50, 30]),
    ('city', ['NYC', 'Montreal', 'Miami', 'NYC'])
]))

layout = html.Div([
    # dash_table.DataTable(
    #     id='table-dropdown',
    #     data=df.to_dict('records'),
    #     columns=[
    #         {'id': 'climate', 'name': 'climate', 'presentation': 'dropdown'},
    #         {'id': 'temperature', 'name': 'temperature'},
    #         {'id': 'city', 'name': 'city', 'presentation': 'dropdown'},
    #     ],
    #     editable=True,
    #                                     #list of dictionaries. One dict per row
    #     dropdown_data=[{                #their keys represent column IDs
    #         'climate': {                #their values are 'options' and 'clearable'
    #             'options': [            #'options' represent cell data
    #                 {'label': i, 'value': i}
    #                 for i in df['climate'].unique()
    #             ],

    #             'clearable':True
    #         },

    #         'city': {
    #             'options': [
    #                 {'label': i, 'value': i}
    #                 for i in df['city'].unique()
    #             ],

    #             'clearable':True
    #         },
    #     } for x in range(2)
    #     ],

    # ),

    # html.Div(generate_datatable('abc', height='400px')),
    cyto.Cytoscape(
        id='cytoscape',
        layout={'name': 'preset'},
        style={'width': '100%', 'height': '400px'},
        elements=[
            {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
            {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}, 'classes':'selected'},
            {'data': {'source': 'one', 'target': 'two'}}
        ],
        stylesheet= [{
            'selector': '.selected',
            'style': {
                'background-color': '#000000',
            }
        }],
    ),

    dbc.Button('Click', id='change'),
    html.Div('aaa', id='div'),

])

@app.callback(
    Output('cytoscape', 'selectedNodeData'),
    Input('change', 'n_clicks'),
    State('cytoscape', 'tapNode'),
)
def click(n_clicks, selectedNodeData):
    # print('ONE:', n_clicks, selectedNodeData)
    print("ONE")
    pprint(selectedNodeData)

    return [{'id': 'two', 'label': 'Node 2'}]

@app.callback(
    Output('cytoscape', 'children'),
    Input('cytoscape', 'selectedNodeData'),
)
def click2(selectedNodeData):
    print('TWO: ', selectedNodeData)

    return no_update

# @app.callback(
#     Output('abc', 'data'),
#     Output('abc', 'columns'),
#     Output('abc', 'dropdown_data'),
#     Input('url', 'pathname'),
# )
# def generate_datatable_aggregate(_):
#     node_id = "022897a3-a3fb-11ec-829c-dc719685b14a"
#     df = get_dataset_data(node_id)
#     columns = [{"name": i, "id": i, 'presentation': 'dropdown'} for i in df.columns]

#     dropdown_data = [
#         {               
#             c['name']: {
#                 'options': [
#                     {'label': 'one', 'value': 1},
#                     {'label': 'two', 'value': 2},
#                 ],
#             },
#         } for c in columns
#     ]
#     print(df)

#     return df.to_dict('records'), columns, dropdown_data


