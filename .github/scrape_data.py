from covid19_data_analyzer.data_functions.scrapers.funkeinteraktiv import (
    get_funkeinteraktiv_data,
)
from covid19_data_analyzer.data_functions.scrapers.JHU import get_JHU_data


if __name__ == "__main__":
    get_funkeinteraktiv_data(update_data=True)
    get_JHU_data(update_data=True)
