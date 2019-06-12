Configuration
=============

There's a variety of ways to change the default behavior of how/where configuration is stored.

By default, the configuration will be in ``$HOME/.config/gspread_pandas`` on Nix systems and
``%APPDATA%\gspread_pandas`` on Windows. Unde the default behavior, you must have your Google
client credentials stored in ``google_secret.json`` in that directory. If you're not using a
Service Account, the user credentials will be stored in a subdirectory called ``creds``.

The easiest way to change the default location is to set the ``GSPREAD_PANDAS_CONFIG_DIR``
env variable to the directory where you want to store everything. If you use this, the
client creds will still need to be named ``google_secret.json`` and user creds will still
be stored in the ``creds`` subdirectory.

If you have different client credentials, you could load them passing in ``conf_dir`` and/or
``file_name`` to ``gspread_pandas.conf.get_config``. Alternatively, you could pull these from
elsewhere, like a database. Once you have the config, you could then pass that to a
``Client`` or ``Spread`` instance, or you could get credentials by passing it to
``gspread_pandas.conf.get_creds``.

When using a Service Account, the ``user`` param will be ignored in ``Client``, ``Spread`` and
``get_creds``. Otherwise, this will be used to store the OAuth2 credentials for each user in the
creds subdirectory. If you generate your credentials elsewhere, you can pass them in to a ``Client``
or ``Spread``. You can also run through the flow to get OAuth2 and avoid saving them by calling
``get_creds`` directly. You can also override the ``creds_dir`` if you call this function.
