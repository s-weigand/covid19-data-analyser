import dash
import flask

from covid19_data_analyzer.dashboard.utils.data_loader import (  # noqa: F401
    DASHBOARD_DATA,
    DASHBOARD_FIT_PARAM_DATA,
    DASHBOARD_FIT_PLOT_DATA,
)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

server = flask.Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=external_stylesheets,
    assets_folder="dashboard_assets",
)

app.title = "COVID19 dashboard"


app.config.suppress_callback_exceptions = True
