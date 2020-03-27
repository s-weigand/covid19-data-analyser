import io
import os

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import flask
import pandas as pd

from data_scraper import get_data, ALLOWED_SOURCES
from data_analyzer import get_daily_growth, get_growth_rate
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
        html.Div(
            [
                html.Label(
                    [
                        "Data Subsets",
                        dcc.Dropdown(
                            id="subsets",
                            options=[],
                            value=None,
                            multi=True,
                            disabled=True,
                        ),
                    ]
                ),
                dcc.Checklist(
                    id="log_plot",
                    options=[{"label": "Log Plot", "value": "log_plot"},],
                    value=[],
                    labelStyle={"display": "inline-block"},
                ),
            ],
            className="plot_settings",
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
                    html.Button("Download Data", id="download-button"),
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
                        " covid19-data-analyzer",
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
    [Output("download-link", "href"), Output("download-link", "target"),],
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
        return generate_dropdown_options(parent_regions), False, False, False
    else:
        return [], True, True, True


@app.callback(
    [Output("regions", "options"), Output("regions", "disabled")],
    [Input("source_select", "value"), Input("parent_regions", "value")],
)
def update_regions(data_source, values):
    if data_source and values:
        covid19_data = get_data(data_source)
        selector = generate_selector(covid19_data.parent_region, values)
        regions = covid19_data[selector].region.sort_values().unique()
        return generate_dropdown_options(regions), False
    else:
        return [], True


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
        return [], []


@app.callback(
    Output("data_plot", "figure"),
    [
        Input("source_select", "value"),
        Input("regions", "value"),
        Input("subsets", "value"),
        Input("log_plot", "value"),
    ],
)
def update_data_plot(data_source, regions, subsets, log_plot):
    if data_source and regions:
        covid19_data = get_data(data_source)
        if "log_plot" in log_plot:
            log_plot = True
        else:
            log_plot = False
        return generate_figure(
            covid19_data,
            regions,
            title="data",
            subsets=subsets,
            y_title="count (people)",
            log_plot=log_plot,
        )
    else:
        return {"data": [], "layout": {"title": "data"}}


@app.callback(
    Output("growth_plot", "figure"),
    [
        Input("source_select", "value"),
        Input("regions", "value"),
        Input("subsets", "value"),
        Input("log_plot", "value"),
    ],
)
def update_growth_plot(data_source, regions, subsets, log_plot):
    if data_source and regions:
        covid19_data = get_data(data_source)
        if "log_plot" in log_plot:
            log_plot = True
        else:
            log_plot = False
        covid19_data = get_daily_growth(covid19_data)
        return generate_figure(
            covid19_data,
            regions,
            title="daily growth",
            subsets=subsets,
            y_title="growth (people/day)",
            log_plot=log_plot,
        )
    else:
        return {"data": [], "layout": {"title": "daily growth"}}


@app.callback(
    Output("growth_rate_plot", "figure"),
    [
        Input("source_select", "value"),
        Input("regions", "value"),
        Input("subsets", "value"),
        Input("log_plot", "value"),
    ],
)
def update_growth_rate_plot(data_source, regions, subsets, log_plot):
    if data_source and regions:
        covid19_data = get_data(data_source)
        if "log_plot" in log_plot:
            log_plot = True
        else:
            log_plot = False
        covid19_data = get_growth_rate(covid19_data)
        return generate_figure(
            covid19_data,
            regions,
            title="growth rate",
            subsets=subsets,
            y_title="growth rate",
            log_plot=log_plot,
        )
    else:
        return {"data": [], "layout": {"title": "growth rate"}}


if "PRODUCTION_DOCKER" in os.environ:
    app.config.suppress_callback_exceptions = True
    app.debug = False
else:
    app.debug = True
    app.port = 8050


if __name__ == "__main__":
    app.run_server()
