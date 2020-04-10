import pandas as pd

from covid19_data_analyzer.data_functions.scrapers.funkeinteraktiv import (
    get_funkeinteraktiv_data,
)
from covid19_data_analyzer.data_functions.scrapers.JHU import get_JHU_data

ALLOWED_SOURCES = ["funkeinteraktiv_de", "funkeinteraktiv_en", "JHU"]


def get_data(
    data_source: str = "funkeinteraktiv_de", update_data: bool = False
) -> pd.DataFrame:
    """
    Convenience function to quickly get covid19 data from the supported sources.

    Parameters
    ----------
    data_source : "funkeinteraktiv_de"|"funkeinteraktiv_en"|"JHU", optional
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
        If data_source is not supported
    """
    if data_source == "funkeinteraktiv_de":
        return get_funkeinteraktiv_data(update_data=update_data, language="de")
    elif data_source == "funkeinteraktiv_en":
        return get_funkeinteraktiv_data(update_data=update_data, language="en")
    elif data_source == "JHU":
        return get_JHU_data(update_data=update_data)
    else:
        raise ValueError(
            f"The data_source '{data_source}', is not supported.\n"
            f"The supported values for 'data_source' are {ALLOWED_SOURCES}"
        )
