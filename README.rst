===============
Getting Started
===============

.. image:: https://img.shields.io/pypi/v/gspread-pandas.svg
        :target: https://pypi.python.org/pypi/gspread-pandas
        :alt: PyPI Version

.. image:: https://img.shields.io/travis/aiguofer/gspread-pandas.svg
        :target: https://travis-ci.org/aiguofer/gspread-pandas
        :alt: Travis-CI Build Status

.. image:: https://readthedocs.org/projects/gspread-pandas/badge/?version=latest
        :target: https://gspread-pandas.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

author: Diego Fernandez

Links:

-  `Documentation <http://gspread-pandas.readthedocs.io/>`_
-  `Source code <https://github.com/aiguofer/gspread-pandas>`_
-  `Short video tutorial <https://youtu.be/2yIcNYzfzPw>`_

.. attention:: There will be breaking API changes in v2. Mainly, I will be
  making the ``user`` key optional and OAuth credentials will be stored under
  a ``default`` file. This should make it easier to use for the common single
  user case, as well as for those using ServiceAccount credentials. I'd love to hear
  your opinion on `the issue <https://github.com/aiguofer/gspread-pandas/issues/24>`__.
  I will also be standardizing the API for ``Spread.add_filter`` to match other functions.
  Feel free to check out the current work on `the v2 branch
  <https://github.com/aiguofer/gspread-pandas/tree/v2>`__.

  To disable warnings:

  .. code-block:: python

        import gspread_pandas.util as util
        util.DEPRECATION_WARNINGS_ENABLED = False

Overview
========

A package to easily open an instance of a Google spreadsheet and
interact with worksheets through Pandas DataFrames. It enables you to
easily pull data from Google spreadsheets into DataFrames as well as
push data into spreadsheets from DataFrames. It leverages
`gspread <https://github.com/burnash/gspread/>`__ in the backend for
most of the heavylifting, but it has a lot of added functionality
to handle things specific to working with DataFrames as well as
some extra nice to have features.

Some key goals/features:

-  Nicely handle headers and indexes
-  Run on Jupyter, headless server, and/or scripts
-  Allow storing different user credentials
-  Automatically handle token refreshes
-  Enable handling of frozen rows and columns
-  Enable handling of merged cells
-  Nicely handle large data sets and retries
-  Enable creation of filters
-  Handle retries when exceeding 100s quota
-  Handle cell merges with option to merge multi-level header cells

Installation / Usage
====================

To install use pip:

.. code-block:: console

    $ pip install gspread-pandas

Or clone the repo:

.. code-block:: console

    $ git clone https://github.com/aiguofer/gspread-pandas.git
    $ python setup.py install

Before using, you will need to download Google client credentials for
your app.

Client Credentials
------------------

To allow a script to use Google Drive API we need to authenticate our
self towards Google. To do so, we need to create a project, describing
the tool and generate credentials. Please use your web browser and go to
`Google console <https://console.developers.google.com/>`__ and :

-  Choose **Create Project** in popup menu on the top.
-  A dialog box appears, so give your project a name and click on
   **Create** button.
-  On the left-side menu click on **API Manager**.
-  A table of available APIs is shown. Switch **Drive API** and click on
   **Enable API** button. Do the same for **Sheets API**. Other APIs might
   be switched off, for our purpose.
-  On the left-side menu click on **Credentials**.
-  In section **OAuth consent screen** select your email address and
   give your product a name. Then click on **Save** button.
-  In section **Credentials** click on **Add credentials** and switch
   **OAuth 2.0 client ID**.
-  A dialog box **Create Cliend ID** appears. Select **Application
   type** item as **Other**.
