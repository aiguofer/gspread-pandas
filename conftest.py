import json
import os

import pytest
from betamax import Betamax
from betamax_serializers.pretty_json import PrettyJSONSerializer
from Crypto.PublicKey import RSA
from google.auth.transport.requests import AuthorizedSession

from gspread_pandas import Client, Spread, conf
from gspread_pandas.util import decode

# from betamax_json_body_serializer import JSONBodySerializer
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

pytest.RECORD = os.environ.get("GSPREAD_RECORD") is not None
pytest.DUMMY_TOKEN = "<ACCESS_TOKEN>"


def configure_betamax():
    Betamax.register_serializer(PrettyJSONSerializer)
    with Betamax.configure() as config:
        config.cassette_library_dir = "tests/cassettes/"
        config.default_cassette_options["serialize_with"] = "prettyjson"

        config.before_record(callback=sanitize_token)

        record_mode = "once" if pytest.RECORD else "none"

        config.default_cassette_options["record_mode"] = record_mode


def sanitize_token(interaction, current_cassette):
    headers = interaction.data["request"]["headers"]
    # google-auth creds set the authorization key using lower case
    token = headers.get("authorization")

    if token is None:
        return

    interaction.data["request"]["headers"]["authorization"] = [
        "Bearer " + pytest.DUMMY_TOKEN
    ]


def make_config(tmpdir_factory, config):
    # convert to str for python 3.5 compat
    f = Path(str(tmpdir_factory.mktemp("conf").join("google_secret.json")))
    f.write_text(decode(json.dumps(config)))
    return f.parent, f.name


def _get_cassette_name(request):
    cassette_name = ""

    if request.module is not None:
        cassette_name += request.module.__name__ + "."

    if request.cls is not None:
        cassette_name += request.cls.__name__ + "."

    cassette_name += request.function.__name__
    return cassette_name


def _set_up_recorder(session, request, cassette_name):
    recorder = Betamax(session)
    recorder.use_cassette(cassette_name)
    recorder.start()
    request.addfinalizer(recorder.stop)

    return recorder


@pytest.fixture
def betamax_authorizedsession(request, set_test_config):
    cassette_name = _get_cassette_name(request)
    session = AuthorizedSession(conf.get_creds())
    if pytest.RECORD:
        session.credentials.refresh(session._auth_request)
    else:
        session.credentials.token = pytest.DUMMY_TOKEN
    recorder = _set_up_recorder(session, request, cassette_name)

    request.cls.session = session
    request.cls.recorder = recorder

    return session


@pytest.fixture
def betamax_client(request, betamax_authorizedsession):
    request.cls.client = Client(session=betamax_authorizedsession)
    return request.cls.client


@pytest.fixture
def betamax_spread(request, betamax_client):
    request.cls.spread = Spread(
        "1u626GkYm1RAJSmHcGyd5_VsHNr_c_IfUcE_W-fQGxIM", sheet=0, client=betamax_client
    )

    return request.cls.spread


@pytest.fixture
def betamax_client_bad_scope(request, set_test_config):
    cassette_name = _get_cassette_name(request)
    session = AuthorizedSession(
        conf.get_creds(
            scope=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
        )
    )

    if pytest.RECORD:
        session.credentials.refresh(session._auth_request)
    else:
        session.credentials.token = pytest.DUMMY_TOKEN
    recorder = _set_up_recorder(session, request, cassette_name)
    client = Client(session=session)

    request.cls.session = session
    request.cls.recorder = recorder
    request.cls.client = client

    return client


@pytest.fixture
def set_test_config(set_sa_config):
    if pytest.RECORD:
        os.environ[conf.CONFIG_DIR_ENV_VAR] = str(os.getcwd())


@pytest.fixture(scope="session")
def sa_config_json():
    return {
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


@pytest.fixture(scope="session")
def oauth_config_json():
    return {
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


@pytest.fixture(scope="session")
def creds_json():
    return {
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


@pytest.fixture
def sa_config(tmpdir_factory, sa_config_json):
    return make_config(tmpdir_factory, sa_config_json)


@pytest.fixture
def oauth_config(tmpdir_factory, oauth_config_json):
    return make_config(tmpdir_factory, oauth_config_json)


def unset_env():
    os.environ.pop(conf.CONFIG_DIR_ENV_VAR)


@pytest.fixture
def set_oauth_config(request, oauth_config):
    os.environ[conf.CONFIG_DIR_ENV_VAR] = str(oauth_config[0])
    request.addfinalizer(unset_env)


@pytest.fixture
def set_sa_config(request, sa_config):
    os.environ[conf.CONFIG_DIR_ENV_VAR] = str(sa_config[0])
    request.addfinalizer(unset_env)


@pytest.fixture
def make_creds(oauth_config, set_oauth_config, creds_json):
    creds_dir = oauth_config[0] / "creds"
    conf.ensure_path(creds_dir)

    creds_dir.joinpath("default").write_text(decode(json.dumps(creds_json)))


configure_betamax()
