from __future__ import print_function

from re import match
from os import path

from builtins import str, range
from past.builtins import basestring

import numpy as np
import pandas as pd
import gspread

from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound, NoValidUrlKeyFound
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser

from decorator import decorator

from gspread_pandas.conf import get_config

__all__ = ['Spread']

default_scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/userinfo.email'
]

ROW = 0
COL = 1

class Spread():
    """
    Simple wrapper for gspread to interact with Pandas. It holds an instance of
    an 'open' spreadsheet, an 'open' worksheet, and a list of available worksheets.

    Each user will be associated with specific OAuth credentials. The authenticated user will
    need the appropriate permissions to the Spreadsheet in order to interact with it.
    """
    #: `(gspread.models.Spreadsheet)` - Currently open Spreadsheet
    spread = None

    #: `(gspread.models.Worksheet)` - Currently open Worksheet
    sheet = None

    #: `(list)` - List of available Worksheets
    sheets = []

    #: `(str)` - E-mail for the currently authenticated user
    email = ''

    #: `(gspread.client.Client)` - Current gspread Client
    client = None

    # chunk range request: https://github.com/burnash/gspread/issues/375
    _max_range_chunk_size = 200000

    # chunk update_cells: https://github.com/burnash/gspread/issues/384
    _max_update_chunk_size = 40000

    def __init__(self, user, spread, sheet=None, config=None):
        """
        :param str user: string indicating the key to a users credentials, which will
            be stored in a file (by default they will be stored in
            ``~/.config/gspread_pandas/creds/<user>`` but can be modified with ``creds_dir``
            property in config)
        :param str spread: name, url, or id of the spreadsheet; must have read access by
            the authenticated user,
            see :meth:`open_spread <gspread_pandas.client.Spread.open_spread>`
        :param str,int sheet: optional, name or index of Worksheet,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)
        :param dict config: optional, if you want to provide an alternate configuration,
            see :meth:`get_config <gspread_pandas.conf.get_config>`
        """
        self._config = config or get_config()
        self._creds_file = path.join(self._config['creds_dir'], user)
        self._login()
        self.email = self._get_email()

        self.open(spread, sheet)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        base = "<gspread_pandas.client.Spread - '{0}'>"
        meta = []
        if self.email:
            meta.append("User: '{0}'".format(self.email))
        if self.spread:
            meta.append("Spread: '{0}'".format(self.spread.title))
        if self.sheet:
            meta.append("Sheet: '{0}'".format(self.sheet.title))
        return base.format(", ".join(meta))

    @decorator
    def _ensure_auth(func, self, *args, **kwargs):
        self.client.login()
        return func(self, *args, **kwargs)

    def _get_email(self):
        try:
            return self\
                .client\
                .session\
                .get('https://www.googleapis.com/userinfo/v2/me')\
                .json()['email']
        except:
            print("""
            Couldn't retrieve email. Delete ~/.config/gspread_pandas/creds and authenticate again
            """)

    def _authorize(self):
        flow = OAuth2WebServerFlow(
            client_id=self._config['client_id'],
            client_secret=self._config['client_secret'],
            redirect_uri=self._config['redirect_uris'][0],
            scope=default_scope)

        storage = Storage(self._creds_file)

        args = argparser.parse_args(args=['--noauth_local_webserver'])

        return run_flow(flow, storage, args)

    def _login(self):
        creds = None

        if path.exists(self._creds_file):
            creds = Storage(self._creds_file).locked_get()
        else:
            creds = self._authorize()

        self.client = gspread.authorize(creds)

    @_ensure_auth
    def _refresh_sheets(self):
        self.sheets = self.spread.worksheets()

    def open(self, spread, sheet=None):
        """
        Open a spreadsheet, and optionally a worksheet. See
        :meth:`open_spread <gspread_pandas.Spread.open_spread>` and
        :meth:`open_sheet <gspread_pandas.Spread.open_sheet>`.

        :param str spread: name, url, or id of Spreadsheet
        :param str,int sheet: name or index of Worksheet
        """
        self.open_spread(spread)

        if sheet is not None:
            self.open_sheet(sheet)

    @_ensure_auth
    def open_spread(self, spread):
        """
        Open a spreadsheet. Authorized user must already have read access.

        :param str spread: name, url, or id of Spreadsheet
        """
        self.spread = None

        try:
            self.spread = self.client.open(spread)
        except SpreadsheetNotFound:
            try:
                self.spread = self.client.open_by_url(spread)
            except (SpreadsheetNotFound, NoValidUrlKeyFound):
                try:
                    self.spread = self.client.open_by_key(spread)
                except SpreadsheetNotFound:
                    raise SpreadsheetNotFound("Spreadsheet not found")
        self._refresh_sheets()

    def open_or_create_sheet(self, sheet):
        """
        DEPRECATED, use the `create` param for `open_sheet` instead

        Open a worksheet. If it doesn't exist, create it first.
        """
        _deprecate("open_or_create_sheet is deprecated, pass create=True to open_sheet")
        self.open_sheet(sheet, True)

    @_ensure_auth
    def open_sheet(self, sheet, create=False):
        """
        Open a worksheet. Optionally, if the sheet doesn't exist then create it first
        (only when ``sheet`` is a str).

        :param str,int sheet: name or index of Worksheet
        :param bool create: whether to create the sheet if it doesn't exist,
            see :meth:`create_sheet <gspread_pandas.Spread.create_sheet>` (default False)
        """
        self.sheet = None

        if isinstance(sheet, int):
            try:
                self.sheet = self.sheets[sheet]
            except:
                raise WorksheetNotFound("Invalid sheet index {0}".format(sheet))
        else:
            self.sheet = self.find_sheet(sheet)

        if not self.sheet:
            if create:
                self.create_sheet(sheet)
            else:
                raise WorksheetNotFound("Worksheet not found")

    @_ensure_auth
    def create_sheet(self, name, rows=1, cols=1):
        """
        Create a new worksheet with the given number of rows and cols.

        Automatically opens that sheet after it's created.

        :param str name: name of new Worksheet
        :param int rows: number of rows (default 1)
        :param int cols: number of columns (default 1)
        """
        self.spread.add_worksheet(name, rows, cols)
        self._refresh_sheets()
        self.open_sheet(name)

    def _parse_sheet_headers(self, vals, headers):
        col_names = None
        if headers:
            if headers > 1:
                col_names = pd.MultiIndex.from_arrays(vals[:headers])
            elif headers == 1:
                col_names = vals[0]
            vals = vals[headers:]
        return col_names

    def _parse_sheet_index(self, df, index):
        if index:
            df = df.set_index(df.columns[index - 1])
            # if it was multi-index, the name is tuple;
            # choose last value in tuple since that is more common
            if type(df.index.name) == tuple:
                df.index.name = df.index.name[-1]
            # get rid of falsey index names
            df.index.name = df.index.name or None
        return df

    @_ensure_auth
    def sheet_to_df(self, index=1, headers=1, start_row=1, sheet=None):
        """
        Pull a worksheet into a DataFrame.

        :param int index: col number of index column, 0 or None for no index (default 1)
        :param int headers: number of rows that represent headers (default 1)
        :param int start_row: row number for first row of headers or data (default 1)
        :param str,int sheet: optional, if you want to open a different sheet first,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)

        :returns: a DataFrame with the data from the Worksheet
        """
        if sheet:
            self.open_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        vals = self.sheet.get_all_values()[start_row - 1:]

        col_names = self._parse_sheet_headers(vals, headers)

        # remove rows where everything is null, then replace nulls with ''
        df = pd.DataFrame(vals[headers or 0:])\
               .replace('', np.nan)\
               .dropna(how='all')\
               .fillna('')

        if col_names is not None:
            df.columns = col_names

        return self._parse_sheet_index(df, index)

    def _parse_df_headers(self, df, include_index):
        headers = df.columns.tolist()

        # handle multi-index headers
        if type(headers[0]) == tuple:
            headers = [list(row) for row in zip(*headers)]

            # Pandas sets index name as top level col name with reset_index
            # Switch to low level since that is more natural
            if include_index:
                headers[-1][0] = headers[0][0]
                headers[0][0] = ''
        # handle regular columns
        else:
            headers = [headers]

        return headers

    @_ensure_auth
    def get_sheet_dims(self, sheet=None):
        """
        Get the dimensions of the currently open Worksheet.

        :param str,int sheet: optional, if you want to open a different sheet first,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)

        :returns: a tuple containing (num_rows,num_cols)
        """
        if sheet:
            self.open_sheet(sheet)

        return (self.sheet.row_count,
                self.sheet.col_count) if self.sheet else None

    def _get_range(self, start, end):
        """Transform start and end to cell range like A1:B5"""
        start_int = self._get_cell_as_tuple(start)
        end_int = self._get_cell_as_tuple(end)

        return "{0}:{1}".format(
            self.sheet.get_addr_int(*start_int),
            self.sheet.get_addr_int(*end_int)
        )

    def _get_cell_as_tuple(self, cell):
        """Take cell in either format, validate, and return as tuple"""
        if type(cell) == tuple:
            if len(cell) != 2 or type(cell[0]) != int or type(cell[1]) != int:
                raise TypeError("{0} is not a valid cell tuple".format(cell))
            return cell
        elif isinstance(cell, basestring):
            if not match('[a-zA-Z]+[0-9]+', cell):
                raise TypeError("{0} is not a valid address".format(cell))
            return self.sheet.get_int_addr(cell)
        else:
            raise TypeError("{0} is not a valid format".format(cell))

    def _get_update_chunks(self, start, end, vals):
        start = self._get_cell_as_tuple(start)
        end = self._get_cell_as_tuple(end)

        num_cols = end[COL] - start[COL] + 1
        num_rows = end[ROW] - start[ROW] + 1
        num_cells = num_cols * num_rows

        if num_cells != len(vals):
            raise Exception("Number of values needs to match number of cells")

        chunk_rows = self._max_range_chunk_size // num_cols
        chunk_size = chunk_rows * num_cols

        end_cell = (start[ROW] - 1, 0)

        for val_chunks in _chunks(vals, int(chunk_size)):
            start_cell = (end_cell[ROW] + 1, start[COL])
            end_cell = (min(start_cell[ROW] + chunk_rows - 1, start[ROW] + num_rows - 1), end[COL])
            yield start_cell, end_cell, val_chunks

    @_ensure_auth
    def update_cells(self, start, end, vals, sheet=None):
        """
        Update the values in a given range. The values should be listed in order
        from left to right across rows.

        :param tuple,str start: tuple indicating (row, col) or string like 'A1'
        :param tuple,str end: tuple indicating (row, col) or string like 'Z20'
        :param list vals: array of values to populate
        :param str,int sheet: optional, if you want to open a different sheet first,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)
        """
        if sheet:
            self.open_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        for start_cell, end_cell, val_chunks in self._get_update_chunks(start,
                                                                        end,
                                                                        vals):
            self.client.login()  # ensure that token is still active
            rng = self._get_range(start_cell, end_cell)

            cells = self.sheet.range(rng)

            if len(val_chunks) != len(cells):
                raise Exception("Number of chunked values doesn't match number of cells")

            for val, cell in zip(val_chunks, cells):
                cell.value = val

            for cells_chunk in _chunks(cells, self._max_update_chunk_size):
                self._retry_update(cells_chunk)

    def _retry_update(self, cells, n=3):
        try:
            self.client.login()  # ensure that token is still active
            self.sheet.update_cells(cells)
        except Exception as e:
            if n > 0:
                self._retry_update(cells, n-1)
            else:
                raise e

    def find_sheet(self, sheet):
        """
        Find a given worksheet by title.

        :param str sheet: name of Worksheet

        :returns: a Worksheet by the given name or None if not found
        """
        for worksheet in self.sheets:
            if sheet.lower() == worksheet.title.lower():
                return worksheet

    @_ensure_auth
    def clear_sheet(self, rows=1, cols=1, sheet=None):
        """
        Reset open worksheet to a blank sheet with given dimensions.

        :param int rows: number of rows (default 1)
        :param int cols: number of columns (default 1)
        :param str,int sheet: optional, name or index of Worksheet,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)
        """
        if sheet:
            self.open_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        self.sheet.resize(1, cols)

        self.update_cells(
            start=(1, 1),
            end=(1, cols),
            vals=['']
        )

        self.sheet.resize(rows, cols)

    @_ensure_auth
    def delete_sheet(self, sheet):
        """
        Delete a worksheet by title. Returns whether the sheet was deleted or not. If
        current sheet is deleted, the ``sheet`` property will be set to None.

        :param str sheet: name of Worksheet

        :returns: True if deleted successfully, else False
        """
        is_current = False

        s = self.find_sheet(sheet)

        if s == self.sheet:
            is_current = True

        if s:
            try:
                self.spread.del_worksheet(s)
                if is_current:
                    self.sheet = None
                return True
            except:
                pass
        return False

    @_ensure_auth
    def df_to_sheet(self, df, index=True, headers=True, start=(1,1), replace=False, sheet=None, start_row=1, start_col=1):
        """
        Save a DataFrame into a worksheet.

        :param DataFrame df: the DataFrame to save
        :param bool index: whether to include the index in worksheet (default True)
        :param bool headers: whether to include the headers in the worksheet (default True)
        :param tuple,str start: tuple indicating (row, col) or string like 'A1' for top left
            cell
        :param bool replace: whether to remove everything in the sheet first (default False)
        :param str,int sheet: optional, if you want to open or create a different sheet
            before saving,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)
        :param int start_row: (DEPRECATED - use `start`) row number for first row of headers or data (default 1)
        :param int start_col: (DEPRECATED - use `start`) column number for first column of headers or data (default 1)
        """
        if sheet:
            self.open_sheet(sheet, create=True)

        if not self.sheet:
            raise Exception("No open worksheet")

        if replace:
            self.clear_sheet()

        if index:
            df = df.reset_index()

        df_list = df.fillna('').values.tolist()

        if headers:
            headers = self._parse_df_headers(df, index)
            df_list = headers + df_list

        start = self._get_cell_as_tuple(start)

        # Check deprecated params.. will be removed in 1.0
        if start == (1, 1) and (start_row > 1 or start_col > 1):
            _deprecate("start_col and start_row params are deprecated, use start instead")
            start = (start_row, start_col)

        sheet_rows, sheet_cols = self.get_sheet_dims()
        req_rows = len(df_list) + (start[ROW] - 1)
        req_cols = len(df_list[0]) + (start[COL] - 1)

        # make sure sheet is large enough
        self.sheet.resize(max(sheet_rows, req_rows), max(sheet_cols, req_cols))

        self.update_cells(
            start=start,
            end=(req_rows, req_cols),
            vals=[val for row in df_list for val in row]
        )


def _chunks(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def _deprecate(message):
    import warnings
    warnings.warn(message, DeprecationWarning, stacklevel=2)
