import pytest
import pandas as pd
import numpy as np

from gspread_pandas import util

@pytest.fixture
def df():
    data = [[1, 2],
            [3, 4]]
    cols = ['col1', 'col2']
    df = pd.DataFrame(data, columns=cols)
    df.index.name = 'test_index'
    return df

@pytest.fixture
def df_empty():
    return pd.DataFrame()

@pytest.fixture
def df_multiheader():
    data = [[1, 2],
            [3, 4]]
    cols = pd.MultiIndex.from_tuples([('col1', 'subcol1'), ('col1', 'subcol2')])
    return pd.DataFrame(data, columns=cols)

@pytest.fixture
def df_multiheader_w_index():
    data = [[1, 2],
            [3, 4]]
    cols = pd.MultiIndex.from_tuples([('col1', 'subcol1'), ('col1', 'subcol2')])
    df = pd.DataFrame(data, columns=cols)
    df.index.name = 'test_index'
    return df.reset_index()

@pytest.fixture
def df_multiheader_w_multiindex():
    data = [[1, 2],
            [3, 4]]
    cols = pd.MultiIndex.from_tuples([('col1', 'subcol1'), ('col1', 'subcol2')])
    ix = pd.MultiIndex.from_tuples([('row1', 'subrow1'), ('row1', 'subrow2')],
                                   names=['l1', 'l2'])
    df = pd.DataFrame(data, columns=cols, index=ix)
    return df.reset_index()

@pytest.fixture
def data_multiheader():
    data = [['', 'col1', 'col1'],
            ['test_index', 'subcol1', 'subcol2'],
            [1, 2, 3],
            [4, 5, 6]]
    return data

@pytest.fixture
def data_empty():
    return [[]]


def test_parse_sheet_index(df):
    assert util.parse_sheet_index(df, 1).index.name == 'col1'

def test_parse_sheet_index_noop(df):
    assert util.parse_sheet_index(df, 0).index.name == 'test_index'

def test_parse_sheet_index_multiheader(df_multiheader):
    """In a multi-header situation, it should use the lower heading as the index name"""
    assert util.parse_sheet_index(df_multiheader, 1).index.name == 'subcol1'

def test_parse_sheet_index_multiheader2(df_multiheader):
    """In a multi-header situation, it should use the lower heading as the index name"""
    assert util.parse_sheet_index(df_multiheader, 2).index.name == 'subcol2'


def test_parse_df_col_names_empty_no_index(df_empty):
    assert util.parse_df_col_names(df_empty, False) == [[]]

def test_parse_df_col_names_normal_no_index(df):
    assert util.parse_df_col_names(df, False) == [['col1', 'col2']]

def test_parse_df_col_names_multiheader_no_index(df_multiheader):
    expected = [['col1', 'col1'],
                ['subcol1', 'subcol2']]
    assert util.parse_df_col_names(df_multiheader, False) == expected

def test_parse_df_col_names_multiheader_w_index(df_multiheader_w_index):
    expected = [['', 'col1', 'col1'],
                ['test_index', 'subcol1', 'subcol2']]
    assert util.parse_df_col_names(df_multiheader_w_index, True) == expected

def test_parse_df_col_names_multiheader_w_multiindex(df_multiheader_w_multiindex):
    expected = [['', '', 'col1', 'col1'],
                ['l1', 'l2', 'subcol1', 'subcol2']]
    assert util.parse_df_col_names(df_multiheader_w_multiindex, True, 2) == expected


def test_parse_sheet_headers_empty(data_empty):
    assert util.parse_sheet_headers(data_empty, 0) is None

def test_parse_sheet_headers_normal(data_multiheader):
    expected = pd.Index(['', 'col1', 'col1'])
    assert util.parse_sheet_headers(data_multiheader, 1).equals(expected)

def test_parse_sheet_headers_multiheader(data_multiheader):
    """Note that 'test_index' should be shifted up"""
    expected = pd.MultiIndex.from_arrays([['test_index', 'col1', 'col1'],
                                          ['', 'subcol1', 'subcol2']])
    assert util.parse_sheet_headers(data_multiheader, 2).equals(expected)

def test_parse_sheet_headers_multiheader3(data_multiheader):
    """Note that 'test_index' and 1 should be shifted up"""
    expected = pd.MultiIndex.from_arrays([['test_index', 'col1', 'col1'],
                                          [1, 'subcol1', 'subcol2'],
                                          ['', 2, 3]])
    assert util.parse_sheet_headers(data_multiheader, 3).equals(expected)


def test_fillna(df):
    df.loc[2] = [None, None]
    df.loc[3] = [np.NaN, np.NaN]
    df['col1'] = df['col1'].astype('category')

    assert util.fillna(df, 'n\a').loc[2].tolist() == \
        util.fillna(df, 'n\a').loc[3].tolist() ==  \
        ['n\a', 'n\a']


def test_get_range():
    assert util.get_range('a1', (3, 3)) == 'A1:C3'
