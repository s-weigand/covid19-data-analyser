import os

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import flask

from data_scraper import ALLOWED_SOURCES, get_data
from data_analyzer import IMPLEMENTED_FIT_MODELS, get_daily_growth, get_growth_rate
from dashboard_helper_functions import (
    generate_dropdown_options,
    generate_figure,
    generate_selector,
    generate_download_buffer,
    get_available_subsets,
)


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

server = flask.Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=external_stylesheets,
    assets_folder="dashboard_assets",
)

app.layout = html.Div(
    [
        html.H1("COVID19 analysis dashboard"),
        html.Div(
            [
                html.Label(
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
                ),
                html.Label(
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
                ),
                html.Label(
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
                ),
                html.Label(
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
                ),
                html.Label(
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
                ),
            ],
            className="data_selection",
        ),
        html.Div(
            [
                dcc.Checklist(
                    id="plot_settings",
                    options=[
                        {"label": "Log Plot", "value": "log_plot"},
                        {"label": "Hide Raw Data", "value": "hide_raw_data"},
                    ],
                    value=[],
                    labelStyle={"display": "inline-block"},
                ),
            ],
            className="plot_settings_div",
        ),
        dcc.Graph(id="data_plot"),
        dcc.Graph(id="growth_plot"),
        dcc.Graph(id="growth_rate_plot"),
        html.Div(
            [
                html.Label(
                    [
                        "Download format",
                        dcc.Dropdown(
                            id="dl_format",
                            placeholder="Select a download file format",
                            options=generate_dropdown_options(["csv", "xls"]),
                            value=None,
                            clearable=False,
                            disabled=True,
                        ),
                    ]
                ),
                html.A(
                    html.Button("Download Raw Data", id="download-button"),
                    id="download-link",
                    target="_blank",
                ),
            ],
            className="download_area",
        ),
        html.Footer(
            html.Span(
                [
                    "Sourcecode available on ",
                    html.A(
                        " s-weigand/covid19-data-analyzer",
                        href="https://github.com/s-weigand/covid19-data-analyzer",
                    ),
                ]
            ),
            className="source-link",
        ),
    ],
    className="container",
)


@app.callback(
    [Output("download-link", "href"), Output("download-link", "target")],
    [Input("source_select", "value"), Input("dl_format", "value")],
)
def update_download_link(data_source, dl_format):
    if data_source and dl_format:
        return (
            f"/download_data?data_source={data_source}&dl_format={dl_format}",
            "_blank",
        )
    else:
        return "#", "_self"


@app.server.route("/download_data")
def download_data():
    data_source = flask.request.args.get("data_source")
    dl_format = flask.request.args.get("dl_format")
    download_dict = generate_download_buffer(data_source, dl_format)
    return flask.send_file(
        download_dict["buffer"],
        mimetype=download_dict["mimetype"],
        attachment_filename=download_dict["file_name"],
        as_attachment=True,
        cache_timeout=0,
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
        covid19_data = get_data(data_source)
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
        covid19_data = get_data(data_source)
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
        covid19_data = get_data(data_source)
        subsets = get_available_subsets(covid19_data)
        return generate_dropdown_options(subsets), subsets
    else:
        return ([],) * 2


PLOT_INPUTS = [
    Input("source_select", "value"),
    Input("regions", "value"),
    Input("subsets", "value"),
    Input("plot_settings", "value"),
    Input("fit_model", "value"),
]


@app.callback(
    Output("data_plot", "figure"), PLOT_INPUTS,
)
def update_data_plot(data_source, regions, subsets, plot_settings, fit_model):
    return generate_figure(
        data_source=data_source,
        regions=regions,
        title="data",
        subsets=subsets,
        y_title="count (people)",
        plot_settings=plot_settings,
        fit_model=fit_model,
    )


@app.callback(
    Output("growth_plot", "figure"), PLOT_INPUTS,
)
def update_growth_plot(data_source, regions, subsets, plot_settings, fit_model):
    return generate_figure(
        data_source=data_source,
        regions=regions,
        data_transform_fuction=get_daily_growth,
        title="daily growth",
        subsets=subsets,
        y_title="growth (people/day)",
        plot_settings=plot_settings,
        fit_model=fit_model,
    )


@app.callback(
    Output("growth_rate_plot", "figure"), PLOT_INPUTS,
)
def update_growth_rate_plot(data_source, regions, subsets, plot_settings, fit_model):
    return generate_figure(
        data_source=data_source,
        regions=regions,
        data_transform_fuction=get_growth_rate,
        title="growth rate",
        subsets=subsets,
        y_title="growth rate",
        plot_settings=plot_settings,
        fit_model=fit_model,
    )


if "PRODUCTION_DOCKER" in os.environ:
    app.config.suppress_callback_exceptions = True
    app.debug = False
else:
    app.debug = True
    app.port = 8050


if __name__ == "__main__":
    app.run_server()
