import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from app import server

from apps import merge_strategy, page2, page3


def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div([
            dcc.Link('Merge Strategy | ', href='/apps/merge_strategy'),
            dcc.Link('Page 2 | ', href='/apps/page2'),
        ], className="row"),
        html.Div(id='page-content', children=[])
    ])


app.layout = serve_layout


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/merge_strategy':
        return merge_strategy.layout
    if pathname == '/apps/page2':
        return page2.layout
    else:
        return merge_strategy.layout


if __name__ == '__main__':
    app.run_server(debug=True)
