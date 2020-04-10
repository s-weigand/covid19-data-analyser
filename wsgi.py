import logging
import sys
import os

logging.basicConfig(stream=sys.stderr)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from covid19_data_analyzer.dashboard.index import app  # noqa: E402

application = app.server
