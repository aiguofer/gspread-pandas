from re import match

import pandas as pd
from gspread.utils import a1_to_rowcol, rowcol_to_a1
from past.builtins import basestring


def parse_sheet_index(df, index):
    """Parse sheet index into df index"""
    if index and len(df.columns) >= index:
        df = df.set_index(df.columns[index - 1])
        # if it was multi-index, the name is tuple;
        # choose last value in tuple since that is more common
        if type(df.index.name) == tuple:
            df.index.name = df.index.name[-1]
        # get rid of falsey index names
        df.index.name = df.index.name or None
    return df


def parse_df_col_names(df, include_index, index_size=1):
    """Parse column names from a df into sheet headers"""
    headers = df.columns.tolist()

    # handle multi-index headers
    if len(headers) > 0 and type(headers[0]) == tuple:
        headers = [list(row) for row in zip(*headers)]

        # Pandas sets index name as top level col name when using reset_index
        # move the index name to lowest header level since that reads more natural
        if include_index:
            for i in range(index_size):
                headers[-1][i] = headers[0][i]
                headers[0][i] = ""
    # handle regular columns
    else:
        headers = [headers]

    return headers


def parse_sheet_headers(vals, header_rows):
    """Parse headers from a sheet into df columns"""
    col_names = None
    if header_rows:
        headers = vals[:header_rows]
        if len(headers) > 0:
            if header_rows > 1:
                _fix_sheet_header_level(headers)
                col_names = pd.MultiIndex.from_arrays(headers)
            elif header_rows == 1:
                col_names = pd.Index(headers[0])

    return col_names


def _fix_sheet_header_level(header_names):
    for col_ix in range(len(header_names[0])):
        _shift_header_up(header_names, col_ix)

    return header_names


def _shift_header_up(
    header_names, col_index, row_index=0, shift_val=0, found_first=False
):
    """Recursively shift headers up so that top level is not empty"""
    rows = len(header_names)
    if row_index < rows:
        current_value = header_names[row_index][col_index]

        if current_value == "" and not found_first:
            shift_val += 1
        else:
            found_first = True

        shift_val = _shift_header_up(
            header_names, col_index, row_index + 1, shift_val, found_first
        )
        if shift_val <= row_index:
            header_names[row_index - shift_val][col_index] = current_value

        if row_index + shift_val >= rows:
            header_names[row_index][col_index] = ""
    return shift_val


def chunks(lst, chunk_size):
    """Chunk a list into specified chunk sizes"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]


def deprecate(message):
    """Display message about deprecation"""
    import warnings

    warnings.warn(message, DeprecationWarning, stacklevel=2)


def create_filter_request(sheet_id, start_row, end_row, start_col, end_col):
    """
    Create v4 API request to create a filter for a given worksheet.
    """
    filterSettings = {
        "range": {
            "sheetId": sheet_id,
            "startRowIndex": start_row,
            "endRowIndex": end_row,
            "startColumnIndex": start_col,
            "endColumnIndex": end_col,
        }
    }
    return [{"setBasicFilter": {"filter": filterSettings}}]


def create_frozen_request(sheet_id, rows=None, cols=None):
    """
    Create v4 API request to freeze rows and/or columns for a
    given worksheet.
    """
    grid_properties = {}

    if rows >= 0:
        grid_properties["frozen_row_count"] = rows

    if cols >= 0:
        grid_properties["frozen_column_count"] = cols

    changed_props = grid_properties.keys()

    return [
        {
            "update_sheet_properties": {
                "properties": {
                    "sheet_id": sheet_id,
                    "grid_properties": grid_properties,
                },
                "fields": "grid_properties({0})".format(
                    ", ".join(changed_props)
                ),
            }
        }
    ]


def fillna(df, fill_value=""):
    """
    Replace null values with `fill_value`. Also replaces in categorical columns.
    """
    for col in df.dtypes[df.dtypes == "category"].index:
        if fill_value not in df[col].cat.categories:
            df[col].cat.add_categories([fill_value], inplace=True)
    return df.fillna(fill_value)


def get_cell_as_tuple(cell):
    """Take cell in either format, validate, and return as tuple"""
    if type(cell) == tuple:
        if len(cell) != 2 or type(cell[0]) != int or type(cell[1]) != int:
            raise TypeError("{0} is not a valid cell tuple".format(cell))
        return cell
    elif isinstance(cell, basestring):
        if not match("[a-zA-Z]+[0-9]+", cell):
            raise TypeError("{0} is not a valid address".format(cell))
        return a1_to_rowcol(cell)
    else:
        raise TypeError("{0} is not a valid format".format(cell))


def get_range(start, end):
    """Transform start and end to cell range like A1:B5"""
    start_int = get_cell_as_tuple(start)
    end_int = get_cell_as_tuple(end)

    return "{0}:{1}".format(rowcol_to_a1(*start_int), rowcol_to_a1(*end_int))
