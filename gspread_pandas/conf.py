import json
import sys
from os import environ, name

from future.utils import reraise
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.oauth2.service_account import Credentials as SACredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from past.builtins import basestring

from gspread_pandas.exceptions import ConfigException
from gspread_pandas.util import decode

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


__all__ = ["default_scope", "get_config", "get_creds"]
if name == "nt":
    _default_dir = Path(environ.get("APPDATA")) / "gspread_pandas"
else:
    _default_dir = (
        Path(environ.get("$XDG_CONFIG_HOME", Path(environ.get("HOME")) / ".config"))
        / "gspread_pandas"
    )
_default_file = "google_secret.json"

default_scope = [
    "openid",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/spreadsheets",
]

CONFIG_DIR_ENV_VAR = "GSPREAD_PANDAS_CONFIG_DIR"


def get_config_dir():
    """Get the config directory. It will first look in the environment variable
    GSPREAD_PANDAS_CONFIG_DIR, but if it's not set it'll use ~/.config/gspread_pandas
    """
    return Path(environ.get(CONFIG_DIR_ENV_VAR, _default_dir))


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
    full_path = Path(full_path)
    if not full_path.exists():
        full_path.mkdir(parents=True, exist_ok=True)


def get_config(conf_dir=None, file_name=_default_file):
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
    conf_dir = Path(conf_dir).expanduser() if conf_dir else get_config_dir()
    cfg_file = conf_dir / file_name

    if not cfg_file.exists():
        raise IOError(
            "No Google client config found.\n"
            "Please download json from "
            "https://console.developers.google.com/apis/credentials and "
            "save as {}".format(cfg_file)
        )

    with cfg_file.open() as fp:
        cfg = json.load(fp)

    return cfg


def get_creds(
    user="default", config=None, scope=default_scope, creds_dir=None, save=True
):
    """Get google google.auth.credentials.Credentials for the given user. If the user
    doesn't have previous creds, they will go through the OAuth flow to get new
    credentials which will be saved for later use. Credentials will be saved in
    config['creds_dir'], if this value is not set, then they will be stored in a folder
    named ``creds`` in the default config dir (either ~/.config/gspread_pandas or
    $GSPREAD_PANDAS_CONFIG_DIR)

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
    creds_dir : str, Path
        Optional, directory to load and store creds from/in. If None, it will use the
        ``creds`` subdirectory in the default config location. (Default value = None)
    scope : list
        Optional, scope to use for Google Auth (Default value = default_scope)

    Returns
    -------
    google.auth.credentials.Credentials
        Google credentials that can be used with gspread
    """
    config = config or get_config()
    try:
        if "private_key_id" in config:
            return SACredentials.from_service_account_info(config, scopes=scope)

        if not isinstance(user, basestring):
            raise ConfigException(
                "Need to provide a user key as a string if not using a service account"
            )

        if creds_dir is None:
            creds_dir = get_config_dir() / "creds"

        creds_file = Path(creds_dir) / user

        if creds_file.exists():
            # need to convert Path to string for python 2.7
            return OAuthCredentials.from_authorized_user_file(str(creds_file))

        flow = InstalledAppFlow.from_client_config(
            config, scope, redirect_uri="urn:ietf:wg:oauth:2.0:oob"
        )
        creds = flow.run_console()

        if save:
            creds_data = {
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }

            ensure_path(creds_dir)
            creds_file.write_text(decode(json.dumps(creds_data)))

        return creds
    except Exception:
        exc_info = sys.exc_info()

    if "exc_info" in locals():
        reraise(ConfigException, *exc_info[1:])
