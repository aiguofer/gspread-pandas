import json
from os import path, makedirs

_default_dir = path.expanduser('~/.google/')

def ensure_path(pth):
    if not path.exists(pth):
        makedirs(pth)

def get_config(conf_dir=_default_dir, file_name='google_secret.json'):
    """
    Get config for Google client. Looks in ~/.google/google_secret.json by
    default, can override with conf_dir and file_name

    Download json from https://console.developers.google.com/apis/credentials
    """
    creds_dir = path.join(conf_dir, 'creds')
    ensure_path(creds_dir)

    cfg_file = path.join(conf_dir, file_name)

    if not path.exists(cfg_file):
        raise IOError('No Google client config found.\nPlease download json from https://console.developers.google.com/apis/credentials and save as ~/.google/google_secret.json')

    with open(cfg_file) as f:
        cfg = json.load(f)['installed']

    cfg['creds_dir'] = creds_dir
    return cfg
