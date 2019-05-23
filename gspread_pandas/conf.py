import json
from os import environ, makedirs, path

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.tools import argparser, run_flow
from past.builtins import basestring

from gspread_pandas.exceptions import ConfigException

__all__ = ["default_scope", "get_config", "get_creds"]

_default_dir = "~/.config/gspread_pandas"
_default_file = "google_secret.json"

default_scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.email",
]


def get_config_dir():
    """Get the config directory. It will first look in the environment variable
    GSPREAD_PANDAS_CONFIG_DIR, but if it's not set it'll use ~/.config/gspread_pandas
    """
    return environ.get("GSPREAD_PANDAS_CONFIG_DIR", _default_dir)


def ensure_path(full_path):
    """Create path if it doesn't exist

    Parameters
    ----------
    full_path : str
        Path to create if needed

    Returns
    -------
    None
    """
    if not path.exists(full_path):
        makedirs(full_path)


def get_config(conf_dir=get_config_dir(), file_name=_default_file):
    """Get config for Google client. Looks in ~/.config/gspread_pandas/google_secret.json
    by default but you can override it with conf_dir and file_name. The creds_dir
    value will be set to conf_dir/creds and the directory will be created if it doesn't
    exist; if you'd like to override that you can do so by changing the 'creds_dir'
    value in the dict returned by this function.

    Download json from https://console.developers.google.com/apis/credentials

    Parameters
    ----------
    conf_dir : str
        Full path to config dir (Default value = get_config_dir())
    file_name : str
        (Default value = "google_secret.json")

    Returns
    -------
    dict
        Dict with necessary contents of google_secret.json
    """
    conf_dir = path.expanduser(conf_dir)
    cfg_file = path.join(conf_dir, file_name)

    if not path.exists(cfg_file):
        raise IOError(
            "No Google client config found.\n"
            "Please download json from "
            "https://console.developers.google.com/apis/credentials and "
            "save as {}".format(cfg_file)
        )

    with open(cfg_file) as f:
        cfg = json.load(f)
        # Different type of App Creds have a different key
        # and Service Accounts aren't nested
        if len(cfg.keys()) == 1:
            cfg = cfg[list(cfg.keys())[0]]

    cfg["creds_dir"] = path.join(conf_dir, "creds")

    return cfg


def get_creds(user="default", config=None, scope=default_scope):
    """Get google OAuth2Credentials for the given user. If the user doesn't have previous
    creds, they will go through the OAuth flow to get new credentials which
    will be saved for later use. Credentials will be saved in config['creds_dir'], if
    this value is not set, then they will be stored in a folder named ``creds`` in the
    default config dir (either ~/.config/gspread_pandas or $GSPREAD_PANDAS_CONFIG_DIR)

    Alternatively, it will get credentials from a service account.

    Parameters
    ----------
    user : str
        Unique key indicating user's credentials. This is not necessary when using
        a ServiceAccount and will be ignored (Default value = "default")
    config : dict
        Optional, dict with "client_id", "client_secret", and "redirect_uris" keys for
        OAuth or "type", "client_email", "private_key", "private_key_id", and
        "client_id" for a Service Account. If None is passed, it will call
        :meth:`get_config() <get_config>` (Default value = None)
    scope : list
        Optional, scope to use for Google Auth (Default value = default_scope)

    Returns
    -------
    OAuth2Credentials, ServiceAccountCredentials
        Google credentials that can be used with gspread
    """
    config = config or get_config()

    if "private_key_id" in config:
        return ServiceAccountCredentials.from_json_keyfile_dict(config, scope)

    if not isinstance(user, basestring):
        raise ConfigException(
            "Need to provide a user key as a string if not using a service account"
        )

    if "creds_dir" not in config:
        config["creds_dir"] = path.expanduser(path.join(get_config_dir(), "creds"))

    ensure_path(config["creds_dir"])

    creds_file = path.join(config["creds_dir"], user)

    if path.exists(creds_file):
        return Storage(creds_file).locked_get()

    if all(key in config for key in ("client_id", "client_secret", "redirect_uris")):
        flow = OAuth2WebServerFlow(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_uri=config["redirect_uris"][0],
            scope=scope,
        )

        storage = Storage(creds_file)
        args = argparser.parse_args(args=["--noauth_local_webserver"])

        return run_flow(flow, storage, args)

    raise ConfigException("Unknown config file format")
