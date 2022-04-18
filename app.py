import dash
import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, MultiplexerTransform
import sentry_sdk
import socket
import sys
import os


# Sentry
try:
    url = ''
    # Heroku dev environment
    if os.environ['environ'] == 'dev':
        url = 'https://f38a51d68768466fb9b994ba3d8c0998@o1139317.ingest.sentry.io/6197574'
    # Heroku production environment
    elif os.environ['environ'] == 'prod':
        url = 'https://b5a59239106f4af79e96d0ace1992117@o1139317.ingest.sentry.io/6197575'

    if url != '':
        sentry_sdk.init(
            url,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0
        )
    print('Initialized Sentry on environ: ', os.environ['environ'])
    sys.stdout.flush()
except:
    pass


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

server = app.server



