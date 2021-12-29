from gspread import Spreadsheet
from gspread.urls import SPREADSHEETS_API_V4_BASE_URL

from ._version import __version__, __version_info__
from .client import Client
from .spread import Spread

__all__ = ["Spread", "Client", "__version__", "__version_info__"]
SPREADSHEET_VALUES_BATCH_URL = SPREADSHEETS_API_V4_BASE_URL + "/%s/values:batchGet"


def values_batch_get(self, ranges, params=None):
    """
    Lower-level method that directly calls `spreadsheets.values.batchGet.

    <https://develop
    ers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchGet>`_.

    Parameters
    ----------
    rantes : list of strings
        List of ranges in the `A1 notation
    params : dict
        (optional) Query parameters

    Returns
    -------
    dict
        Response body
    """
    if params is None:
        params = {}

    params.update(ranges=ranges)

    url = SPREADSHEET_VALUES_BATCH_URL % (self.id)
    r = self.client.request("get", url, params=params)
    return r.json()


Spreadsheet.values_batch_get = values_batch_get
