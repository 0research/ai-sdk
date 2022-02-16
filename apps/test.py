import pandas as pd
import dash_bootstrap_components as dbc
import json
from app import app
import dash_cytoscape as cyto
from dash import Dash, no_update, html, Input, Output, dash_table as dt
from dash.exceptions import PreventUpdate
from dash_extensions import EventListener

df = pd.read_csv("https://git.io/Juf1t")
df["id"] = df.index


table = dt.DataTable(
    id="tbl",
    data=df.to_dict("records"),
    columns=[{"name": i, "id": i} for i in df.columns],
)

cytoscape = cyto.Cytoscape(id='cytoscape',
                            minZoom=0.2,
                            maxZoom=2,
                            selectedNodeData=[],
                            layout={
                                'name': 'preset',
                                'fit': True,
                                'directed': True,
                                'padding': 10,
                                'zoom': 1,
                            },
                            elements=[
                                {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
                                {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},
                                {'data': {'source': 'one', 'target': 'two'}}
                            ],
                            style={'height': '800px','width': '100%'},
                        )


input1 = dbc.Input(id='input1', value='empty')

layout = dbc.Container(
    [   
        # # Event Listener 1
        # EventListener(
        #         id="el",
        #         events=[{"event": "input", "props": ["srcElement.className", "srcElement.value", "srcElement.innerText"]}],
        #         logging=True,
        #         children=input1,
        # ),
        # # dbc.Alert("Click the table", id="out"),
        # html.Div(id="event"),
        

        # # Event Listener 2
        # EventListener(
        #         id="el2",
        #         events=[{"event": "click", "props": ["srcElement.className", "srcElement.value", "srcElement.innerText"]}],
        #         logging=True,
        #         children=cytoscape,
        # ),

        dbc.Button('Click', id='button1')
        # html.Div(id='output')
    ]
)

@app.callback(
    Output('output', 'children'),
    Input('button1', 'n_clicks')
)
def button_trigger(n_clicks):
    if n_clicks is None: return no_update



# # Event Listener 1 (Datatable)
# @app.callback(Output("event", "children"), Input("el", "event"), Input("el", "n_events"))
# def click_event(event, n_events):
#     print(event)
#     # Check if the click is on the active cell.
#     if not event or "cell--selected" not in event["srcElement.className"]:
#         raise PreventUpdate
#     # Return the content of the cell.
#     return f"Cell content is {event['srcElement.innerText']}, number of clicks in {n_events}"

# @app.callback(Output("out", "children"), Input("tbl", "active_cell"))
# def update_graphs(active_cell):
#     return json.dumps(active_cell)


# # Event Listener 2 (Cytoscape)
# @app.callback(Output("event", "children"), Input("el2", "event"), Input("el2", "n_events"))
# def click_event(event, n_events):
#     # Check if the click is on the active cell.
#     if not event or "cell--selected" not in event["srcElement.className"]:
#         raise PreventUpdate
#     # Return the content of the cell.
#     return f"Cell content is {event['srcElement.innerText']}, number of clicks in {n_events}"

# @app.callback(Output("out", "children"), Input("tbl", "active_cell"))
# def update_graphs(active_cell):
#     return json.dumps(active_cell)




