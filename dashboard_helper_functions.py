from typing import Dict, List

import io

import pandas as pd
from plotly.colors import DEFAULT_PLOTLY_COLORS

from data_scraper import get_data
from data_analyzer import get_fit_data


def generate_dropdown_options(value_list_like):
    """
    Generates Dropdown options from a list

    Parameters
    ----------
    value_list_like : Listlike
        Iterable with the option values

    Returns
    -------
    Dict
        Options for the Dropdown
    """
    options = []
    for value in value_list_like:
        options.append({"label": value, "value": value})
    return options


def get_available_subsets(covid19_data: pd.DataFrame) -> list:
    """
    Returns a list of subsets which are available on the dataset

    Parameters
    ----------
    covid19_data : pd.DataFrame
        [description]

    Returns
    -------
    list
        List of available subsets
    """
    column_selector = covid19_data.columns.isin(
        ["confirmed", "recovered", "deaths", "still_infectious"]
    )
    return covid19_data.columns[column_selector].to_list()


def generate_selector(df_column: pd.Series, values):
    """
    Generates a selector based on values are in df_columns

    Parameters
    ----------
    df_column : pd.Series
        DataFrame colum which values should be compared to the values of values
    values : Listlike
        Iterable of column values

    Returns
    -------
    pd.Series
        Boolean pd.Series which can be used as selector for the dataframe
    """
    selector_data = []
    for value in values:
        selector_data.append(df_column == value)
    return pd.DataFrame(selector_data).apply(any)


def plotly_color_cycler(plot_index: int):
    mod_index = plot_index % len(DEFAULT_PLOTLY_COLORS)
    return DEFAULT_PLOTLY_COLORS[mod_index]


def generate_figure(
    data_source,
    regions,
    title,
    y_title,
    data_transform_fuction=None,
    subsets=["confirmed"],
    plot_settings=[],
    fit_model=None,
):

    if data_source and regions:
        plot_data = []
        plot_index = 0
        data = get_data(data_source)
        if data_transform_fuction is not None:
            data = data_transform_fuction(data)
        if fit_model is not None:
            fit_plot_data = get_fit_data(
                data_source=data_source, model_name=fit_model, kind="plot"
            )
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
    raw_data, region, subset, color, hide_raw_data=False, fit_data=None
) -> List[Dict]:
    plot_sub_data = []
    if not hide_raw_data:
        raw_region_data = raw_data[raw_data.region == region]
        raw_data_trace = create_trace(raw_region_data, region, subset, color)
        plot_sub_data.append(raw_data_trace,)
    if fit_data is not None:
        fit_region_data = fit_data[fit_data.region == region]
        if len(fit_region_data):
            fit_data_trace = create_trace(
                fit_region_data, region, subset, color, is_fit=True
            )
            plot_sub_data.append(fit_data_trace,)

    return plot_sub_data


def create_trace(data, region, subset, color, is_fit=False) -> Dict:
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


def generate_download_buffer(data_source: str, file_format: str):
    """
    Transdorms a dataframe to a given fileformat as buffer,
    which can be used for flask.send_file

    Parameters
    ----------
    data_source : str
        Name of the data source
    file_format : "csv" | "xls
        Format the file should be downloaded in

    Returns
    -------
    dict
        dict containing the buffer, mimetype and filename
    """
    buffer = io.BytesIO()
    covid19_data = get_data(data_source)
    file_name = f"covid19_data_{data_source}"
    if file_format == "xls":
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as excel_writer:  # noqa: E0110
            covid19_data.to_excel(excel_writer, sheet_name="sheet1", index=False)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        file_name += ".xls"

    elif file_format == "csv":
        with io.StringIO() as str_buffer:
            covid19_data.to_csv(str_buffer, index=False)
            buffer.write(str_buffer.getvalue().encode("utf-8"))
            str_buffer.close()
        mimetype = "text/csv"
        file_name += ".csv"

    buffer.seek(0)
    return {"buffer": buffer, "file_name": file_name, "mimetype": mimetype}
