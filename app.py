import dash
import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, MultiplexerTransform
import sentry_sdk
import socket
import sys
import os

# # Sentry
# try:
#     url = "https://abd709165a4e4d059c7ae7310455d630@o1139317.ingest.sentry.io/6345275" # Dev
#     # if os.environ['environ'] == 'dev':
#     #     url = "https://abd709165a4e4d059c7ae7310455d630@o1139317.ingest.sentry.io/6345275"
#     # elif os.environ['environ'] == 'prod':
#     #     url = 'https://b5a59239106f4af79e96d0ace1992117@o1139317.ingest.sentry.io/6197575'
#     sentry_sdk.init(url, traces_sample_rate=1.0)
#     print('Initialized Sentry on environ: ')
# except Exception as e:
#     print("Init Sentry Failed, Exception: ", e)

# sys.stdout.flush()


# External Scripts
external_scripts = [
    # {'src': 'https://cdn.jsdelivr.net/npm/typesense@latest/dist/typesense.min.js', 'type':'module', 'data-main': 'main'},
    # {'src': '/assets/require.js', 'data-main': 'main', 'type':'module'},
    # {'src': '/assets/typesense.js', 'data-main': 'main', 'type':'module'},
    # {'src': '/assets/typesense.min.js', 'data-main': 'main'},
    # {'src': 'http://requirejs.org/docs/release/2.1.5/comments/require.js', 'type':'module', 'data-main': 'main'}
]

# Stylesheet
FA = {
    "href": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css",
    "rel": "stylesheet",
    "integrity": "sha512-iBBXm8fW90+nuLcSKlbmrPcLa0OT92xO1BIsZ+ywDWZCvqsWgccV3gFoRBv0z+8dLJgyAHIhR35VZc2oM/gI1w==",
    "crossorigin": "anonymous",
    "referrerpolicy": "no-referrer",
}
external_stylesheets = [dbc.themes.BOOTSTRAP, FA, 'https://codepen.io/chriddyp/pen/bWLwgP.css']


# App
app = DashProxy(__name__,
    # prevent_initial_callbacks=True,
    suppress_callback_exceptions=True,
    external_scripts=external_scripts,
    transforms=[MultiplexerTransform()],
    external_stylesheets=external_stylesheets,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}],
    title='AI-SDK'
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        {%scripts%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            
            {%renderer%}
            
        </footer>
    </body>
</html>
'''


# Server
server = app.server



