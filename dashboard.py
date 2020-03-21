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
                        "Data representation",
                        dcc.Dropdown(
                            id="data_reperesentation",
                            options=generate_dropdown_options(
                                ["infected", "growth", "growth_rate"]
                            ),
                            clearable=False,
                            value="infected",
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
        dcc.Graph(id="my-graph"),
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
        Output("data_reperesentation", "disabled"),
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
    Output("my-graph", "figure"),
    [
        Input("source_select", "value"),
        Input("regions", "value"),
        Input("data_reperesentation", "value"),
        Input("log_plot", "value"),
    ],
)
def update_plot(data_source, regions, data_reperesentation, log_plot):
    if data_source and regions:
        covid19_data = get_data(data_source)
        if "log_plot" in log_plot:
            log_plot = True
        else:
            log_plot = False
        if data_reperesentation == "growth":
            covid19_data = get_daily_growth(covid19_data)
        elif data_reperesentation == "growth_rate":
            covid19_data = get_growth_rate(covid19_data)
        return generate_figure(
            covid19_data, regions, y_title=data_reperesentation, log_plot=log_plot
        )
    else:
        return {"data": [], "layout": {}}


if __name__ == "__main__":
    if "PRODUCTION_DOCKER" in os.environ:
        app.config.suppress_callback_exceptions = True
        DEBUG = False
    else:
        DEBUG = True
    app.run_server(host="0.0.0.0", port=8050, debug=DEBUG)
