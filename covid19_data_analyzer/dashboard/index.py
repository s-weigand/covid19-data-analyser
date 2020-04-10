import os

from covid19_data_analyzer.dashboard.app import app
from covid19_data_analyzer.dashboard.components import LAYOUT

app.layout = LAYOUT

if "PRODUCTION_DOCKER" in os.environ:
    app.config.suppress_callback_exceptions = True

if __name__ == "__main__":
    if "PRODUCTION_DOCKER" in os.environ:
        DEBUG = False
    else:
        DEBUG = True
    app.run_server(host="0.0.0.0", port=8050, debug=DEBUG)
