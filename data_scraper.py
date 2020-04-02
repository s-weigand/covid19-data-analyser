from datetime import datetime
from pathlib import Path

import pandas as pd

ALLOWED_SOURCES = ["morgenpost", "JHU"]


def get_data_path(sub_path: str) -> Path:
    """
    Returns the Path object of a path in data

    Parameters
    ----------
    sub_path : str
        subpath in data directory

    Returns
    -------
    Path
        Path to a file in data
    """
    data_base_path = Path(__file__).parent / "data"
    return data_base_path / sub_path


def get_infectious(covid_df: pd.DataFrame) -> None:
    """
    Calculates the number of still infectious people.
    This function uses the mutability of DataFrames,
    which is why it doesn't have a return value

    Parameters
    ----------
    covid_df : pd.DataFrame
        Dataframe containing all covid19 data
    """
    if covid_df.columns.isin(["recovered"]).any():
        recovered = covid_df.recovered.fillna(0)
    else:
        recovered = 0
    deaths = covid_df.deaths.fillna(0)
    covid_df["still_infectious"] = covid_df.confirmed - recovered - deaths


def calc_country_total(covid_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the total for each country from the covid_df,
    where only data for regions was present before

    Parameters
    ----------
    covid_df : pd.DataFrame
        covid19 DataFrame

    Returns
    -------
    pd.DataFrame
        Dataframe containing the totals for countries, which before only had
        their regions listed.
    """
    total_df = pd.DataFrame()
    for (parent, date), group in covid_df.groupby(["parent_region", "date"]):
        if parent != "#Global":
            country_total = group.sum()
            country_total.parent_region = "#Global"
            country_total.region = f"{parent} (total)"
            country_total["date"] = date
            total_df = total_df.append(country_total, ignore_index=True)
    return total_df


def get_morgenpost_data(update_data: bool = False) -> pd.DataFrame:
    """
    Retrives covid19 data from morgenpost API, which is used to generate the following website:
    https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/

    Parameters
    ----------
    update_data : bool, optional
        Whether to fetch updated data or not, if the locally saved data
        doesn't include today.

    Returns
    -------
    pd.DataFrame
        Dataframe containing the covid19 data from morgenpost.de
    """
    local_save_path = get_data_path("morgenpost/covid19_infections.csv")
    morgenpost_data = pd.read_csv(local_save_path, parse_dates=["date"])
    if morgenpost_data.date.max().date() != pd.Timestamp.today().date() and update_data:
        print("Fetching updated data: morgenpost")
        js_timestamp_now = int(datetime.now().timestamp() * 1e3)
        morgenpost_data = pd.read_csv(
            f"https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/data/Coronavirus.history.v2.csv?{js_timestamp_now}",  # noqa: E501
            parse_dates=["date"],
        ).drop(["lon", "lat"], axis=1)
        morgenpost_data.rename(
            columns={"label": "region", "parent": "parent_region"}, inplace=True
        )
        morgenpost_data.loc[
            morgenpost_data.parent_region == "global", "parent_region"
        ] = "#Global"
        country_total = calc_country_total(morgenpost_data)
        morgenpost_data = morgenpost_data.append(country_total, ignore_index=True)
        get_infectious(morgenpost_data)
        morgenpost_data.sort_values(["date", "parent_region", "region"], inplace=True)
        morgenpost_data.set_index("date").to_csv(local_save_path)
    return morgenpost_data


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
    """
    local_save_path = get_data_path("JHU/covid19_infections.csv")
    JHU_data = pd.read_csv(local_save_path, parse_dates=["date"])
    if JHU_data.date.max().date() != pd.Timestamp.today().date() and update_data:
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


def get_data(source: str = "morgenpost", update_data: bool = False) -> pd.DataFrame:
    """
    Convenience function to quickly get covid19 data from the supported sources.

    Parameters
    ----------
    source : "morgenpost", optional
        source from which the data should be fetched, by default "morgenpost"

    update_data : bool, optional
        Whether to fetch updated data or not, if the locally saved data
        doesn't include today.

    Returns
    -------
    pd.DataFrame
        covid19 DataFrame

    Raises
    ------
    ValueError
        If source is not supported
    """
    if source == "morgenpost":
        return get_morgenpost_data(update_data=update_data)
    elif source == "JHU":
        return get_JHU_data(update_data=update_data)
    else:
        raise ValueError(f"The source '{source}', is not supported.")


if __name__ == "__main__":
    get_morgenpost_data(update_data=True)
    get_JHU_data(update_data=True)
