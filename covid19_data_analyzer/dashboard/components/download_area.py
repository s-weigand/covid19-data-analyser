from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import flask

from covid19_data_analyzer.dashboard.app import app
from covid19_data_analyzer.dashboard.utils.controls import generate_dropdown_options
from covid19_data_analyzer.dashboard.utils.download import generate_download_buffer

DOWNLOAD_AREA = html.Div(
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
