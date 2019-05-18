import warnings
from re import match
from time import sleep

import numpy as np
import pandas as pd
from gspread.client import Client as ClientV4
from gspread.exceptions import APIError
from gspread.utils import a1_to_rowcol, rowcol_to_a1
from past.builtins import basestring

ROW = START = 0
COL = END = 1
DEPRECATION_WARNINGS_ENABLED = True
_WARNINGS_ALREADY_ENABLED = False


def parse_sheet_index(df, index):
    """Parse sheet index into df index"""
    if index and len(df.columns) >= index:
        df = df.set_index(df.columns[index - 1])
        # if column was MultiIndex, the name is a tuple;
        # choose last non-empty value in tuple
        # since that is more common
        if type(df.index.name) == tuple:
            df.index.name = [x for x in df.index.name if x][-1]
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
                # Pandas sets the index's column name as "index" if it doesn't have a
                # name so we need to clean that up
                headers[-1][i] = headers[0][i] if headers[0][i] != "index" else ""
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
    global DEPRECATION_WARNINGS_ENABLED, _WARNINGS_ALREADY_ENABLED
    # force enable DeprecationWarnings since most interactive shells have
    # them disabled
    if DEPRECATION_WARNINGS_ENABLED and not _WARNINGS_ALREADY_ENABLED:
        _WARNINGS_ALREADY_ENABLED = True
        warnings.filterwarnings(
            "default", ".*", category=DeprecationWarning, module="gspread_pandas"
        )
    # provide ability to disable them at runtime
    if _WARNINGS_ALREADY_ENABLED and not DEPRECATION_WARNINGS_ENABLED:
        warnings.filterwarnings(
            "ignore", ".*", category=DeprecationWarning, module="gspread_pandas"
        )

    warnings.warn(message, DeprecationWarning, stacklevel=2)


def create_filter_request(sheet_id, start, end):
    """
    Create v4 API request to create a filter for a given worksheet.
    """
    start = get_cell_as_tuple(start)
    end = get_cell_as_tuple(end)

    return {
        "setBasicFilter": {
            "filter": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start[ROW],
                    "endRowIndex": end[ROW],
                    "startColumnIndex": start[COL],
                    "endColumnIndex": end[COL],
                }
            }
        }
    }


def create_frozen_request(sheet_id, rows=None, cols=None):
    """
    Create v4 API request to freeze rows and/or columns for a
    given worksheet.
    """
    grid_properties = {}

    if rows is not None and rows >= 0:
        grid_properties["frozen_row_count"] = rows

    if cols is not None and cols >= 0:
        grid_properties["frozen_column_count"] = cols

    changed_props = grid_properties.keys()

    return {
        "update_sheet_properties": {
            "properties": {"sheet_id": sheet_id, "grid_properties": grid_properties},
            "fields": "grid_properties({0})".format(", ".join(changed_props)),
        }
    }


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
        if (
            len(cell) != 2
            or not np.issubdtype(type(cell[ROW]), np.integer)
            or not np.issubdtype(type(cell[COL]), np.integer)
        ):
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


def create_merge_cells_request(sheet_id, start, end, merge_type="MERGE_ALL"):
    """
    Create v4 API request to merge rows and/or columns for a
    given worksheet.
    """
    start = get_cell_as_tuple(start)
    end = get_cell_as_tuple(end)

    return {
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start[ROW] - 1,
                "endRowIndex": end[ROW],
                "startColumnIndex": start[COL] - 1,
                "endColumnIndex": end[COL],
            },
            "mergeType": merge_type,
        }
    }


def create_unmerge_cells_request(sheet_id, start, end):
    """
    Create v4 API request to unmerge rows and/or columns for a
    given worksheet.
    """
    start = get_cell_as_tuple(start)
    end = get_cell_as_tuple(end)

    return {
        "unmergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start[ROW] - 1,
                "endRowIndex": end[ROW],
                "startColumnIndex": start[COL] - 1,
                "endColumnIndex": end[COL],
            }
        }
    }


def monkey_patch_request(client, retry_delay=10):
    """Monkey patch gspread's Client.request to auto-retry with a delay when you get a
    100s RESOURCE_EXCHAUSTED error.
    """

    def request(*args, **kwargs):
        try:
            return ClientV4.request(client, *args, **kwargs)
        except APIError as e:
            error = str(e)
            # Only retry on 100s quota breaches
            if "RESOURCE_EXHAUSTED" in error and "100s" in error:
                sleep(retry_delay)
                return request(*args, **kwargs)
            else:
                error = e

        if "error" in locals():
            raise error

    client.request = request


def create_merge_headers_request(sheet_id, headers, start, index_size):
    """
    Create v4 API request to merge labels for a given worksheet.
    """
    request = []
    start = get_cell_as_tuple(start)

    if isinstance(headers, pd.MultiIndex):
        merge_cells = get_col_merge_ranges(headers)
        request.append(
            [
                create_merge_cells_request(
                    sheet_id,
                    (start[ROW] + row_ix, col_rng[START] + start[COL] + index_size),
                    (start[ROW] + row_ix, col_rng[END] + start[COL] + index_size),
                )
                for row_ix, row in enumerate(merge_cells)
                for col_rng in row
            ]
        )

    return request


def get_col_merge_ranges(index):
    """Get list of ranges to be merged for each level of columns. For each level,
    same values will only be merged if they share the same label for the level above.
    """
    labels = index.codes if hasattr(index, "codes") else index.labels
    # Dummy range indicating the full size, this is removed at the end
    ranges = [[(0, len(labels[0]))]]

    for ix, index_level in enumerate(labels[:]):
        index_ranges = []
        for rng in ranges[ix]:
            index_ranges.extend(
                get_contiguous_ranges(index_level, rng[START], rng[END])
            )
        ranges.append(index_ranges)

    ranges.pop(0)
    return ranges


def get_contiguous_ranges(lst, lst_start, lst_end):
    """Get list of tuples, each indicating the range of contiguous equal values in the lst
    between lst_start and lst_end. Everything is 0 indexed.

    For example, get_contiguous_ranges([0, 0, 0, 1, 1], 1, 4) = [(1, 2), (3, 4)]
    [(the 2nd and 3rd items are both 0), (the 4th and 5th items are both 1)]
    """
    prev_val = None
    index_ranges = []
    lst_section = lst[lst_start : lst_end + 1]
    rng_start = lst_section[START]

    for ix, val in enumerate(lst_section):
        # If there's more than 1 value in the range and there's a change in val
        if rng_start < ix - 1 and prev_val != val:
            # Save the rng until the previous val
            index_ranges.append((lst_start + rng_start, lst_start + ix - 1))
        # If this is the last val and the val is still the same
        elif ix == len(lst_section) - 1 and prev_val == val:
            # Save the rng including the last val
            index_ranges.append((lst_start + rng_start, lst_start + ix))

        if prev_val != val:
            rng_start = ix

        prev_val = val
    return index_ranges
