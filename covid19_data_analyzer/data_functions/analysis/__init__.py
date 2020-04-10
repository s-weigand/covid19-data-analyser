import pandas as pd

from covid19_data_analyzer.data_functions.data_utils import get_data_path
from covid19_data_analyzer.data_functions.scrapers import ALLOWED_SOURCES


IMPLEMENTED_FIT_MODELS = ["exponential_curve", "logistic_curve"]


def get_fit_data(
    data_source: str, model_name="logistic_curve", kind="plot"
) -> pd.DataFrame:
    """
    Convenience function to quickly get the fitted data from the supported sources.

    Parameters
    ----------
    data_source : str
        Name of the source the fitted data was fetched from.
    model_name : str, optional
        Name of the model which was used for fitting, by default "logistic_curve"
    kind : str, optional
        kind of data you want to retrieve, by default "plot"

    Returns
    -------
    pd.DataFrame
        Plot data or parameters, depending on 'kind'

    Raises
    ------
    ValueError
        If the model_name isn't supported
    ValueError
        If the data_source isn't supported
    """
    if model_name in IMPLEMENTED_FIT_MODELS and data_source in ALLOWED_SOURCES:
        if kind == "plot":
            fitted_plot_data_path = get_data_path(
                f"{data_source}/{model_name}_model_fit_plot_data.csv"
            )
            return pd.read_csv(fitted_plot_data_path, parse_dates=["date"])
        elif kind == "params":
            fitted_param_results_path = get_data_path(
                f"{data_source}/{model_name}_model_fit_params.csv"
            )
            return pd.read_csv(fitted_param_results_path)
        else:
            raise ValueError("The value of 'kind' need to be 'plot' or 'params'.")

    elif model_name not in IMPLEMENTED_FIT_MODELS:
        raise ValueError(
            f"The model '{model_name}' is not in "
            "IMPLEMENTED_FIT_MODELS ({IMPLEMENTED_FIT_MODELS}). "
            "If you just implemented a new model, make sure to add it to"
            "'IMPLEMENTED_FIT_MODELS'."
        )
    else:
        raise ValueError(
            f"The data_source '{data_source}', is not supported.\n"
            f"The supported values for 'data_source' are {ALLOWED_SOURCES}"
        )
