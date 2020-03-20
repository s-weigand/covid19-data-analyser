import io

import pandas as pd

from data_scraper import get_data


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


def generate_selector(df_column, values):
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
    return pd.DataFrame(selector_data).apply(lambda row: any(row))


def generate_figure(covid19_data, regions, log_plot=False, fit_function=None):
    plot_data = []
    for region in regions:
        region_data = covid19_data[covid19_data.region == region]
        plot_data.append(
            {
                "x": region_data.date,
                "y": region_data.confirmed,
                "name": region,
                "mode": "markers",
                "marker": {"size": 12},
            },
        )
    return {
        "data": plot_data,
        "layout": {
            "clickmode": "event+select",
            "yaxis": {"type": "log" if log_plot else "linear"},
        },
    }


def generate_download_buffer(data_source, file_format):
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
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as excel_writer:
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
