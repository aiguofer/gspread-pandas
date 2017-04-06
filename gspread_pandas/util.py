import pandas as pd

def _parse_sheet_index(df, index):
    """Parse sheet index into df index"""
    if index:
        df = df.set_index(df.columns[index - 1])
        # if it was multi-index, the name is tuple;
        # choose last value in tuple since that is more common
        if type(df.index.name) == tuple:
            df.index.name = df.index.name[-1]
        # get rid of falsey index names
        df.index.name = df.index.name or None
    return df

def _parse_df_headers(df, include_index):
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

def _parse_sheet_headers(vals, header_rows):
    """Parse headers from a sheet into df columns"""
    col_names = None
    if header_rows:
        headers = vals[:header_rows]
        if header_rows > 1:
            col_names = pd.MultiIndex.from_arrays(headers)
        elif header_rows == 1:
            col_names = headers

    return col_names

def _chunks(lst, chunk_size):
    """Chunk a list into specified chunk sizes"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def _deprecate(message):
    """Display message about deprecation"""
    import warnings
    warnings.warn(message, DeprecationWarning, stacklevel=2)
