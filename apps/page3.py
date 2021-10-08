# import dash_html_components as html
# from dash.dependencies import Input, Output, State
# from app import app
# from subprocess import call


# # Layout
# tab_labels = ['tab one', 'tab two', 'tab three']
# tab_values = ['tab-' + str(i) for i in range(1, len(tab_labels)+1)]
# layout = html.Div([
#     # html.Script(**{'xlink:href':'../abc.js'}),
#     html.Button('Detect', id='button'),
#     html.Div(id='output'),
# ], **{'data-label': ''})


# @app.callback(
#     Output('output', 'children'),
#     [Input('button', 'n_clicks')])
# def run_script_onClick(n_clicks):
#     # Don't run unless the button has been pressed...

#     script_path = 'python C:/0research/Project/ai-sdk/test/git_graph.js'
#     # The output of a script is always done through a file dump.
#     # Let's just say this call dumps some data into an `output_file`
#     call(["python3", script_path])

#     # Load your output file with "some code"
#     # output_content = some_loading_function('output file')

#     # Now return.
#     return html.Div('aaa')