-  Click on **Create** button.
-  Click on **Download JSON** icon on the right side of created **OAuth
   2.0 client IDs** and store the downloaded file on your file system.
   Please be aware, the file contains your private credentials, so take
   care of the file in the same way you care of your private SSH key;
   i.e. move downloaded JSON to ``~/.config/gspread_pandas/google_secret.json``
   (or you can configure the directory and file name by directly calling
   ``gspread_pandas.conf.get_config``

Thanks to similar project
`df2gspread <https://github.com/maybelinot/df2gspread>`__ for this great
description of how to get the client credentials.

User Credentials
----------------

Once you have your client credentials, you can have multiple user
credentials stored in the same machine. This can be useful when you have
a shared server (for example with a Jupyter notebook server) with
multiple people that may want to use the library. The first parameter to
``Spread`` must be the key identifying a user's credentials. The first
time this is called for a specific key, you will have to authenticate
through a text based OAuth prompt; this makes it possible to run on a headless
server through ssh or through a Jupyter notebook. After this, the
credentials for that user will be stored (by default in
``~/.config/gspread_pandas/creds`` or you can manually set it in
``GSPREAD_PANDAS_CONFIG_DIR`` env var) and the tokens will berefreshed
automatically any time the tool is used.

Users will only be able to interact with Spreadsheets that they have
access to.

Handling Authentication
-----------------------

In the backend, the library is leveraging
`Google's oauth2client <http://oauth2client.readthedocs.io/en/latest/>`__ to
handle authentication. It conveniently stores everything as described
above so that you don't have to worry about boiler plate code to handle auth.
However, if you need to customize how you handle authentication you can do so
in a few different ways. You can change the directory where everything is stored
using the ``GSPREAD_PANDAS_CONFIG_DIR`` env var. You can also generate your own
``oauth2client.client.OAuth2Credentials`` and pass them in when instanciating a
``Client`` or ``Spread`` object. For other ways to customize authentication, see
``gspread_pandas.conf.get_config`` and ``gspread_pandas.conf.get_creds``

Contributing
============

Code should be run through black, isort, and flake8 before being merged. Pre-commit
takes care of it for you, but you need to have Python 3 installed to be able to run
black. To contribute, please fork the repo, create a feature branch, push it to your
repo, then create a pull request.

To install and set up the environment after you fork it (replace `aiguofer` with your
username):

.. code-block:: console

    $ git clone https://github.com/aiguofer/gspread-pandas.git && cd gspread-pandas
    $ pip install -e ".[dev]"
    $ pre-commit install


Example
=======

.. code:: python

    from __future__ import print_function
    import pandas as pd
    from gspread_pandas import Spread, Client

    file_name = "http://stats.idre.ucla.edu/stat/data/binary.csv"
    df = pd.read_csv(file_name)

    # 'Example Spreadsheet' needs to already exist and your user must have access to it
    spread = Spread('example_user', 'Example Spreadsheet')
    # This will ask to authenticate if you haven't done so before for 'example_user'

    # Display available worksheets
    spread.sheets

    # Save DataFrame to worksheet 'New Test Sheet', create it first if it doesn't exist
    spread.df_to_sheet(df, index=False, sheet='New Test Sheet', start='A2', replace=True)
    spread.update_cells('A1', 'A1', ['Created by:', spread.email])
    print(spread)
    # <gspread_pandas.client.Spread - User: '<example_user>@gmail.com', Spread: 'Example Spreadsheet', Sheet: 'New Test Sheet'>

    # You can now first instanciate a Client separately and query folders and
    # instanciate other Spread objects by passing in the Client
    client = Client('example_user')
    # Assumming you have a dir called 'example dir' with sheets in it
    available_sheets = client.find_spreadsheet_files_in_folders('example dir')
    spreads = []
    for sheet in available_sheets.get('example dir', []):
        spreads.append(Spread(client, sheet['id']))

Troubleshooting
===============

SSL Error
---------

If you're getting an SSL related error or can't seem to be able to open existing
spreadsheets that you have access to, you might be running into an issue caused by
``certifi``. This has mainly been experienced on RHEL and CentOS running Python 2.7.
You can read more about it in `issue 223
<https://github.com/burnash/gspread/issues/223>`_
and `issue 354 <https://github.com/burnash/gspread/issues/354>`_ but, in short, the
solution is to either install a specific version of ``certifi`` that works for you,
or remove it altogether.

.. code-block:: console

   pip install certifi==2015.4.28

or

.. code-block:: console

   pip uninstall certifi

EOFError in Rodeo
-----------------

If you're trying to use ``gspread_pandas`` from within
`Rodeo <https://www.yhat.com/products/rodeo>`_ you might get an
``EOFError: EOF when reading a line`` error when trying to pass in the verification
code. The workaround for this is to first verify your account in a regular shell.
Since you're just doing this to get your Oauth token, the spreadsheet doesn't need
to be valid. Just run this in shell:

.. code:: python

   python -c "from gspread_pandas import Spread; Spread('<user_key>','')"

Then follow the instructions to create and store the OAuth creds.
