import dash
import dash_bootstrap_components as dbc

FA = {
    "href": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css",
    "rel": "stylesheet",
    "integrity": "sha512-iBBXm8fW90+nuLcSKlbmrPcLa0OT92xO1BIsZ+ywDWZCvqsWgccV3gFoRBv0z+8dLJgyAHIhR35VZc2oM/gI1w==",
    "crossorigin": "anonymous",
    "referrerpolicy": "no-referrer",
}
external_stylesheets = [dbc.themes.BOOTSTRAP, FA]

app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=external_stylesheets,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
                )

server = app.server