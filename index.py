import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from app import server

from apps import merge_strategy, temporal_evolution, missing_data, page2, page3, page4, page6, page6,page7, page8, page9, page10, page11


def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div([
            dcc.Link('Merge Strategy | ', href='/apps/merge_strategy'),
            dcc.Link('Temporal Evolution | ', href='/apps/temporal_evolution'),
            dcc.Link('Missing Data | ', href='/apps/missing_data'),
            dcc.Link('Page 2 | ', href='/apps/page2'),
            dcc.Link('Page 3 | ', href='/apps/page3'),
            dcc.Link('Page 4 | ', href='/apps/page4'),
            dcc.Link('Page 6 | ', href='/apps/page6'),
            dcc.Link('Page 7 | ', href='/apps/page7'),
            dcc.Link('Page 8 | ', href='/apps/page8'),
            dcc.Link('Page 9 | ', href='/apps/page9'),
            dcc.Link('Page 10 | ', href='/apps/page10'),
            dcc.Link('Page 11 | ', href='/apps/page11'),
        ], className="row"),
        html.Div(id='page-content', children=[])
    ])


app.layout = serve_layout


@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/merge_strategy': return merge_strategy.layout
    if pathname == '/apps/temporal_evolution': return temporal_evolution.layout
    if pathname == '/apps/missing_data': return missing_data.layout
    if pathname == '/apps/page2': return page2.layout
    if pathname == '/apps/page3': return page3.layout
    if pathname == '/apps/page4': return page4.layout
    if pathname == '/apps/page6': return page6.layout
    if pathname == '/apps/page7': return page7.layout
    if pathname == '/apps/page8': return page8.layout
    if pathname == '/apps/page9': return page9.layout
    if pathname == '/apps/page10': return page10.layout
    if pathname == '/apps/page11': return page11.layout

    # if pathname == '/apps/git_graph': return git_graph.layout
    else: return merge_strategy.layout


if __name__ == '__main__':
    app.run_server(debug=True)
