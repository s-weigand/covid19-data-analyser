from datetime import datetime
from pathlib import Path

import pandas as pd

ALLOWED_SOURCES = ["morgenpost"]


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
    local_save_path = Path("./data/morgenpost/covid19_infections.csv").resolve()
    morgenpost_data = pd.read_csv(local_save_path, parse_dates=["date"])
    if morgenpost_data.date.max().date() != pd.Timestamp.today().date() and update_data:
        print("Fetching updated data")
        js_timestamp_now = int(datetime.now().timestamp() * 1e3)
        morgenpost_data = pd.read_csv(
            f"https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/data/Coronavirus.history.v2.csv?{js_timestamp_now}",
            parse_dates=["date"],
        ).drop(["lon", "lat"], axis=1)
        country_total = calc_morgenpost_country_total(morgenpost_data)
        morgenpost_data = morgenpost_data.append(country_total, ignore_index=True)
        morgenpost_data.rename(
            columns={"label": "region", "parent": "parent_region"}, inplace=True
        )
        morgenpost_data.sort_values(["date", "parent_region", "region"], inplace=True)
        morgenpost_data.set_index("date").to_csv(local_save_path)
    return morgenpost_data


def calc_morgenpost_country_total(morgenpost_df):
    """
    Calculates the total for each country from the morgenpost_df,
    where only data for regions was present before

    Parameters
    ----------
    morgenpost_df : pd.DataFrame
        Data fetched frm the morgenpost API

    Returns
    -------
    pd.DataFrame
        Dataframe containing the totals for countries, which before only had
        their regions listed.
    """
    total_df = pd.DataFrame()
    for (parent, date), group in morgenpost_df.groupby(["parent", "date"]):
        if parent != "global":
            country_total = group.sum()
            country_total.parent = "global"
            country_total.label = f"{parent} (total)"
            country_total["date"] = date
            total_df = total_df.append(country_total, ignore_index=True)
    return total_df


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
