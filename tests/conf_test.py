import json
import os

import pytest
from Crypto.PublicKey import RSA
from oauth2client.client import OAuth2Credentials
from oauth2client.service_account import ServiceAccountCredentials

from gspread_pandas import conf, exceptions

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


def decode(strg):
    try:
        strg = strg.decode()
    except AttributeError:
        pass
    return strg


def make_config(tmpdir_factory, config):
    # convert to str for python 3.5 compat
    f = Path(str(tmpdir_factory.mktemp("conf").join("google_secret.json")))
    f.write_text(decode(json.dumps(config)))
    return f.parent, f.name


@pytest.fixture
def sa_config(tmpdir_factory):
    config = {
        "type": "service_account",
        "project_id": "",
        "private_key_id": "",
        "private_key": RSA.generate(2048).exportKey("PEM").decode(),
        "client_email": "",
        "client_id": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "",
    }
    return make_config(tmpdir_factory, config)


@pytest.fixture
def oauth_config(tmpdir_factory):
    config = {
        "installed": {
            "client_id": "",
            "project_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }
    return make_config(tmpdir_factory, config)


def unset_env():
    os.environ[conf.CONFIG_DIR_ENV_VAR] = ""


@pytest.fixture
def set_oauth_config(request, oauth_config):
    os.environ[conf.CONFIG_DIR_ENV_VAR] = str(oauth_config[0])
    request.addfinalizer(unset_env)


@pytest.fixture
def set_sa_config(request, sa_config):
    os.environ[conf.CONFIG_DIR_ENV_VAR] = str(sa_config[0])
    request.addfinalizer(unset_env)


@pytest.fixture
def make_creds(oauth_config, set_oauth_config):
    creds = {
        "access_token": "",
        "client_id": "",
        "client_secret": "",
        "refresh_token": "",
        "token_expiry": "2019-05-25T04:21:52Z",
        "token_uri": "https://oauth2.googleapis.com/token",
        "user_agent": None,
        "revoke_uri": "https://oauth2.googleapis.com/revoke",
        "id_token": {
            "iss": "https://accounts.google.com",
            "azp": "",
            "aud": "",
            "sub": "",
            "email": "",
            "email_verified": True,
            "at_hash": "MoXn24dfJiPj1RnBRLtLng",
            "iat": 1558754512,
            "exp": 1558758112,
        },
        "id_token_jwt": "",
        "token_response": {
            "access_token": "",
            "expires_in": 3600,
            "refresh_token": "",
            "scope": "",
            "token_type": "Bearer",
            "id_token": "",
        },
        "scopes": [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/drive",
        ],
        "token_info_uri": "https://oauth2.googleapis.com/tokeninfo",
        "invalid": False,
        "_class": "OAuth2Credentials",
        "_module": "oauth2client.client",
    }
    creds_dir = oauth_config[0] / "creds"
    conf.ensure_path(creds_dir)

    creds_dir.joinpath("default").write_text(decode(json.dumps(creds)))


class Test_get_config:
    def test_no_file(self):
        with pytest.raises(IOError):
            conf.get_config(file_name="this_file_doesnt_exist")

    def test_with_oauth(self, oauth_config):
        c = conf.get_config(*oauth_config)
        assert isinstance(c, dict)
        assert "creds_dir" in c
        assert len(c) > 1

    def test_with_sa(self, sa_config):
        c = conf.get_config(*sa_config)
        assert isinstance(c, dict)
        assert "creds_dir" in c
        assert len(c) > 1


class Test_get_creds:
    def test_service_account(self, set_sa_config):
        creds = conf.get_creds()
        assert isinstance(creds, ServiceAccountCredentials)

    def test_oauth_no_key(self, set_oauth_config):
        with pytest.raises(exceptions.ConfigException):
            conf.get_creds(user=None)

    def test_oauth_first_time(self, mocker, set_oauth_config):
        mocker.patch.object(conf, "run_flow")
        conf.get_creds()
        # python 3.5 doesn't have assert_called_once
        assert conf.run_flow.call_count == 1

    def test_oauth_default(self, make_creds):
        assert isinstance(conf.get_creds(), OAuth2Credentials)

    def test_bad_config(self):
        with pytest.raises(exceptions.ConfigException):
            conf.get_creds(config={"foo": "bar"})
