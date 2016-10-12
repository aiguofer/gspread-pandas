from os import path

import numpy as np
import pandas as pd
import gspread

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser

from conf import get_config

_default_scope = [
    'https://docs.google.com/feeds', 'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


class Spread():
    """
    Simple wrapper for gspread to interact with Pandas. It holds an instance of
    an 'open' spreadsheet, an 'open' worksheet, and a list of available worksheets.

    It each user will be associated with specific OAuth credentials. The user will
    need respective access to the Spreadsheet.
    """

    def __init__(self, user, spread, sheet=None, config=None):
        self._config = config or get_config()
        self._creds_file = path.join(self._config['creds_dir'], user)
        self._login()
        self.spread = None
        self.sheet = None
        self.open(spread, sheet)

    def _authorize(self):
        flow = OAuth2WebServerFlow(
            client_id=self._config['client_id'],
            client_config=self._config['client_config'],
            redirect_uri=self._config['redirect_uris'][0],
            scope=_default_scope)

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

    def _refresh_sheets(self):
        if self.spread:
            self.sheets = self.spread.worksheets()

    def open(self, spread=None, sheet=None):
        """
        Open a spreadsheet and optionally a worksheet
        """
        self.open_spread(spread)

        if sheet:
            self.open_sheet(sheet)

    def open_spread(self, spread):
        """
        Open a spreadsheet. It can take in a name, url, or id
        """
        self.spread = None

        try:
            self.spread = self.client.open(spread)
        except:
            try:
                self.spread = self.client.open_by_url(spread)
            except:
                try:
                    self.spread = self.client.open_by_key(spread)
                except:
                    raise Exception("Spreadsheet not found")
        self._refresh_sheets()

    def open_sheet(self, sheet):
        """
        Open a worksheet. It can take in a name or integer index (0 indexed)
        """
        self.sheet = None

        if isinstance(sheet, int):
            try:
                self.sheet = self.sheets[sheet]
            except:
                pass
        else:
            self.sheet = self.find_sheet(sheet)

        if not self.sheet:
            raise Exception("Worksheet not found")

    def create_sheet(self, name, rows=1, cols=1):
        """
        Create a new worksheet with the given number of rows and cols.

        Automatically opens that sheet after it's created.
        """
        self.spread.add_worksheet(name, rows, cols)
        self._refresh_sheets()
        self.open_sheet(name)

    def open_or_create_sheet(self, sheet):
        """
        Open a worksheet. If it doesn't exist, create it first.
        """
        try:
            self.open_sheet(sheet)
        except:
            self.create_sheet(sheet)

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

    def sheet_to_df(self, index=None, headers=None, start_row=1, sheet=None):
        """
        Convert a worksheet into a DataFrame

        Args:
        index -- col number of index (default None)
        headers -- number of rows that represent headers (default None)
        start_row -- row number for first row of headers or data (default 1)
        sheet -- in case you want to open a different sheet first (default None)
        """
        if sheet:
            self.open_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        vals = self.sheet.get_all_values()[start_row - 1:]

        col_names = self._parse_sheet_headers(vals, headers)

        df = pd.DataFrame(vals[headers or 0:]).replace('', np.nan).dropna(
            how='all').fillna('')

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

    def get_sheet_dims(self, sheet=None):
        """
        Get the dimensions of a worksheet
        """
        if sheet:
            self.open_sheet(sheet)

        return (self.sheet.row_count,
                self.sheet.col_count) if self.sheet else None

    def _get_range(self, start, end):
        return "{0}:{1}".format(
            self.sheet.get_addr_int(*start), self.sheet.get_addr_int(*end))

    def update_cells(self, start, end, vals, sheet=None):
        """
        Update the values in a given range. The values should be listed in order
        from left to right across rows.

        Args:
        start -- tuple indicating (row, col) or string like 'A1'
        end -- tuple indicating (row, col) or string like 'Z20'
        vals -- array of values to populate
        sheet -- in case you want to open a different sheet first (default None)
        """
        if sheet:
            self.open_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        if type(start) == tuple and type(end) == tuple:
            rng = self._get_range(start, end)
        elif isinstance(start, basestring) and isinstance(end, basestring):
            rng = start + ":" + end
        else:
            raise TypeError("Start and end need to be tuple or string")

        cells = self.sheet.range(rng)

        for val, cell in zip(vals, cells):
            cell.value = val

        # https://github.com/burnash/gspread/issues/384
        # and https://github.com/burnash/gspread/issues/375
        for cells_chunk in _chunks(cells, 40000):
            self.sheet.update_cells(cells_chunk)

    def find_sheet(self, sheet):
        """
        Find a given worksheet by title, return None if not found.
        """
        for worksheet in self.sheets:
            if sheet == worksheet.title:
                return worksheet

    def clear_sheet(self, sheet):
        """
        Remove a worksheet by title then re-create it
        """
        if self.delete_sheet(sheet):
            self.create_sheet(sheet)

    def delete_sheet(self, sheet):
        """
        Delete a worksheet by title. Returns whether the sheet was deleted or not
        """
        s = self.find_sheet(sheet)
        if s:
            try:
                self.spread.del_worksheet(s)
                return True
            except:
                pass
        return False

    def df_to_sheet(self, df, index=True, headers=True, start_row=1,
                    start_col=1, replace=False, sheet=None):
        """
        Convert a DataFrame into a worksheet

        Args:
        df - a DataFrame
        index -- whether to include the index in worksheet (default True)
        headers -- whether to include the headers in the worksheet (default True)
        start_row -- row number for first row of headers or data (default 1)
        start_col -- column number for first column of headers or data (default 1)
        replace -- whether to remove everything in the sheet first (default False)
        sheet -- in case you want to open a different sheet first (default None)
        """
        if sheet:
            if replace:
                self.clear_sheet(sheet)
            self.open_or_create_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        if index:
            df = df.reset_index()

        df_list = df.fillna('').values.tolist()

        if headers:
            headers = self._parse_df_headers(df, index)
            df_list = headers + df_list

        sheet_rows, sheet_cols = self.get_sheet_dims()
        req_rows = len(df_list) + (start_row - 1)
        req_cols = len(df_list[0]) + (start_col - 1)

        # make sure sheet is large enough
        self.sheet.resize(max(sheet_rows, req_rows), max(sheet_cols, req_cols))

        args = {
            'start': (start_row, start_col),
            'end': (req_rows, req_cols),
            'vals': [val for row in df_list for val in row]
        }

        self.update_cells(**args)


def _chunks(lst, chunk_size):
    for i in xrange(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]
