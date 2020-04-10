from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html


from covid19_data_analyzer.dashboard.app import app
from covid19_data_analyzer.dashboard.utils.plot import generate_figure

from covid19_data_analyzer.data_functions.analysis import get_fit_data
from covid19_data_analyzer.data_functions.data_utils import (
    get_daily_growth,
    get_growth_rate,
)

DATA_PLOTS = html.Div(
    [
        html.Div(
            [
                dcc.Checklist(
                    id="plot_settings",
                    options=[
                        {"label": "Log Plot", "value": "log_plot"},
                        {"label": "Hide Raw Data", "value": "hide_raw_data"},
                        {"label": "Show fitted parameters", "value": "show_params"},
                    ],
                    value=[],
                    labelStyle={"display": "inline-block"},
                ),
            ],
            className="plot_settings_div",
        ),
        dcc.Markdown(id="fit_params"),
        dcc.Markdown("### Plots"),
        dcc.Graph(id="data_plot"),
        dcc.Graph(id="growth_plot"),
        dcc.Graph(id="growth_rate_plot"),
    ]
)


PLOT_INPUTS = [
    Input("source_select", "value"),
    Input("parent_regions", "value"),
    Input("regions", "value"),
    Input("subsets", "value"),
    Input("plot_settings", "value"),
    Input("fit_model", "value"),
]


@app.callback(
    Output("fit_params", "children"), PLOT_INPUTS,
)
def update_fit_param_table(
    data_source, parent_regions, regions, subsets, plot_settings, fit_model
):
    if "show_params" in plot_settings and fit_model is not None:
        fit_param_df = get_fit_data(
            data_source=data_source, model_name=fit_model, kind="params",
        )
        fit_param_df = fit_param_df[
            fit_param_df.parent_region.isin(parent_regions)
            & fit_param_df.region.isin(regions)
            & fit_param_df.subset.isin(subsets)
        ]
        fit_param_df_md = fit_param_df.set_index("parent_region").to_markdown()
        return f"### Fitted Parameters\n\n{fit_param_df_md}"
    elif "show_params" in plot_settings:
        return "#### In order to see the fitparameters you need to first select a 'Fitmodel'"
    else:
        return ""


@app.callback(
    Output("data_plot", "figure"), PLOT_INPUTS,
)
def update_data_plot(
    data_source, parent_regions, regions, subsets, plot_settings, fit_model
):
    return generate_figure(
        data_source=data_source,
        parent_regions=parent_regions,
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
def update_growth_plot(
    data_source, parent_regions, regions, subsets, plot_settings, fit_model
):
    return generate_figure(
        data_source=data_source,
        parent_regions=parent_regions,
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
def update_growth_rate_plot(
    data_source, parent_regions, regions, subsets, plot_settings, fit_model
):
    return generate_figure(
        data_source=data_source,
        parent_regions=parent_regions,
        regions=regions,
        data_transform_fuction=get_growth_rate,
        title="growth rate",
        subsets=subsets,
        y_title="growth rate",
        plot_settings=plot_settings,
        fit_model=fit_model,
    )
