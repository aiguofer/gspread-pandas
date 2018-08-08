import gspread_pandas.client


def test_module():
    assert hasattr(gspread_pandas.client, "Spread")
    assert hasattr(gspread_pandas.client, "Client")
