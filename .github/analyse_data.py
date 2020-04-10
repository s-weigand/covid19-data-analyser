from covid19_data_analyzer.data_functions.data_utils import (
    translate_funkeinteraktiv_fit_data,
)

from covid19_data_analyzer.data_functions.scrapers import ALLOWED_SOURCES

from covid19_data_analyzer.data_functions.analysis.logistic_curve import (
    batch_fit_logistic_curve,
)
from covid19_data_analyzer.data_functions.analysis.exponential_curve import (
    batch_fit_exponential_curve,
)


if __name__ == "__main__":
    ALLOWED_SOURCES.remove("funkeinteraktiv_en")
    batch_fit_logistic_curve()
    batch_fit_exponential_curve()
    translate_funkeinteraktiv_fit_data()
