from typing import Tuple
import pandas as pd


def get_shifted_dfs(covid_df, time_shift=1, time_shift_unit="D"):
    """
    Helper function to shift the date of the covid data by a given time
    and gain dataframes which can be used to calculate the growth and growth rate.

    Parameters
    ----------
    covid_df : pd.DataFrame
        covid19 DataFrame
    time_shift : int, optional
        value by which the time should be shifted, by default 1
    time_shift_unit : str, optional
        unit of the time shift , by default "D"

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        shifted and unshifted covid19 data, with date, parent_region and region as index
    """
    unshifted_data = covid_df.set_index(["date", "parent_region", "region"])
    shifted_data = covid_df.copy()
    shifted_data.date = shifted_data.date + pd.Timedelta(
        time_shift, unit=time_shift_unit
    )
    shifted_data = shifted_data.set_index(["date", "parent_region", "region"])
    return unshifted_data, shifted_data


def get_daily_growth(covid_df):
    """
    Calculates the daily growth values

    Parameters
    ----------
    covid_df : pd.DataFrame
        covid19 DataFrame

    Returns
    -------
    pd.DataFrame
        covid19 DataFrame, with daily growth values instead of totals.
    """
    unshifted_data, shifted_data = get_shifted_dfs(covid_df)
    daily_increase = unshifted_data - shifted_data
    return daily_increase.dropna().reset_index()


def get_growth_rate(covid_df):
    """
    Calculates the growth rate values

    Parameters
    ----------
    covid_df : pd.DataFrame
        [description]

    Returns
    -------
    pd.DataFrame
        covid19 DataFrame, with growth rate values instead of totals.
    """
    daily_increase_df = get_daily_growth(covid_df)
    unshifted_data, shifted_data = get_shifted_dfs(daily_increase_df)
    # the '+1' is needed to prevent zero division
    growth_rate = shifted_data / (unshifted_data + 1)
    return growth_rate.dropna().reset_index()
