import pandas as pd

from covid19_data_analyzer.data_functions.data_utils import (
    get_data_path,
    get_infectious,
)


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
