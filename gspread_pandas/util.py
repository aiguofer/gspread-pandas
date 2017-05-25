import pandas as pd

def parse_sheet_index(df, index):
    """Parse sheet index into df index"""
    if index and len(df.columns) > index:
        df = df.set_index(df.columns[index - 1])
        # if it was multi-index, the name is tuple;
        # choose last value in tuple since that is more common
        if type(df.index.name) == tuple:
            df.index.name = df.index.name[-1]
        # get rid of falsey index names
        df.index.name = df.index.name or None
    return df

def parse_df_col_names(df, include_index):
    """Parse column names from a df into sheet headers"""
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

def parse_sheet_headers(vals, header_rows):
    """Parse headers from a sheet into df columns"""
    col_names = None
    if header_rows:
        headers = vals[:header_rows]
        if header_rows > 1:
            _fix_sheet_header_level(headers)
            col_names = pd.MultiIndex.from_arrays(headers)
        elif header_rows == 1:
            col_names = headers

    return col_names

def _fix_sheet_header_level(header_names):
    for col_ix in range(len(header_names[0])):
        _shift_header_up(header_names, col_ix)

    return header_names

def _shift_header_up(header_names, col_index, row_index=0,
                     shift_val=0, found_first=False):
    """Recursively shift headers up so that top level is not empty"""
    rows = len(header_names)
    if row_index < rows:
        current_value = header_names[row_index][col_index]

        if current_value == '' and not found_first:
            shift_val += 1
        else:
            found_first = True

        shift_val = _shift_header_up(header_names, col_index, row_index + 1,
                                     shift_val, found_first)
        if shift_val <= row_index:
            header_names[row_index - shift_val][col_index] = current_value

        if row_index + shift_val >= rows:
            header_names[row_index][col_index] = ''
    return shift_val

def chunks(lst, chunk_size):
    """Chunk a list into specified chunk sizes"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def deprecate(message):
    """Display message about deprecation"""
    import warnings
    warnings.warn(message, DeprecationWarning, stacklevel=2)

def create_frozen_request(sheet_id, rows=None, cols=None):
    """
    Create v4 API request to freeze rows and/or columns for a
    given worksheet.
    """
    grid_properties = {}

    if rows >= 0:
        grid_properties['frozen_row_count'] = rows

    if cols >= 0:
        grid_properties['frozen_column_count'] = cols

    changed_props = grid_properties.keys()

    return {
        'update_sheet_properties': {
            'properties': {
                'sheet_id': sheet_id,
                'grid_properties': grid_properties
            },
            'fields': 'grid_properties({0})'.format(', '.join(changed_props))
        }
    }
