from typing import Dict, Union

import pandas as pd

import lmfit
from lmfit.models import StepModel


from covid19_data_analyzer.data_functions.analysis.factory_functions import (
    batch_fit_model,
    fit_data_model,
    predict_trend,
)


LOGISTIC_MODEL = StepModel(form="logistic")


def fit_data_logistic_curve(
    covid19_data: pd.DataFrame,
    region: str,
    data_set: str = "confirmed",
    sigma: Union[int, float] = 5,
) -> Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]]:
    """
    Implementation of fit_data_model, with setting specific to
    the logistic curve model

    Parameters
    ----------
    covid19_data : pd.DataFrame
        Full covid19 data from a data_source
    region : str
        region which data should be fired, needs to be in covid19_region_data.region
    data_set : str, optional
        which subdata schold be fitted, need to be of value
        ["confirmed", "recovered", deaths], by default "confirmed"
    sigma : int, optional
        initial value for the parameter 'sigma' of the logistic curve model,
        by default 14

    Returns
    -------
    Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]]
        Result dict with keys "model_result" and "plot_data".

        model_result: lmfit.model.ModelResult
            result of the fit, with optimized parameters
        plot_data: pd.DataFrame
            Same as covid19_region_data, but with an resetted index and
            and added fir result

    See Also
    --------
    fit_data_model
    """
    covid19_region_data = covid19_data.loc[
        covid19_data.region == region, :
    ].reset_index(drop=True)
    center = covid19_region_data[
        covid19_region_data[data_set] > covid19_region_data[data_set].max() / 2
    ].index.min()
    init_params = {
        "amplitude": covid19_region_data[data_set].max(),
        "center": center,
        "sigma": sigma,
    }
    fit_result = fit_data_model(
        covid19_region_data, LOGISTIC_MODEL, data_set=data_set, init_params=init_params
    )
    return fit_result


def predict_trend_logistic_curve(
    fit_result: Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]],
    days_to_predict: int = 30,
) -> pd.DataFrame:
    """
    Implementation of fit_data_model, with setting specific to
    the logistic curve model


    Parameters
    ----------
    fit_result : Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]]
        result of fit_data_model or its implementation
    days_to_predict : int, optional
        number of days to predict a trend for, by default 30


    Returns
    -------
    pd.DataFrame
        DataFrame with columns "date", "trend", "trend_sup" and "trend_inf"

        date: pd.Datetime
            date of the values
        trend: float
            predicted trend
        trend_sup: float
            supremum of the trend
        trend_inf: float
            infimum of the trend

    See Also
    --------
    predict_trend
    fit_data_model
    calc_extrema
    params_to_df
    """

    return predict_trend(
        fit_result,
        days_to_predict=days_to_predict,
        func_options={"form": "logistic"},
        brute_force_extrema=True,
    )


def batch_fit_logistic_curve():
    """
    Implementation of batch_fit_model, for the logistic curve model.

    See Also
    --------
    fit_data_logistic_curve
    batch_fit_model
    """
    batch_fit_model(fit_function=fit_data_logistic_curve, model_name="logistic_curve")
