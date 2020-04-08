from typing import Callable, Dict, Iterable, Tuple, Union
import itertools

import numpy as np
import pandas as pd

import lmfit
from lmfit.models import StepModel

from data_scraper import ALLOWED_SOURCES, get_data, get_data_path, get_infectious

IMPLEMENTED_FIT_MODELS = ["logistic_curve"]

LOGISTIC_MODEL = StepModel(form="logistic")


def get_shifted_dfs(
    covid_df: pd.DataFrame,
    time_shift: Union[int, float] = 1,
    time_shift_unit: str = "D",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Helper function to shift the date of the covid data by a given time
    and gain DataFrames which can be used to calculate the growth and growth rate.

    Parameters
    ----------
    covid_df : pd.DataFrame
        Full covid19 data from a data_source
    time_shift : [int,float], optional
        value by which the time should be shifted, by default 1
    time_shift_unit : str, optional
        unit of the time shift , by default "D"

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        shifted and unshifted covid19 data, with date, parent_region and region as index
    """
    unshifted_data = covid_df.set_index(["date", "parent_region", "region"])
    shifted_data = covid_df.copy()
    shifted_data.date = shifted_data.date + pd.Timedelta(
        time_shift, unit=time_shift_unit
    )
    shifted_data = shifted_data.set_index(["date", "parent_region", "region"])
    return unshifted_data, shifted_data


def get_daily_growth(covid_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the daily growth values

    Parameters
    ----------
    covid_df : pd.DataFrame
        Full covid19 data from a data_source

    Returns
    -------
    pd.DataFrame
        covid19 DataFrame, with daily growth values instead of totals.
    """
    unshifted_data, shifted_data = get_shifted_dfs(covid_df)
    daily_increase = unshifted_data - shifted_data
    return daily_increase.dropna().reset_index()


def get_growth_rate(covid_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the growth rate values

    Parameters
    ----------
    covid_df : pd.DataFrame
        Full covid19 data from a data_source

    Returns
    -------
    pd.DataFrame
        covid19 DataFrame, with growth rate values instead of totals.
    """
    daily_growth = get_daily_growth(covid_df)
    unshifted_data, shifted_data = get_shifted_dfs(daily_growth)
    # the '+1' is needed to prevent zero division
    growth_rate = unshifted_data / (shifted_data + 1)
    return growth_rate.dropna().reset_index()


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
    covid19_region_data : pd.DataFrame
        covid19 DataFrame for one region
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


def params_to_dict(params: lmfit.Parameters, kind: str = "values") -> dict:
    """
    Converts fit result parameters to a dict

    Parameters
    ----------
    params : lmfit.Parameters
        fit result parameters
    kind : str, optional
        ["values", "stderr"], by default "values"

    Returns
    -------
    dict
        Dict containing the parameternames as key and the values or stderr as values
    """
    result_dict = {}
    for name, param in params.items():
        if kind == "values":
            result_dict[name] = param.value
        elif kind == "stderr":
            result_dict[name] = param.stderr
    return result_dict


def params_to_df(
    params: lmfit.Parameters, param_inverted_stderr: Iterable[str] = []
) -> pd.DataFrame:
    """
    Returns a DataFrame with the values and stderr of the params

    Parameters
    ----------
    params : lmfit.Parameters
        fit result parameters
    param_inverted_stderr : Iterable[str], optional
        iterable of parameternames with should be inverted,
        to calculate the extrema. , by default []

    Returns
    -------
    pd.DataFrame
        DataFrame with columns "value" and "stderr", parameternames as index
    """
    param_vals = params_to_dict(params)
    param_stderrs = params_to_dict(params, kind="stderr")
    param_df = pd.DataFrame({"value": param_vals, "stderr": param_stderrs})
    param_df.loc[param_inverted_stderr, "stderr"] = -param_df.loc[
        param_inverted_stderr, "stderr"
    ]
    return param_df


def get_fit_param_results_row(
    region: str,
    parent_region: str,
    subset: str,
    fit_result: Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]],
) -> pd.DataFrame:
    """
    Returns a row containing all fitted parameters for a region,
    which can than be combined to a fit param results dataframe

    Parameters
    ----------
    region : str
        Value of the fitted region
    parent_region : str
        Parent region of the fitted region
    subset:str
        Subset of the regions data which was fitted
    fit_result : Dict[str, Union[lmfit.model.ModelResult, pd.DataFrame]]
        Result of fit_data_model or its implementation

    Returns
    -------
    pd.DataFrame
        Row of fit param results dataframe, for the fitted region

    See Also
    --------
    fit_data_model
    """
    flat_params_df = pd.DataFrame(
        [{"region": region, "parent_region": parent_region, "subset": subset}]
    )
    params_df = params_to_df(fit_result["model_result"].params)
    transformed_df = (
        params_df.reset_index()
        .melt(id_vars="index", var_name="kind")
        .sort_values("index")
    )
    new_index = transformed_df["index"] + " " + transformed_df["kind"]
    transformed_df = (
        transformed_df.set_index(new_index).drop(["index", "kind"], axis=1).T
    )
    flat_params_df = flat_params_df.join(transformed_df.reset_index(drop=True))
    return flat_params_df


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


def translate_funkeinteraktiv_fit_data():
    """
    Helperfunction to prevent Fitting overhead,
    which would be caused if the same dataset with de and en
    region names would be fitted.
    Rather than fitting twice, this function simply translates
    the german region names to the english ones, which were both extracted by
    'get_funkeinteraktiv_data'.
    """
    source_dir = get_data_path("funkeinteraktiv_de")
    target_dir = get_data_path("funkeinteraktiv_en")
    translate_path = source_dir / "translation_table.csv"
    translate_df = pd.read_csv(translate_path).rename(
        {"label_parent_en": "parent_region", "label_en": "region"}, axis=1
    )
    region_df = translate_df[["region", "label"]].set_index("label", drop=True)
    parent_region_df = translate_df[["parent_region", "label_parent"]].set_index(
        "label_parent", drop=True
    )
    translate_dict = {**parent_region_df.to_dict(), **region_df.to_dict()}
    for source_file_path in source_dir.glob("*model_fit*.csv"):
        data_df = pd.read_csv(source_file_path)
        rel_path = source_file_path.relative_to(source_dir)
        target_file_path = target_dir / rel_path
        data_df.replace(translate_dict).to_csv(target_file_path, index=False)


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
            fit_result = fit_function(covid19_data, region, subset, **fit_func_kwargs)
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


def batch_fit_logistic_curve():
    """
    Implementation of batch_fit_model, for the logistic curve model.


    See Also
    --------
    fit_data_logistic_curve
    batch_fit_model
    """
    batch_fit_model(fit_function=fit_data_logistic_curve, model_name="logistic_curve")


def get_fit_plot_data(data_source, model_name="logistic_curve"):
    if model_name in IMPLEMENTED_FIT_MODELS and data_source in ALLOWED_SOURCES:
        fitted_plot_data_path = get_data_path(
            f"{data_source}/{model_name}_model_fit_plot_data.csv"
        )
        return pd.read_csv(fitted_plot_data_path, parse_dates=["date"])
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


if __name__ == "__main__":
    ALLOWED_SOURCES.remove("funkeinteraktiv_en")
    batch_fit_logistic_curve()
    translate_funkeinteraktiv_fit_data()
