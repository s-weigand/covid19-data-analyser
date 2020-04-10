from typing import Dict

import io

import pandas as pd

from covid19_data_analyzer.data_functions.scrapers import get_data


def generate_download_buffer(data_source: str, file_format: str) -> Dict:
    """
    Transdorms a dataframe to a given fileformat as buffer,
    which can be used for flask.send_file

    Parameters
    ----------
    data_source : str
        Name of the data source
    file_format : "csv" | "xls
        Format the file should be downloaded in

    Returns
    -------
    Dict
        dict containing the buffer, mimetype and filename
    """
    buffer = io.BytesIO()
    covid19_data = get_data(data_source)
    file_name = f"covid19_data_{data_source}"
    if file_format == "xls":
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as excel_writer:  # noqa: E0110
            covid19_data.to_excel(excel_writer, sheet_name="sheet1", index=False)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        file_name += ".xls"

    elif file_format == "csv":
        with io.StringIO() as str_buffer:
            covid19_data.to_csv(str_buffer, index=False)
            buffer.write(str_buffer.getvalue().encode("utf-8"))
            str_buffer.close()
        mimetype = "text/csv"
        file_name += ".csv"

    buffer.seek(0)
    return {"buffer": buffer, "file_name": file_name, "mimetype": mimetype}
