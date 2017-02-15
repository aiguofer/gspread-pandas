import json
from os import path, makedirs

_default_dir = path.expanduser('~/.config/gspread_pandas')
_default_file = 'google_secret.json'

def ensure_path(pth):
    if not path.exists(pth):
        makedirs(pth)

def get_config(conf_dir=_default_dir, file_name=_default_file):
    """
    Get config for Google client. Looks in ~/.config/gspread_pandas/google_secret.json
    by default, can override with conf_dir and file_name

    Download json from https://console.developers.google.com/apis/credentials
    """
    # Migrate config, this can be deleted in 1.0
    _migrate_config()
    creds_dir = path.join(conf_dir, 'creds')
    ensure_path(creds_dir)

    cfg_file = path.join(conf_dir, file_name)

    if not path.exists(cfg_file):
        raise IOError('No Google client config found.\nPlease download json from https://console.developers.google.com/apis/credentials and save as ~/.config/gspread_pandas/google_secret.json')

    with open(cfg_file) as f:
        cfg = json.load(f)['installed']

    cfg['creds_dir'] = creds_dir
    return cfg

def _migrate_config():
    old_dir = path.expanduser('~/.google/')
    if path.exists(path.join(old_dir, _default_file)):
        import shutil
        shutil.move(old_dir, _default_dir)
        print("Config migrated from {0} to {1}".format(old_dir, _default_dir))
