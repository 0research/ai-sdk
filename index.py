import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from app import server

from apps import merge_strategy, temporal_evolution, temporal_merge, time_series_decomposition, impute_time_series_missing_data, page2, page3, page4, page6, page6,page7, page8, page9, page10


def serve_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div([
            dcc.Link(' Merge Strategy | ', href='/apps/merge_strategy'),
            # dcc.Link('Temporal Merge | ', href='/apps/temporal_merge'),
            dcc.Link(' Temporal Evolution | ', href='/apps/temporal_evolution'),
            dcc.Link(' Impute Time Series Missing Data | ', href='/apps/impute_time_series_missing_data'),
            dcc.Link(' Time Series Decomposition | ', href='/apps/time_series_decomposition'),
            dcc.Link(' Page 3 | ', href='/apps/page3'),
            dcc.Link(' Page 4 | ', href='/apps/page4'),
            # dcc.Link('Page 6 | ', href='/apps/page6'),
            # dcc.Link('Merge Strategy | ', href='/apps/page7'),
            # dcc.Link('Temporal Merge | ', href='/apps/page8'),
            # dcc.Link('Temporal Evolution | ', href='/apps/page9'),
            # dcc.Link('Page 10 | ', href='/apps/page10'),
        ], className="row"),
        html.Div(id='page-content', children=[])
    ])


app.layout = serve_layout


@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/merge_strategy': return merge_strategy.layout
    if pathname == '/apps/temporal_evolution': return temporal_evolution.layout
    if pathname == '/apps/time_series_decomposition': return time_series_decomposition.layout
    if pathname == '/apps/impute_time_series_missing_data': return impute_time_series_missing_data.layout
    if pathname == '/apps/page3': return page3.layout
    if pathname == '/apps/page4': return page4.layout

    if pathname == '/apps/temporal_merge': return temporal_merge.layout
    if pathname == '/apps/page2': return page2.layout
    if pathname == '/apps/page6': return page6.layout
    if pathname == '/apps/page7': return page7.layout
    if pathname == '/apps/page8': return page8.layout
    if pathname == '/apps/page9': return page9.layout
    if pathname == '/apps/page10': return page10.layout
    

    # if pathname == '/apps/git_graph': return git_graph.layout
    else: return merge_strategy.layout


if __name__ == '__main__':
    app.run_server(debug=True)
