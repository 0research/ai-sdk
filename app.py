import dash
import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, MultiplexerTransform

FA = {
    "href": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css",
    "rel": "stylesheet",
    "integrity": "sha512-iBBXm8fW90+nuLcSKlbmrPcLa0OT92xO1BIsZ+ywDWZCvqsWgccV3gFoRBv0z+8dLJgyAHIhR35VZc2oM/gI1w==",
    "crossorigin": "anonymous",
    "referrerpolicy": "no-referrer",
}
external_stylesheets = [dbc.themes.BOOTSTRAP, FA]



app = DashProxy(__name__,
                suppress_callback_exceptions=True,
                transforms=[MultiplexerTransform()],
                external_stylesheets=external_stylesheets,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}],
                title='AI-SDK'
                )

app.layout = dbc.Container(
    dbc.Alert("Wrangle Data!", color="success"),
    className="p-5",
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