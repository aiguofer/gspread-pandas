from time import sleep

import pandas as pd
import pytest
from gspread.models import Worksheet
from past.builtins import basestring

from gspread_pandas import Client, Spread, util


@pytest.mark.usefixtures("betamax_client")
class TestClient:
    # just here just for autocompletion during development, during
    # test run this will be overridden by the above fixture
    client = Client

    def test_root(self):
        root = self.client.root
        assert isinstance(root, dict)
        assert {"id", "name"} == set(root.keys())

    def test_directories(self):
        dirs = self.client.directories
        for d in dirs:
            assert isinstance(d, dict)
            assert {"name", "id", "path"} == set(d.keys())

    def test_email(self):
        assert isinstance(self.client.auth.service_account_email, basestring)

    def test_email_no_perm(self, betamax_client_bad_scope, capsys):
        betamax_client_bad_scope.email
        captured = capsys.readouterr()
        assert "Couldn't retrieve" in str(captured)

    def test_list_spreadsheet_files(self):
        self.client.refresh_directories()
        files = self.client.list_spreadsheet_files()
        assert isinstance(files, list)

        for f in files:
            assert isinstance(f, dict)
            assert {"name", "id", "path"} == set(f.keys())

    def test_find_spreadsheet_files_in_folder(self):
        files = self.client.list_spreadsheet_files_in_folder("root")

        assert isinstance(files, list)

        for f in files:
            assert f["path"] == "/"

    def test_find_folders(self):
        dirs = self.client.directories
        dirs_sub = self.client.find_folders("Sub")

        assert set(d["id"] for d in dirs_sub) < set(d["id"] for d in dirs)

    def test_find_spreadsheet_files_in_folders(self):
        files = self.client.find_spreadsheet_files_in_folders("sub")

        assert isinstance(files, dict)
        assert all("sub" in k.lower() for k in files.keys())
        assert all(isinstance(v, list) for v in files.values())

    def test_create_folder(self):
        self.client.create_folder("/this/is/a/new/dir")
        assert (
            next(
                d
                for d in self.client.directories
                if "/this/is/a/new" in d["path"] and d["name"] == "dir"
            )
            is not None
        )

    def test_create_folder_no_parents(self):
        with pytest.raises(Exception):
            self.client.create_folder("/this/does/not/exist", parents=False)

    def test_move_file(self):
        self.client.create("test")
        files = self.client.list_spreadsheet_files_in_folder("root")
        to_move = files[0]
        self.client.move_file(to_move["id"], "/this/is/a/new/dir")

        assert to_move["id"] not in [
            f["id"] for f in self.client.list_spreadsheet_files_in_folder("root")
        ]

        new_dir = next(
            d
            for d in self.client.directories
            if "/this/is/a/new" in d["path"] and d["name"] == "dir"
        )

        assert to_move["id"] in [
            f["id"] for f in self.client.list_spreadsheet_files_in_folder(new_dir["id"])
        ]


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
