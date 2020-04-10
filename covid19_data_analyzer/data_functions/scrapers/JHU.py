import pandas as pd


from covid19_data_analyzer.data_functions.data_utils import (
    get_data_path,
    get_infectious,
    calc_country_total,
)


def get_JHU_data_subset(subset: str) -> pd.DataFrame:
    """
    Retrives covid19 data subset from JHU (Johns Hopkins University)
    https://github.com/CSSEGISandData/COVID-19

    Parameters
    ----------
    subset : str
        Name of the subset, currently 'confirmed' or 'deaths'
        see: https://github.com/CSSEGISandData/COVID-19/issues/1250

    Returns
    -------
    pd.DataFrame
        Dataframe containing the covid19 data subset from JHU
    """
    JHU_subset = pd.read_csv(
        f"https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{subset}_global.csv"  # noqa: E501
    ).drop(["Long", "Lat"], axis=1)
    JHU_subset.rename(
        columns={"Country/Region": "parent_region", "Province/State": "region"},
        inplace=True,
    )
    global_selector = JHU_subset["region"].isna()
    JHU_subset.loc[global_selector, "region"] = JHU_subset[global_selector][
        "parent_region"
    ]
    JHU_subset.loc[global_selector, "parent_region"] = "#Global"
    date_columns = JHU_subset.columns.drop(["region", "parent_region"])
    tranformed = JHU_subset.melt(
        id_vars=["region", "parent_region"],
        value_vars=date_columns,
        var_name="date",
        value_name=subset,
    )
    tranformed["date"] = pd.to_datetime(tranformed["date"])
    return tranformed


def get_JHU_data(update_data: bool = False) -> pd.DataFrame:
    """
    Retrives covid19 data from JHU (Johns Hopkins University)
    and transforms it to a uniform style
    https://github.com/CSSEGISandData/COVID-19

    Parameters
    ----------
    update_data : bool, optional
        Whether to fetch updated data or not, if the locally saved data
        doesn't include today.

    Returns
    -------
    pd.DataFrame
        Dataframe containing the covid19 data from JHU

    See Also
    --------
    get_JHU_data_subset
    """
    local_save_path = get_data_path("JHU/covid19_infections.csv")
    if local_save_path.exists():
        JHU_data = pd.read_csv(local_save_path, parse_dates=["date"])
    if not local_save_path.exists() or update_data:
        print("Fetching updated data: JHU")
        confirmed = get_JHU_data_subset("confirmed")
        deaths = get_JHU_data_subset("deaths")
        recovered = get_JHU_data_subset("recovered")
        JHU_data = pd.merge(confirmed, deaths, on=["date", "region", "parent_region"])
        JHU_data = pd.merge(JHU_data, recovered, on=["date", "region", "parent_region"])
        country_total = calc_country_total(JHU_data)
        JHU_data = JHU_data.append(country_total, ignore_index=True)
        get_infectious(JHU_data)
        JHU_data.sort_values(["date", "parent_region", "region"], inplace=True)
        JHU_data.set_index("date").to_csv(local_save_path)
    return JHU_data
