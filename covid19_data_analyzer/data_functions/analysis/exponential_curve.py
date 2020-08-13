from typing import Dict, Union

import numpy as np
import pandas as pd

import lmfit
from lmfit.models import ExponentialModel

from covid19_data_analyzer.data_functions.analysis.factory_functions import (
    batch_fit_model,
    fit_data_model,
)


def fit_data_exponential_curve(
    covid19_data: pd.DataFrame,
    parent_region: str,
    region: str,
    data_set: str = "confirmed",
) -> Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]]:
    """
    Implementation of fit_data_model, with setting specific to
    the exponential curve model

    Parameters
    ----------
    covid19_data : pd.DataFrame
        Full covid19 data from a data_source
    parent_region : str
        parent_region of the data which should be fitted,
        needs to be in covid19_region_data.parent_region
    region : str
        region which data should be fired, needs to be in covid19_region_data.region
    data_set : str, optional
        which subdata schold be fitted, need to be of value
        ["confirmed", "recovered", deaths], by default "confirmed"

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

    def exp_func(x, amplitude=1, decay=1):
        return amplitude * np.exp(-x / decay)

    data_selector = (covid19_data.region == region) & (
        covid19_data.parent_region == parent_region
    )
    covid19_region_data = covid19_data.loc[data_selector, :].reset_index(drop=True)
    current_max = covid19_region_data[data_set].max()
    init_params = {
        "amplitude": current_max * 1e-3,
        "decay": -covid19_region_data.shape[0] / 7,
    }
    exp_model = ExponentialModel()
    exp_model.func = exp_func
    fit_result = fit_data_model(
        covid19_region_data, exp_model, data_set=data_set, init_params=init_params,
    )
    return fit_result


def batch_fit_exponential_curve():
    """
    Implementation of batch_fit_model, for the exponential curve model.

    See Also
    --------
    fit_data_exponential_curve
    batch_fit_model

    """
    batch_fit_model(
        fit_function=fit_data_exponential_curve, model_name="exponential_curve"
    )
