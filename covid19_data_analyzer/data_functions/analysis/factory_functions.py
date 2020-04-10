from typing import Callable, Dict, Iterable, Tuple, Union
import itertools

import numpy as np
import pandas as pd

import lmfit

from covid19_data_analyzer.data_functions.data_utils import (
    get_fit_param_results_row,
    params_to_df,
)

from covid19_data_analyzer.data_functions.scrapers import ALLOWED_SOURCES, get_data
from covid19_data_analyzer.data_functions.data_utils import (
    get_data_path,
    get_infectious,
)


def fit_data_model(
    covid19_region_data: pd.DataFrame,
    model: lmfit.Model,
    data_set: str = "confirmed",
    init_params: dict = {},
    free_var_name: str = "x",
) -> Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]]:
    """
    Generic function to fit lmfit.Model models, onto a regional subset covid data.

    Parameters
    ----------
    covid19_region_data : pd.DataFrame
        covid19 DataFrame for one region
    model : lmfit.Model
        [description]
    data_set : str, optional
        which subdata schold be fitted, need to be of value
        ["confirmed" | "recovered" | deaths], by default "confirmed"
    init_params : dict, optional
        initial parameters for a fit, they depend on the model, by default {}
    free_var_name : str, optional
        name of the free variable used by the model, by default "x"

    Returns
    -------
    Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]]
        Result dict with keys "model_result" and "plot_data".

        model_result: lmfit.model.ModelResult
            result of the fit, with optimized parameters
        plot_data: pd.DataFrame
            Same as covid19_region_data, but with an resetted index and
            and added fir result

    """
    region_data = covid19_region_data.copy().reset_index(drop=True)
    x = np.arange(region_data.shape[0])
    y = region_data[data_set].values
    result = model.fit(y, **{free_var_name: x, **init_params})
    region_data[f"fitted_{data_set}"] = result.best_fit
    return {"model_result": result, "plot_data": region_data}


def calc_extrema(
    x: np.ndarray,
    func: Callable,
    param_df: pd.DataFrame,
    func_options: dict = {},
    brute_force_extrema: bool = False,
) -> Tuple[np.ndarray]:
    """
    Calculates the supremum and infimum of a given function func,
    with the parameters and their errors given by param_df, over the values of x.

    Parameters
    ----------
    x : np.ndarray
        Values the supremum and infimum should be calculated over
    func : Callable
        Functions used to calculate the supremum and infimum
    param_df : pd.DataFrame
        DataFrame with parameters and errors
    func_options : dict, optional
        options for func, by default {}
    brute_force_extrema : bool, optional
        Whether or not to calculate supremum and infimum from all permutations
        of adding and subtracting the errors from the parameters.
        For some functions, i.e. the logistic curve, this is needed, since simply
        adding or subtracting the errors from the parameter can lead to supremum and/or
        infimum to cross the result with the exact parameters., by default False

    Returns
    -------
    Tuple[np.ndarray]
        supremum, infimum
    """
    if brute_force_extrema:
        error_permutation_df = pd.DataFrame(
            itertools.product(*zip(param_df.stderr, -param_df.stderr)),
            columns=param_df.index,
        )
        param_permutation_df = error_permutation_df + param_df.value
        result_permutation_df = param_permutation_df.apply(
            lambda params: func(x, **{**params.to_dict(), **func_options}),
            axis=1,
            result_type="expand",
        )
        supremum = result_permutation_df.max()
        infimum = result_permutation_df.min()
    else:
        supremum_params = (param_df.value + param_df.stderr).to_dict()
        infimum_params = (param_df.value - param_df.stderr).to_dict()
        supremum = func(x, **{**supremum_params, **func_options})
        infimum = func(x, **{**infimum_params, **func_options})
    return supremum, infimum


def predict_trend(
    fit_result: Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]],
    days_to_predict: int = 30,
    func_options: dict = {},
    param_inverted_stderr: Iterable[str] = [],
    brute_force_extrema: bool = False,
) -> pd.DataFrame:
    """
    Generic function to predict a trend from fitted data

    Parameters
    ----------
    fit_result : Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]]
        result of fit_data_model or its implementation
    days_to_predict : int, optional
        number of days to predict a trend for, by default 30
    func_options : dict, optional
        options for the function of model, by default {}
    param_inverted_stderr : Iterable[str], optional
        iterable of parameternames with should be inverted,
        to calculate the extrema. , by default []
    brute_force_extrema : bool, optional
        Whether or not to calculate supremum and infimum from all permutations
        of adding and subtracting the errors from the parameters.
        For some functions, i.e. the logistic curve, this is needed, since simply
        adding or subtracting the errors from the parameter can lead to supremum and/or
        infimum to cross the result with the exact parameters., by default False


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
    fit_data_model
    calc_extrema
    params_to_df
    """
    model_result = fit_result["model_result"]
    func = model_result.model.func
    x = np.arange(model_result.ndata, model_result.ndata + days_to_predict)
    param_df = params_to_df(
        model_result.params, param_inverted_stderr=param_inverted_stderr
    )
    params = param_df.value.to_dict()
    date = fit_result["plot_data"].date.max() + pd.Series(x).apply(
        lambda x: pd.Timedelta(x + 1, unit="D")
    )
    trend = func(x, **{**params, **func_options})
    sup, inf = calc_extrema(
        x,
        func,
        param_df,
        func_options=func_options,
        brute_force_extrema=brute_force_extrema,
    )
    trend_df = pd.DataFrame(
        {"date": date, "trend": trend, "trend_sup": sup, "trend_inf": inf}
    )
    return trend_df.set_index(x)


