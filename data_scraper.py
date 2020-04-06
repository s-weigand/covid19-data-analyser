from pathlib import Path

import pandas as pd

ALLOWED_SOURCES = ["funkeinteraktiv_de", "funkeinteraktiv_en", "JHU"]


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


def get_funkeinteraktiv_language_data(
    covid19_data: pd.DataFrame, language: str
) -> pd.DataFrame:
    """
    Helperfunction to select in which language the region and parent_region
    values should be represented

    Parameters
    ----------
    covid19_data : pd.DataFrame
        covid19 DataFrame from "https://funkeinteraktiv.b-cdn.net/history.v4.csv"
    language : "de"|"en"
        Language in which the region and parent_region values should be represented

    Returns
    -------
    pd.DataFrame
        [description]

    See Also
    --------
    get_funkeinteraktiv_data
    """
    target_labels = ["region", "parent_region"]
    language_labels_de = ["label", "label_parent"]
    language_labels_en = ["label_en", "label_parent_en"]
    if language == "de":
        rename_dict = dict(zip(language_labels_de, target_labels))
        drop_list = language_labels_en
    else:
        rename_dict = dict(zip(language_labels_en, target_labels))
        drop_list = language_labels_de
    return covid19_data.drop(drop_list, axis=1).rename(columns=rename_dict)


def get_funkeinteraktiv_data(
    update_data: bool = False, language: str = "de"
) -> pd.DataFrame:
    """
    Retrives covid19 data from morgenpost API, which is used to generate the following website:
    https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/

    Parameters
    ----------
    update_data : bool, optional
        Whether to fetch updated data or not, if the locally saved data
        doesn't include today.

    language: "de"|"en", optional
        Language in which the region and parent_region values should be represented

    Returns
    -------
    pd.DataFrame
        Dataframe containing the covid19 data from morgenpost.de
    """
    translation_table_path = get_data_path("funkeinteraktiv_de/translation_table.csv")
    local_save_path_de = get_data_path("funkeinteraktiv_de/covid19_infections.csv")
    local_save_path_en = get_data_path("funkeinteraktiv_en/covid19_infections.csv")
    if language == "de":
        local_save_path = local_save_path_de
    else:
        local_save_path = local_save_path_en
    if local_save_path.exists():
        funkeinteraktiv_data = pd.read_csv(local_save_path, parse_dates=["date"])
    if not local_save_path.exists() or update_data:
        print("Fetching updated data: funkeinteraktiv")
        columns_to_drop = [
            "id",
            "parent",
            "lon",
            "lat",
            "levels",
            "updated",
            "retrieved",
            "source",
            "source_url",
            "scraper",
        ]
        funkeinteraktiv_data = pd.read_csv(
            f"https://funkeinteraktiv.b-cdn.net/history.v4.csv", parse_dates=["date"],
        ).drop(columns_to_drop, axis=1)
        funkeinteraktiv_data.fillna(
            {"label_parent": "#Global", "label_parent_en": "#Global"}, inplace=True
        )
        get_infectious(funkeinteraktiv_data)
        funkeinteraktiv_data.sort_values(
            ["date", "label_parent", "label"], inplace=True
        )

        get_funkeinteraktiv_language_data(funkeinteraktiv_data, "de").set_index(
            "date"
        ).to_csv(local_save_path_de)

        get_funkeinteraktiv_language_data(funkeinteraktiv_data, "en").set_index(
            "date"
        ).to_csv(local_save_path_en)

        funkeinteraktiv_data[
            ["label_parent", "label", "label_parent_en", "label_en"]
        ].drop_duplicates().to_csv(translation_table_path, index=False)

        funkeinteraktiv_data = get_funkeinteraktiv_language_data(
            funkeinteraktiv_data, language=language
        )
    return funkeinteraktiv_data


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


def get_data(
    source: str = "funkeinteraktiv_de", update_data: bool = False
) -> pd.DataFrame:
    """
    Convenience function to quickly get covid19 data from the supported sources.

    Parameters
    ----------
    source : "funkeinteraktiv_de"|"funkeinteraktiv_en"|"JHU", optional
        source from which the data should be fetched, by default "funkeinteraktiv_de"

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
    if source == "funkeinteraktiv_de":
        return get_funkeinteraktiv_data(update_data=update_data, language="de")
    elif source == "funkeinteraktiv_en":
        return get_funkeinteraktiv_data(update_data=update_data, language="en")
    elif source == "JHU":
        return get_JHU_data(update_data=update_data)
    else:
        raise ValueError(f"The source '{source}', is not supported.")


if __name__ == "__main__":
    get_funkeinteraktiv_data(update_data=True)
    get_JHU_data(update_data=True)
