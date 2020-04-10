import dash_core_components as dcc
import dash_html_components as html

from .data_selection import DATA_SELECTION
from .data_plots import DATA_PLOTS
from .download_area import DOWNLOAD_AREA
from .footer import FOOTER

LAYOUT = html.Div(
    [
        html.H1("COVID19 analysis dashboard"),
        DATA_SELECTION,
        DATA_PLOTS,
        DOWNLOAD_AREA,
        FOOTER,
    ],
    className="container",
)
