from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html


from covid19_data_analyzer.dashboard.app import app
from covid19_data_analyzer.dashboard.utils.controls import (
    generate_dropdown_options,
    generate_selector,
    get_available_subsets,
)

from covid19_data_analyzer.dashboard.utils.data_loader import DASHBOARD_DATA
from covid19_data_analyzer.data_functions.scrapers import ALLOWED_SOURCES

from covid19_data_analyzer.data_functions.analysis import IMPLEMENTED_FIT_MODELS


SOURCE_SELECTION = html.Label(
    [
        "Data source",
        dcc.Dropdown(
            id="source_select",
            placeholder="Select a data source",
            options=generate_dropdown_options(ALLOWED_SOURCES),
            multi=False,
            clearable=False,
        ),
    ]
)
PARENT_REGION_SELECTION = html.Label(
    [
        "Parent region",
        dcc.Dropdown(
            id="parent_regions",
            placeholder="Select a parent region of the data",
            options=[],
            value=None,
            multi=True,
            clearable=False,
            disabled=True,
        ),
    ]
)
REGION_SELECTION = html.Label(
    [
        "Regions",
        dcc.Dropdown(
            id="regions",
            placeholder="Select a region of the data",
            options=[],
            value=None,
            multi=True,
            disabled=True,
        ),
    ]
)
SUBSET_SELECTION = html.Label(
    [
        "Data Subsets",
        dcc.Dropdown(
            id="subsets",
            placeholder="Select data subset",
            options=[],
            value=None,
            multi=True,
            disabled=True,
        ),
    ]
)
FITMODEL_SELECTION = html.Label(
    [
        "Fitmodel",
        dcc.Dropdown(
            id="fit_model",
            placeholder="Select fit model",
            options=generate_dropdown_options(IMPLEMENTED_FIT_MODELS),
            value=None,
            multi=False,
            disabled=True,
            clearable=True,
        ),
    ]
)

DATA_SELECTION = html.Div(
    [
        SOURCE_SELECTION,
        PARENT_REGION_SELECTION,
        REGION_SELECTION,
        SUBSET_SELECTION,
        FITMODEL_SELECTION,
    ],
    className="data_selection",
)


@app.callback(
    [
        Output("parent_regions", "options"),
        Output("parent_regions", "disabled"),
        Output("dl_format", "disabled"),
        Output("subsets", "disabled"),
    ],
    [Input("source_select", "value")],
)
def update_parent_regions(data_source):
    if data_source:
        covid19_data = DASHBOARD_DATA[data_source]
        parent_regions = covid19_data.parent_region.sort_values().unique()
        return (generate_dropdown_options(parent_regions), *[False] * 3)
    else:
        return ([], *[True] * 3)


@app.callback(
    [
        Output("regions", "options"),
        Output("regions", "disabled"),
        Output("fit_model", "disabled"),
    ],
    [Input("source_select", "value"), Input("parent_regions", "value")],
)
def update_regions(data_source, values):
    if data_source and values:
        covid19_data = DASHBOARD_DATA[data_source]
        selector = generate_selector(covid19_data.parent_region, values)
        regions = covid19_data[selector].region.sort_values().unique()
        return (generate_dropdown_options(regions), *[False] * 2)
    else:
        return ([], *[True] * 2)


@app.callback(
    [Output("subsets", "options"), Output("subsets", "value")],
    [Input("source_select", "value")],
)
def update_subsets(data_source):
    if data_source:
        covid19_data = DASHBOARD_DATA[data_source]
        subsets = get_available_subsets(covid19_data)
        return generate_dropdown_options(subsets), subsets
    else:
        return ([],) * 2
