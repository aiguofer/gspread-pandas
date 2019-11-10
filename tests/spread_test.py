from time import sleep

import pandas as pd
import pytest
from gspread.models import Worksheet

from gspread_pandas import Spread, util


@pytest.mark.usefixtures("betamax_spread")
class TestSpread:
    spread = Spread

    def test_spread(self):
        assert isinstance(self.spread, Spread)
        assert self.spread.email
        assert self.spread.url
        assert isinstance(self.spread.sheets, list)
        assert isinstance(self.spread.sheet, Worksheet)
        assert self.spread.sheets[0].id == self.spread.sheet.id

    def test_open_sheet(self):
        sheet = self.spread.sheets[0]
        self.spread.open_sheet(0)
        by_index = self.spread.sheet
        self.spread.open_sheet(sheet)
        by_sheet = self.spread.sheet
        self.spread.open_sheet(sheet.title)
        by_name = self.spread.sheet

        assert by_index.id == by_sheet.id == by_name.id

    def test_df(self):
        df = self.spread.sheet_to_df(header_rows=2, start_row=2)

        assert isinstance(df.columns, pd.MultiIndex)
        assert df.shape == (3, 9)

        self.spread.df_to_sheet(
            df,
            start="A2",
            replace=True,
            sheet="Test df_to_sheet",
            freeze_index=True,
            freeze_headers=True,
            add_filter=True,
            merge_headers=True,
        )

        # ensre values are the same
        assert (
            self.spread.sheets[1].get_all_values()
            == self.spread.sheets[2].get_all_values()
        )

        sheets_metadata = self.spread._spread_metadata["sheets"]

        # ensure merged cells match
        assert util.remove_keys_from_list(
            sheets_metadata[1]["merges"], ["sheetId"]
        ) == util.remove_keys_from_list(sheets_metadata[2]["merges"], ["sheetId"])

        # ensure basic filter matches
        assert util.remove_keys(
            sheets_metadata[1]["basicFilter"]["range"], ["sheetId"]
        ) == util.remove_keys(sheets_metadata[2]["basicFilter"]["range"], ["sheetId"])

        # ensure frozen cols/rows and dims match
        assert (
            sheets_metadata[1]["properties"]["gridProperties"]
            == sheets_metadata[2]["properties"]["gridProperties"]
        )

        self.spread.unmerge_cells()
        # sometimes it fetches the data too quickly and it hasn't
        # updated
        sleep(1)
        self.spread.refresh_spread_metadata()
        sheets_metadata = self.spread._spread_metadata["sheets"]

        # ensure merged cells don't match
        assert util.remove_keys_from_list(
            sheets_metadata[1]["merges"], ["sheetId"]
        ) != util.remove_keys_from_list(
            sheets_metadata[2].get("merges", {}), ["sheetId"]
        )

        self.spread.delete_sheet("Test df_to_sheet")
