import json
from os import path, makedirs

_default_dir = path.expanduser('~/.google/')

def ensure_path(pth):
    if not path.exists(pth):
        makedirs(pth)

def get_config(conf_dir=_default_dir, file_name='google_secret.json'):
    """
    Get config for Google client. Looks in ~/.google/google_secret.json by
    default, can override with env vars GSPREAD_PANDAS_CONFIG and
    GSPREAD_PANDAS_CLIENT_FILE.

    Download json from https://console.developers.google.com/apis/credentials
    """
    creds_dir = path.join(conf_dir, 'creds')
    ensure_path(creds_dir)

    cfg_file = path.join(conf_dir, file_name)
    with open(cfg_file) as f:
        cfg = json.load(f)['installed']

    cfg['creds_dir'] = creds_dir
    return cfg
