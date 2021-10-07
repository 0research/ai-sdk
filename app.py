import dash
import dash_bootstrap_components as dbc

external_stylesheets = [dbc.themes.BOOTSTRAP]


app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=external_stylesheets,
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
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