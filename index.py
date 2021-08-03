import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from app import server

from apps import page1, page2


def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div([
            dcc.Link('Page 1 | ', href='/apps/page1'),
            dcc.Link('Page 2 ', href='/apps/page2'),
        ], className="row"),
        html.Div(id='page-content', children=[])
    ])


app.layout = serve_layout


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/page1':
        return page1.layout
    if pathname == '/apps/page2':
        return page2.layout
    else:
        return page1.layout


if __name__ == '__main__':
    app.run_server(debug=True)
