from datetime import datetime
from pathlib import Path

import pandas as pd

ALLOWED_SOURCES = ["morgenpost"]


def get_infectious(covid_df: pd.DataFrame, has_recovered: bool = False):
    """
    Calculates the number of still infectious people.
    This function uses the mutability of DataFrames,
    which is why it doesn't have a return value

    Parameters
    ----------
    covid_df : pd.DataFrame
        Dataframe containing all covid19 data
    has_recovered: bool
        Whether or not the dataset has a recovered column i.e. JHU doesn't
    """
    if has_recovered:
        covid_df["still_infectious"] = (
            covid_df.confirmed - covid_df.recovered - covid_df.deaths
        )
    else:
        covid_df["still_infectious"] = covid_df.confirmed - covid_df.deaths


def calc_country_total(covid_df):
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


def get_morgenpost_data(update_data=False):
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
    local_save_path = Path("./data/morgenpost/covid19_infections.csv")
    morgenpost_data = pd.read_csv(local_save_path, parse_dates=["date"])
    if morgenpost_data.date.max().date() != pd.Timestamp.today().date() and update_data:
        print("Fetching updated data: morgenpost")
        js_timestamp_now = int(datetime.now().timestamp() * 1e3)
        morgenpost_data = pd.read_csv(
            f"https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/data/Coronavirus.history.v2.csv?{js_timestamp_now}",
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
        get_infectious(morgenpost_data, has_recovered=True)
        morgenpost_data.sort_values(["date", "parent_region", "region"], inplace=True)
        morgenpost_data.set_index("date").to_csv(local_save_path)
    return morgenpost_data


def get_data(source="morgenpost", update_data=False):
    """
    Convenience function to quickly get covid19 data from the supported sources.

    Parameters
    ----------
    source : "morgenpost", optional
        source from which the data should be fetched, by default "morgenpost"

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
    else:
        raise ValueError(f"The source '{source}', is not supported.")


if __name__ == "__main__":
    get_morgenpost_data(update_data=True)
