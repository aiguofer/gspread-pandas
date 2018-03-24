from __future__ import print_function

from re import match
from os import path

from builtins import str, range
from past.builtins import basestring

import numpy as np
import pandas as pd
import gspread

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.tools import run_flow, argparser

from decorator import decorator
import gspread
from gspread.models import Worksheet
from gspread.utils import rowcol_to_a1, a1_to_rowcol
from gspread.exceptions import (SpreadsheetNotFound, WorksheetNotFound,
                                NoValidUrlKeyFound, RequestError)
from gspread.v4.exceptions import APIError
from gspread_pandas.conf import get_config
from gspread_pandas.util import (chunks, parse_df_col_names,
                                 parse_sheet_index, parse_sheet_headers,
                                 create_frozen_request, fillna)


__all__ = ['Spread']

default_scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.email'
]

ROW = 0
COL = 1

def list_spreadsheet_files_patched(self):
    files = []
    page_token = ''
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        'q': "mimeType='application/vnd.google-apps.spreadsheet'",
        "pageSize": 1000
    }

    while page_token is not None:
        if page_token:
            params['pageToken'] = page_token

        res = self.request('get', url, params=params).json()
        files.extend(res['files'])
        page_token = res.get('nextPageToken', None)

    return files


gspread.v4.client.Client.list_spreadsheet_files = list_spreadsheet_files_patched


