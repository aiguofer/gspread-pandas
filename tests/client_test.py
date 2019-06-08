import pytest
from past.builtins import basestring

# from gspread_pandas import Client, Spread


@pytest.mark.usefixtures("betamax_client")
class TestClient:
    # just here just for autocompletion during development
    # client = Client

    def test_email(self):
        assert isinstance(self.client.auth.service_account_email, basestring)

    def test_email_no_perm(self, betamax_client_bad_scope, capsys):
        betamax_client_bad_scope.email
        captured = capsys.readouterr()
        assert "Couldn't retrieve" in str(captured)

    def test_get_spreadsheet_files(self):
        self.client.directories
        assert isinstance(self.client.list_spreadsheet_files(), list)

    def test_root(self):
        pass

    def test_directories(self):
        # missing parents
        # has path
        pass
