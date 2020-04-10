from typing import Iterable

import pandas as pd


def generate_dropdown_options(values: Iterable[str]):
    """
    Generates Dropdown options from a list

    Parameters
    ----------
    values : Iterable[str]
        Iterable with the option values

    Returns
    -------
    Dict
        Options for the Dropdown
    """
    options = []
    for value in values:
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


def generate_selector(df_column: pd.Series, values: Iterable[str]):
    """
    Generates a selector based on values are in df_columns

    Parameters
    ----------
    df_column : pd.Series
        DataFrame colum which values should be compared to the values of values
    values : Iterable[str]
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
