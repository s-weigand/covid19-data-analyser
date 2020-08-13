from typing import Callable, Dict, List, Iterable

import pandas as pd
from plotly.colors import DEFAULT_PLOTLY_COLORS

from covid19_data_analyzer.dashboard.utils.data_loader import (
    DASHBOARD_DATA,
    DASHBOARD_FIT_PLOT_DATA,
)


def plotly_color_cycler(plot_index: int) -> str:
    """
    Colorcycler on base of the plotly default colors,
    to ensure that raw data and fits have the same color

    Parameters
    ----------
    plot_index : int
        index of the current plot

    Returns
    -------
    str
        Color to be used for a plot
    """
    mod_index = plot_index % len(DEFAULT_PLOTLY_COLORS)
    return DEFAULT_PLOTLY_COLORS[mod_index]


def generate_figure(
    data_source: str,
    parent_regions: Iterable[str],
    regions: Iterable[str],
    title: str,
    y_title: str,
    data_transform_fuction: Callable = None,
    subsets: Iterable[str] = ["confirmed"],
    plot_settings: Iterable[str] = [],
    fit_model: str = None,
) -> Dict:
    """
    Creates the Figure data for a plot

    Parameters
    ----------
    data_source : str
        name of the data source
    parent_regions : Iterable[str]
        names of the parent_regions which should be plotted
    regions : Iterable[str]
        names of the regions which should be plotted
    title : str
        Title of the plot
    y_title : str
        caption of the y-axis
    data_transform_fuction : Callable, optional
        function which should be applied on the data, by default None
    subsets : Iterable[str], optional
        subsets of the data which should be ploted, by default ["confirmed"]
    plot_settings : Iterable[str], optional
        settings which should be used for the plot, by default []
    fit_model : str, optional
        name of the fit model which should be used, by default None

    Returns
    -------
    Dict
        figure data of the plot
    """
    if data_source and regions:
        plot_data = []
        plot_index = 0
        data = DASHBOARD_DATA[data_source]
        data = data[data.parent_region.isin(parent_regions)]
        if data_transform_fuction is not None:
            data = data_transform_fuction(data)
        if fit_model is not None:
            fit_plot_data = DASHBOARD_FIT_PLOT_DATA[data_source][fit_model]
            if data_transform_fuction is not None:
                fit_plot_data = data_transform_fuction(fit_plot_data)
        else:
            fit_plot_data = None
        for subset in subsets:
            for region in regions:
                color = plotly_color_cycler(plot_index)
                plot_sub_data = generate_plot_sub_data(
                    raw_data=data,
                    region=region,
                    subset=subset,
                    hide_raw_data="hide_raw_data" in plot_settings,
                    color=color,
                    fit_data=fit_plot_data,
                )
                for plot_sub_data_entry in plot_sub_data:
                    plot_data.append(plot_sub_data_entry)
                plot_index += 1
        return {
            "data": plot_data,
            "layout": {
                "title": title,
                "clickmode": "event+select",
                "yaxis": {
                    "type": "log" if "log_plot" in plot_settings else "linear",
                    "title": y_title,
                },
                "xaxis": {"title": "Date"},
            },
        }
    else:
        return {"data": [], "layout": {"title": title}}


def generate_plot_sub_data(
    raw_data: pd.DataFrame,
    region: str,
    subset: str,
    color: str,
    hide_raw_data: bool = False,
    fit_data: pd.DataFrame = None,
) -> List[Dict]:
    """
    Function to generate the data used to plot raw data and/or its fit

    Parameters
    ----------
    raw_data : pd.DataFrame
        Actual case data
    region : str
        region name of the data, needed to generate the legend
    subset : str
        subset name of the data, needed to generate the legend
    color : str
        color of the trace, needed so raw data and fits have the same color
    hide_raw_data : bool, optional
        Whether or not to hide the raw data, by default False
    fit_data : pd.DataFrame, optional
        Data used to plot a fit, by default None

    Returns
    -------
    List[Dict]
        List of traces which should be ploted
    """
    plot_sub_data = []
    if not hide_raw_data:
        raw_region_data = raw_data[raw_data.region == region]
        raw_data_trace = create_trace(raw_region_data, region, subset, color)
        plot_sub_data.append(raw_data_trace,)
    if fit_data is not None:
        fit_region_data = fit_data[fit_data.region == region]
        if len(fit_region_data) and not fit_region_data[subset].isna().any():
            fit_data_trace = create_trace(
                fit_region_data, region, subset, color, is_fit=True
            )
            plot_sub_data.append(fit_data_trace,)

    return plot_sub_data


def create_trace(
    data: pd.DataFrame, region: str, subset: str, color: str, is_fit: bool = False
) -> Dict:
    """
    Function to generate the Plot trace of a single dataset,
    with the appropriate style (raw data -> marker, fit -> line)


    Parameters
    ----------
    data : pd.DataFrame
        Data which should be plotted
    region : str
        region name of the data, needed to generate the legend
    subset : str
        subset name of the data, needed to generate the legend
    color : str
        color of the trace, needed so raw data and fits have the same color
    is_fit : bool, optional
        Whether or not the data are from a fit, by default False

    Returns
    -------
    Dict
        Trace data to generate a plot with dash
    """
    name = f"{region} {subset}"
    if is_fit:
        mode = "line"
        name = f"fit {name}"
    else:
        mode = "markers"
    return {
        "x": data.date,
        "y": data[subset],
        "name": name,
        "mode": mode,
        "marker": {"size": 8, "color": color},
        "line": {"color": color},
        "hoverlabel": {"namelength": -1},
    }