class Spread():
    """
    Simple wrapper for gspread to interact with Pandas. It holds an instance of
    an 'open' spreadsheet, an 'open' worksheet, and a list of available worksheets.

    Each user will be associated with specific OAuth credentials. The authenticated user
    will need the appropriate permissions to the Spreadsheet in order to interact with it.
    """
    #: `(gspread.models.Spreadsheet)` - Currently open Spreadsheet
    spread = None

    #: `(gspread.models.Worksheet)` - Currently open Worksheet
    sheet = None

    #: `(str)` - E-mail for the currently authenticated user
    email = ''

    #: `(gspread.client.Client)` - Current gspread Client
    client = None

    # chunk range request: https://github.com/burnash/gspread/issues/375
    _max_range_chunk_size = 1000000

    def __init__(self, user, spread, sheet=None, config=None,
                 create_spread=False, create_sheet=False):
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
        :param bool create_sheet: whether to create the spreadsheet if it doesn't exist,
            it wil use the ``spread`` value as the sheet title
        :param bool create_spread: whether to create the sheet if it doesn't exist,
            it wil use the ``spread`` value as the sheet title
        """
        self._config = config or get_config()
        self._creds_file = path.join(self._config['creds_dir'], user)
        self._login()
        self.email = self._get_email()

        self.open(spread, sheet, create_sheet, create_spread)

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

    @property
    def url(self):
        """`(str)` - Url for this spreadsheet"""
        return 'https://docs.google.com/spreadsheets/d/{0}'.format(self.spread.id)

    @property
    def sheets(self):
        """`(list)` - List of available Worksheets"""
        return self.spread.worksheets()

    @property
    def _spread_metadata(self):
        """`(dict)` - Spreadsheet metadata"""
        return self.spread.fetch_sheet_metadata()

    @property
    def _sheet_metadata(self):
        """`(dict)` - Metadata for currently open worksheet"""
        if self.sheet:
            ix = self._find_sheet(self.sheet.title)[0]
            return self._spread_metadata['sheets'][ix]

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
        except Exception:
            print("""
            Couldn't retrieve email. Delete {0} and authenticate again
            """.format(self._creds_file))

    def _authorize(self):
        if all(key in self._config for key in ('client_id',
                                               'client_secret',
                                               'redirect_uris')):
            flow = OAuth2WebServerFlow(
                client_id=self._config['client_id'],
                client_secret=self._config['client_secret'],
                redirect_uri=self._config['redirect_uris'][0],
                scope=default_scope)

            storage = Storage(self._creds_file)
            args = argparser.parse_args(args=['--noauth_local_webserver'])

            return run_flow(flow, storage, args)

        if 'private_key_id' in self._config:
            return ServiceAccountCredentials.from_json_keyfile_dict(self._config,
                                                                    default_scope)

        raise Exception("Unknown config file format")

    def _login(self):
        creds = None

        if path.exists(self._creds_file):
            creds = Storage(self._creds_file).locked_get()
        else:
            creds = self._authorize()

        self.client = gspread.authorize(creds)

    def open(self, spread, sheet=None, create_sheet=False, create_spread=False):
        """
        Open a spreadsheet, and optionally a worksheet. See
        :meth:`open_spread <gspread_pandas.Spread.open_spread>` and
        :meth:`open_sheet <gspread_pandas.Spread.open_sheet>`.

        :param str spread: name, url, or id of Spreadsheet
        :param str,int sheet: name or index of Worksheet
        :param bool create_sheet: whether to create the spreadsheet if it doesn't exist,
            it wil use the ``spread`` value as the sheet title
        :param bool create_spread: whether to create the sheet if it doesn't exist,
            it wil use the ``spread`` value as the sheet title
        """
        self.open_spread(spread, create_spread)

        if sheet is not None:
            self.open_sheet(sheet, create_sheet)

    @_ensure_auth
    def open_spread(self, spread, create=False):
        """
        Open a spreadsheet. Authorized user must already have read access.

        :param str spread: name, url, or id of Spreadsheet
        :param bool create: whether to create the spreadsheet if it doesn't exist,
            it wil use the ``spread`` value as the sheet title
        """
        self.spread = None

        try:
            self.spread = self.client.open(spread)
        except SpreadsheetNotFound:
            try:
                self.spread = self.client.open_by_url(spread)
                self.spread.fetch_sheet_metadata()
            except (SpreadsheetNotFound, NoValidUrlKeyFound, APIError):
                try:
                    self.spread = self.client.open_by_key(spread)
                    self.spread.fetch_sheet_metadata()
                except (SpreadsheetNotFound, APIError):
                    if create:
                        try:
                            self.spread = self.client.create(spread)
                        except RequestError as e:
                            err = str(e)
                            msg = "Couldn't create spreadsheet.\n"
                            if 'accessNotConfigured' in err:
                                msg += "Drive API has not been enabled. Enable it at " +\
                                       "https://console.developers.google.com/apis/api/drive/overview"
                            elif 'insufficientPermissions' in err:
                                msg += "Delete {0} and authenticate again"\
                                       .format(self._creds_file)
                            else:
                                msg += err
                            raise Exception(msg)
                    else:
                        raise SpreadsheetNotFound("Spreadsheet not found")

    @_ensure_auth
    def open_sheet(self, sheet, create=False):
        """
        Open a worksheet. Optionally, if the sheet doesn't exist then create it first
        (only when ``sheet`` is a str).

        :param str,int,Worksheet sheet: name, index, or Worksheet object
        :param bool create: whether to create the sheet if it doesn't exist,
            see :meth:`create_sheet <gspread_pandas.Spread.create_sheet>` (default False)
        """
        self.sheet = None
        if isinstance(sheet, int):
            try:
                self.sheet = self.sheets[sheet]
            except Exception:
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
        self.open_sheet(name)

    @_ensure_auth
    def sheet_to_df(self, index=1, header_rows=1, start_row=1, sheet=None):
        """
        Pull a worksheet into a DataFrame.

        :param int index: col number of index column, 0 or None for no index (default 1)
        :param int header_rows: number of rows that represent headers (default 1)
        :param int start_row: row number for first row of headers or data (default 1)
        :param str,int sheet: optional, if you want to open a different sheet first,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)

        :returns: a DataFrame with the data from the Worksheet
        """
        if sheet:
            self.open_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        vals = self._retry_get_all_values()
        vals = self._fix_merge_values(vals)[start_row - 1:]

        col_names = parse_sheet_headers(vals, header_rows)

        # remove rows where everything is null, then replace nulls with ''
        df = pd.DataFrame(vals[header_rows or 0:])\
               .replace('', np.nan)\
               .dropna(how='all')\
               .fillna('')

        if col_names is not None:
            if len(df.columns) == len(col_names):
                df.columns = col_names
            elif len(df) == 0:
                # if we have headers but no data, set column headers on empty DF
                df = df.reindex(columns=col_names)
            else:
                raise Exception("Column headers don't match number of data columns")

        return parse_sheet_index(df, index)

    @_ensure_auth
    def get_sheet_dims(self, sheet=None):
        """
        Get the dimensions of the currently open Worksheet.

        :param str,int,Worksheet sheet: optional, if you want to open a different sheet first,
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
            rowcol_to_a1(*start_int),
            rowcol_to_a1(*end_int)
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
            return a1_to_rowcol(cell)
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

        for val_chunks in chunks(vals, int(chunk_size)):
            start_cell = (end_cell[ROW] + 1,
                          start[COL])
            end_cell = (min(start_cell[ROW] + chunk_rows - 1,
                            start[ROW] + num_rows - 1),
                        end[COL])
            yield start_cell, end_cell, val_chunks

    @_ensure_auth
    def update_cells(self, start, end, vals, sheet=None):
        """
        Update the values in a given range. The values should be listed in order
        from left to right across rows.

        :param tuple,str start: tuple indicating (row, col) or string like 'A1'
        :param tuple,str end: tuple indicating (row, col) or string like 'Z20'
        :param list vals: array of values to populate
        :param str,int,Worksheet sheet: optional, if you want to open a different sheet first,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)
        """
        if sheet:
            self.open_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        if start == end:
            return

        for start_cell, end_cell, val_chunks in self._get_update_chunks(start,
                                                                        end,
                                                                        vals):
            rng = self._get_range(start_cell, end_cell)

            cells = self._retry_range(rng)

            if len(val_chunks) != len(cells):
                raise Exception("Number of chunked values doesn't match number of cells")

            for val, cell in zip(val_chunks, cells):
                cell.value = val

            self._retry_update(cells)

    @_ensure_auth
    def _retry_get_all_values(self, n=3):
        """Call self.sheet.update_cells with retry"""
        try:
            return self.sheet.get_all_values()
        except Exception as e:
            if n > 0:
                self._retry_get_all_values(n-1)
            else:
                raise e

    @_ensure_auth
    def _retry_update(self, cells, n=3):
        """Call self.sheet.update_cells with retry"""
        try:
            self.sheet.update_cells(cells)
        except Exception as e:
            if n > 0:
                self._retry_update(cells, n-1)
            else:
                raise e

    @_ensure_auth
    def _retry_range(self, rng, n=3):
        """Call self.sheet.range with retry"""
        try:
            return self.sheet.range(rng)
        except Exception as e:
            if n > 0:
                self._retry_range(rng, n-1)
            else:
                raise e

    def _find_sheet(self, sheet):
        """Find a worksheet and return with index"""
        for ix, worksheet in enumerate(self.sheets):
            if isinstance(sheet, basestring) and sheet.lower() == worksheet.title.lower():
                return ix, worksheet
            if isinstance(sheet, Worksheet) and sheet == worksheet:
                return ix, worksheet
        return None, None

    def find_sheet(self, sheet):
        """
        Find a given worksheet by title

        :param str sheet: name of Worksheet

        :returns: a Worksheet by the given name or None if not found
        """
        return self._find_sheet(sheet)[1]

    @_ensure_auth
    def clear_sheet(self, rows=1, cols=1, sheet=None):
        """
        Reset open worksheet to a blank sheet with given dimensions.

        :param int rows: number of rows (default 1)
        :param int cols: number of columns (default 1)
        :param str,int,Worksheet sheet: optional; name, index, or Worksheet,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)
        """
        if sheet:
            self.open_sheet(sheet)

        if not self.sheet:
            raise Exception("No open worksheet")

        frozen_rows = self._sheet_metadata['properties']['gridProperties']\
                          .get('frozenRowCount', 0)

        frozen_cols = self._sheet_metadata['properties']['gridProperties']\
                          .get('frozenColCount', 0)

        clear_rows = frozen_rows + 1
        clear_cols = max(frozen_cols, cols)

        self.sheet.resize(clear_rows, clear_cols)

        self.update_cells(
            start=(1, 1),
            end=(clear_rows, clear_cols),
            vals=['' for i in range(0, clear_rows * clear_cols)]
        )

        self.sheet.resize(max(clear_rows, rows), clear_cols)

    @_ensure_auth
    def delete_sheet(self, sheet):
        """
        Delete a worksheet by title. Returns whether the sheet was deleted or not. If
        current sheet is deleted, the ``sheet`` property will be set to None.

        :param str,Worksheet sheet: name or Worksheet

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
            except Exception:
                pass
        return False

    @_ensure_auth
    def df_to_sheet(self, df, index=True, headers=True, start=(1,1), replace=False,
                    sheet=None, freeze_index=False, freeze_headers=False, fill_value=''):
        """
        Save a DataFrame into a worksheet.

        :param DataFrame df: the DataFrame to save
        :param bool index: whether to include the index in worksheet (default True)
        :param bool headers: whether to include the headers in the worksheet (default True)
        :param tuple,str start: tuple indicating (row, col) or string like 'A1' for top left
            cell
        :param bool replace: whether to remove everything in the sheet first (default False)
        :param str,int,Worksheet sheet: optional, if you want to open or create a different sheet
            before saving,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)
        :param bool freeze_index: whether to freeze the index columns (default False)
        :param bool freeze_headers: whether to freeze the header rows (default False)
        :param str fill_value: value to fill nulls with (default '')
        """
        if sheet:
            self.open_sheet(sheet, create=True)

        if not self.sheet:
            raise Exception("No open worksheet")

        index_size = df.index.nlevels
        header_size = df.columns.nlevels

        if index:
            df = df.reset_index()

        df = fillna(df, fill_value)
        df_list = df.values.tolist()

        if headers:
            header_rows = parse_df_col_names(df, index)
            df_list = header_rows + df_list

        start = self._get_cell_as_tuple(start)

        sheet_rows, sheet_cols = self.get_sheet_dims()
        req_rows = len(df_list) + (start[ROW] - 1)
        req_cols = len(df_list[0]) + (start[COL] - 1) or 1

        if replace:
            # this takes care of resizing
            self.clear_sheet(req_rows, req_cols)
        else:
            # make sure sheet is large enough
            self.sheet.resize(max(sheet_rows, req_rows), max(sheet_cols, req_cols))

        self.update_cells(
            start=start,
            end=(req_rows, req_cols),
            vals=[val for row in df_list for val in row]
        )

        self.freeze(None if not freeze_headers else header_size,
                    None if not freeze_index else index_size)

    def _fix_merge_values(self, vals):
        """Assign the top-left value to all cells in a merged range"""
        for merge in self._sheet_metadata.get('merges', []):
            start_row, end_row = merge['startRowIndex'], merge['endRowIndex']
            start_col, end_col = merge['startColumnIndex'], merge['endColumnIndex']

            # ignore merge cells outside the data range
            if start_row < len(vals) and start_col < len(vals[0]):
                orig_val = vals[start_row][start_col]
                for row in vals[start_row:end_row]:
                    row[start_col:end_col] = [orig_val for i in
                                              range(start_col, end_col)]

        return vals

    @_ensure_auth
    def freeze(self, rows=None, cols=None, sheet=None):
        """
        Freeze rows and/or columns for the open worksheet.

        :param int rows: the DataFrame to save
        :param int cols: whether to include the index in worksheet (default True)
        :param str,int,Worksheet sheet: optional, if you want to open or create a different sheet
            before freezing,
            see :meth:`open_sheet <gspread_pandas.client.Spread.open_sheet>` (default None)
        """
        if sheet:
            self.open_sheet(sheet, create=True)

        if not self.sheet:
            raise Exception("No open worksheet")

        if rows is None and cols is None:
            return

        self.client.bath_update({
            'requests': [create_frozen_request(self.sheet.id, rows, cols)]
        })
