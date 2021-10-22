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


app = DashProxy(__name__, suppress_callback_exceptions=True,
                transforms=[MultiplexerTransform()],
                external_stylesheets=external_stylesheets,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}],
                title='AI-SDK'
                )
#https://dash-bootstrap-components.opensource.faculty.ai/docs/quickstart/
# To use dash-bootstrap-components you must do two things:
#    1.Link a Bootstrap v4 compatible stylesheet (example code shown below)
#    2.Incorporate dash-bootstrap-components into the layout of your app.(already done in app.py)



app.layout = dbc.Container(
    dbc.Alert("Wrangle Data!", color="success"),
    className="p-5",
)

server = app.server