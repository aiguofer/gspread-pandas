import numpy as np
import pandas as pd
import pytest

from gspread_pandas import util

TEST = 0
ANSWER = 1


@pytest.fixture
def df():
    data = [[1, 2], [3, 4]]
    cols = ["col1", "col2"]
    df = pd.DataFrame(data, columns=cols)
    df.index.name = "test_index"
    return df


@pytest.fixture
def df_empty():
    return pd.DataFrame()


@pytest.fixture
def df_multiheader():
    data = [[1, 2], [3, 4]]
    cols = pd.MultiIndex.from_tuples([("col1", "subcol1"), ("col1", "subcol2")])
    return pd.DataFrame(data, columns=cols)


@pytest.fixture
def df_multiheader_w_index():
    data = [[1, 2], [3, 4]]
    cols = pd.MultiIndex.from_tuples([("col1", "subcol1"), ("col1", "subcol2")])
    df = pd.DataFrame(data, columns=cols)
    df.index.name = "test_index"
    return df.reset_index()


@pytest.fixture
def df_multiheader_w_multiindex():
    data = [[1, 2], [3, 4]]
    cols = pd.MultiIndex.from_tuples([("col1", "subcol1"), ("col1", "subcol2")])
    ix = pd.MultiIndex.from_tuples(
        [("row1", "subrow1"), ("row1", "subrow2")], names=["l1", "l2"]
    )
    df = pd.DataFrame(data, columns=cols, index=ix)
    return df.reset_index()


@pytest.fixture
def df_multiheader_blank_top():
    data = [[1], [3]]
    cols = pd.MultiIndex.from_tuples([("", "subcol1")])
    return pd.DataFrame(data, columns=cols)


@pytest.fixture
def df_multiheader_blank_bottom():
    data = [[1], [3]]
    cols = pd.MultiIndex.from_tuples([("col1", "")])
    return pd.DataFrame(data, columns=cols)


@pytest.fixture
def data_multiheader():
    data = [
        ["", "col1", "col1"],
        ["test_index", "subcol1", "subcol2"],
        [1, 2, 3],
        [4, 5, 6],
    ]
    return data


@pytest.fixture
def data_multiheader_top():
    data = [
        ["test_index", "col1", "col1"],
        ["", "subcol1", "subcol2"],
        [1, 2, 3],
        [4, 5, 6],
    ]
    return data


@pytest.fixture
def data_empty():
    return [[]]


class Test_parse_sheet_index:
    def test_normal(self, df):
        assert util.parse_sheet_index(df, 1).index.name == "col1"

    def test_noop(self, df):
        assert util.parse_sheet_index(df, 0).index.name == "test_index"

    def test_multiheader(self, df_multiheader):
        assert util.parse_sheet_index(df_multiheader, 1).index.name == "subcol1"

    def test_multiheader2(self, df_multiheader):
        assert util.parse_sheet_index(df_multiheader, 2).index.name == "subcol2"

    def test_multiheader_blank_top(self, df_multiheader_blank_top):
        assert (
            util.parse_sheet_index(df_multiheader_blank_top, 1).index.name == "subcol1"
        )

    def test_multiheader_blank_bottom(self, df_multiheader_blank_bottom):
        assert (
            util.parse_sheet_index(df_multiheader_blank_bottom, 1).index.name == "col1"
        )


class Test_parse_df_col_names:
    def test_empty_no_index(self, df_empty):
        assert util.parse_df_col_names(df_empty, False) == [[]]

    def test_normal_no_index(self, df):
        assert util.parse_df_col_names(df, False) == [["col1", "col2"]]

    def test_multiheader_no_index(self, df_multiheader):
        expected = [["col1", "col1"], ["subcol1", "subcol2"]]
        assert util.parse_df_col_names(df_multiheader, False) == expected

    def test_multiheader_w_index(self, df_multiheader_w_index):
        expected = [["", "col1", "col1"], ["test_index", "subcol1", "subcol2"]]
        assert util.parse_df_col_names(df_multiheader_w_index, True) == expected

    def test_multiheader_w_multiindex(self, df_multiheader_w_multiindex):
        expected = [["", "", "col1", "col1"], ["l1", "l2", "subcol1", "subcol2"]]
        assert util.parse_df_col_names(df_multiheader_w_multiindex, True, 2) == expected


class Test_parse_sheet_headers:
    def test_empty(self, data_empty):
        assert util.parse_sheet_headers(data_empty, 0) is None

    def test_normal(self, data_multiheader):
        expected = pd.Index(["", "col1", "col1"])
        assert util.parse_sheet_headers(data_multiheader, 1).equals(expected)

    def test_multiheader(self, data_multiheader):
        """Note that 'test_index' should be shifted up"""
        expected = pd.MultiIndex.from_arrays(
            [["test_index", "col1", "col1"], ["", "subcol1", "subcol2"]]
        )
        assert util.parse_sheet_headers(data_multiheader, 2).equals(expected)

    def test_multiheader3(self, data_multiheader):
        """Note that 'test_index' and 1 should be shifted up"""
        expected = pd.MultiIndex.from_arrays(
            [["test_index", "col1", "col1"], [1, "subcol1", "subcol2"], ["", 2, 3]]
        )
        assert util.parse_sheet_headers(data_multiheader, 3).equals(expected)


def test_chunks():
    tests = [
        (([], 1), []),
        (([1], 1), [[1]]),
        (([1, 2], 1), [[1], [2]]),
        (([1, 2, 3], 2), [[1, 2], [3]]),
    ]
    for test in tests:
        assert [chunk for chunk in util.chunks(*test[TEST])] == test[ANSWER]


def test_get_cell_as_tuple():
    tests = [("A1", (1, 1)), ((1, 1), (1, 1))]
    for test in tests:
        assert util.get_cell_as_tuple(test[TEST]) == test[ANSWER]

    bad_tests = [
        "This is a bad cell string",
        (1.0, 1.0),
        (1, 1, 1),
        {"x": "y"},
        10000000,
    ]

    for test in bad_tests:
        with pytest.raises(TypeError):
            util.get_cell_as_tuple(test)


class Test_create_filter_request:
    pass


class Test_create_frozen_request:
    pass


class Test_create_merge_cells_request:
    pass


class Test_create_unmerge_cells_request:
    pass


class Test_create_merge_headers_request:
    pass


class Test_deprecate:
    pass


class Test_monkey_patch_request:
    util.monkey_patch_request
    pass


class Test_get_col_merge_ranges:
    pass


def test_fillna(df):
    df.loc[2] = [None, None]
    df.loc[3] = [np.NaN, np.NaN]
    df["col1"] = df["col1"].astype("category")

    assert (
        util.fillna(df, "n\a").loc[2].tolist()
        == util.fillna(df, "n\a").loc[3].tolist()
        == ["n\a", "n\a"]
    )


def test_get_range():
    assert util.get_range("a1", (3, 3)) == "A1:C3"


def test_get_contiguous_ranges():
    tests = [
        ([0], []),
        ([0, 0], [(0, 1)]),
        ([0, 1], []),
        ([0, 0, 0], [(0, 2)]),
        ([0, 0, 1], [(0, 1)]),
        ([0, 1, 1], [(1, 2)]),
        ([0, 1, 0], []),
        ([0, 0, 1, 1], [(0, 1), (2, 3)]),
        ([0, 0, 1, 1, 0, 0], [(0, 1), (2, 3), (4, 5)]),
        ([0, 1, 1, 1, 1, 0], [(1, 4)]),
    ]

    for test in tests:
        assert util.get_contiguous_ranges(test[TEST], 0, len(test[0])) == test[ANSWER]