def fit_subsets(
    fit_function: Callable,
    covid19_data: pd.DataFrame,
    row: pd.Series,
    subsets: Iterable,
    data_source: str,
    fit_func_kwargs: dict = {},
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Function to fit the subsets of a regional covid data

    Parameters
    ----------
    fit_function : Callable
        Implementation of a model with fit_data_model
    covid19_data : pd.DataFrame
        Full covid19 data from a data_source
    row : pd.Series
        Row of of a dataframe only containing unique value pairs for
        "region" and "parent_region"
    subsets : Iterable
        Iterable of subset names
    data_source : str
        name of the data source, only needed to print debug information
    fit_func_kwargs : dict, optional
        Additional kwargs passed to fit_function, by default {}

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        fitted_region_plot_data, fitted_param_subset

        fitted_region_plot_data:
            actual fitted data, which can be used for plotting
        fitted_param_subset:
            fit parameters for a region

    See Also
    --------
    fit_data_model
    fit_regions
    batch_fit_model
    """
    region = row.region
    parent_region = row.parent_region
    fitted_param_subset = pd.DataFrame()
    fitted_region_plot_data = None
    print(f"Fitting data for: {region}, from {data_source}")
    for subset in subsets:
        try:
            fit_result = fit_function(
                covid19_data, parent_region, region, subset, **fit_func_kwargs
            )
            fit_param_row = get_fit_param_results_row(
                region, parent_region, subset, fit_result
            )
            fitted_param_subset = fitted_param_subset.append(
                fit_param_row, ignore_index=True
            )
            fitted_data_column = f"fitted_{subset}"
            plot_data = fit_result["plot_data"][
                ["date", "region", "parent_region", fitted_data_column]
            ].copy()
            plot_data = plot_data.rename(columns={fitted_data_column: subset})
            if fitted_region_plot_data is None:
                fitted_region_plot_data = plot_data[
                    ["date", "region", "parent_region", subset]
                ]
            else:
                fitted_region_plot_data = pd.merge(
                    fitted_region_plot_data,
                    plot_data,
                    on=["date", "region", "parent_region"],
                )
        except (ValueError, TypeError):
            print(f"Error fitting data for: {region} {subset}, from {data_source}")
    if fitted_region_plot_data is None:
        return pd.DataFrame(), pd.DataFrame()
    else:
        return fitted_region_plot_data, fitted_param_subset


def fit_regions(
    covid19_data: pd.DataFrame,
    fit_function: Callable,
    data_source: str,
    fit_func_kwargs: dict = {},
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Function to fit all regions of a covid dataset

    Parameters
    ----------
    covid19_data : pd.DataFrame
        Full covid19 data from a data_source
    fit_function : Callable
        Implementation of a model with fit_data_model
    data_source : str
        name of the data source, only needed to print debug information
    fit_func_kwargs : dict, optional
        Additional kwargs passed to fit_function, by default {}

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        fitted_plot_data, fitted_param_results

        fitted_plot_data:
            actual fitted data, which can be used for plotting
        fitted_param_results:
            fit parameters

    See Also
    --------
    fit_subsets
    batch_fit_model
    """
    subset_selector = covid19_data.columns.isin(["confirmed", "deaths", "recovered"])
    subsets = covid19_data.columns[subset_selector]
    regions_df = covid19_data[["region", "parent_region"]].drop_duplicates("region")
    fitted_param_results = pd.DataFrame()
    fitted_plot_data = pd.DataFrame()
    for _, row in regions_df.iterrows():
        fitted_region_plot_data, fitted_param_subset = fit_subsets(
            fit_function=fit_function,
            covid19_data=covid19_data,
            row=row,
            subsets=subsets,
            data_source=data_source,
            fit_func_kwargs=fit_func_kwargs,
        )
        fitted_param_results = fitted_param_results.append(
            fitted_param_subset, ignore_index=True
        )
        fitted_plot_data = fitted_plot_data.append(
            fitted_region_plot_data, ignore_index=True
        )

    get_infectious(fitted_plot_data)

    fitted_param_results.sort_values(["parent_region", "region"], inplace=True)
    fitted_plot_data.sort_values(["date", "parent_region", "region"], inplace=True)
    return fitted_plot_data, fitted_param_results


def batch_fit_model(
    fit_function: Callable, model_name: str, fit_func_kwargs: dict = {},
) -> None:
    """
    Generic function to fit a fit_function to the data of all data sources and
    save them to file

    Parameters
    ----------
    fit_function : Callable
        Implementation of a model with fit_data_model
    model_name : str
        Name of the model which is fitted, used to generate the path
    fit_func_kwargs : dict, optional
        Additional kwargs passed to fit_function, by default {}

    See Also
    --------
    fit_subsets
    fit_regions
    """
    for data_source in ALLOWED_SOURCES:
        covid19_data = get_data(data_source)
        fitted_plot_data, fitted_param_results = fit_regions(
            covid19_data=covid19_data,
            fit_function=fit_function,
            data_source=data_source,
            fit_func_kwargs=fit_func_kwargs,
        )
        fitted_plot_data_path = get_data_path(
            f"{data_source}/{model_name}_model_fit_plot_data.csv"
        )
        fitted_param_results_path = get_data_path(
            f"{data_source}/{model_name}_model_fit_params.csv"
        )

        fitted_param_results.to_csv(fitted_param_results_path, index=False)
        fitted_plot_data.to_csv(fitted_plot_data_path, index=False)
