from typing import Dict, Iterable, Tuple, Union
from pathlib import Path

import lmfit
import pandas as pd


def get_data_path(sub_path: str) -> Path:
    """
    Returns the Path object of a path in data and
    creates the parent folders if they don't exist already

    Parameters
    ----------
    sub_path : str
        subpath in data directory

    Returns
    -------
    Path
        Path to a file in data
    """
    data_base_path = Path(__file__).parent.parent / "data"
    data_path = data_base_path / sub_path
    if data_path.suffixes == []:
        data_path.mkdir(parents=True, exist_ok=True)
    else:
        data_path.parent.mkdir(parents=True, exist_ok=True)
    return data_path


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
        covid19 DataFrame (needs to be in uniform style)

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


def calc_worldwide_total(
    covid_df: pd.DataFrame, parent_region_label="parent_region", region_label="region"
) -> pd.DataFrame:
    """
    Calculates the worldwide total.

    Parameters
    ----------
    covid_df : pd.DataFrame
        covid19 DataFrame (needs to be in uniform style)
    parent_region_label: str
        name of the parent_region column
    region_label: str
        name of the region column

    Returns
    -------
    pd.DataFrame
        Dataframe containing the worldwide totals.
    """
    global_country_df = covid_df[covid_df[parent_region_label] == "#Global"]
    worldwide_total_df = global_country_df.groupby(["date"]).sum()
    worldwide_total_df[parent_region_label] = "#Global"
    worldwide_total_df[region_label] = "#Worldwide"
    worldwide_total_df.reset_index(inplace=True)
    return worldwide_total_df


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
    param_df = pd.DataFrame({"values": param_vals, "stderr": param_stderrs})
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
    covid19_data_analyzer.data_functions.analysis.factory_functions.fit_data_model
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
