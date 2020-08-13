from typing import Dict

import pandas as pd

from covid19_data_analyzer.data_functions.scrapers import ALLOWED_SOURCES, get_data
from covid19_data_analyzer.data_functions.analysis import (
    get_fit_data,
    IMPLEMENTED_FIT_MODELS,
)


def get_fit_data_dict(kind: str) -> Dict[str, Dict[str, pd.DataFrame]]:
    return {
        data_source: {
            model_name: get_fit_data(data_source, model_name, kind)
            for model_name in IMPLEMENTED_FIT_MODELS
        }
        for data_source in ALLOWED_SOURCES
    }


DASHBOARD_DATA: Dict[str, pd.DataFrame] = {
    data_source: get_data(data_source) for data_source in ALLOWED_SOURCES
}

DASHBOARD_FIT_PLOT_DATA = get_fit_data_dict("plot")
DASHBOARD_FIT_PARAM_DATA = get_fit_data_dict("params")
