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
-  Allow storing different user credentials or using Service Accounts
-  Automatically handle token refreshes
-  Enable handling of frozen rows and columns
-  Enable handling of merged cells when pulling data
-  Nicely handle large data sets and auto-retries
-  Enable creation of filters
-  Handle retries when exceeding 100s quota
-  When pushing DataFrames with MultiIndex columns, allow merging or flattening headers
-  Ability to nicely handle Spreadsheet permissions

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
   **OAuth client ID** (if you want to use your own account or enable
   the use of multiple accounts) or **Service account key** (if you prefer
   to have a service account interacting with spreadsheets).
-  If you select **OAuth client ID**:
   -  Select **Application type** item as **Other** and give it a name.
   -  Click on **Create** button.
   -  Click on **Download JSON** icon on the right side of created **OAuth
      client IDs** and store the downloaded file on your file system.
-  If you select **Service account key**
   -  Click on **Service account** dropdown and select **New service account**
   -  Give it a **Service account name** and ignore the **Role** dropdown
      (unless you know you need this for something else, it's not necessary for
      working with spreadsheets)
   -  Note the **Service account ID** as you might need to give that user
      permission to interact with your spreadsheets
   -  Leave **Key type** as **JSON**
   -  Click **Create** and store the downloaded file on your file system.
-  Please be aware, the file contains your private credentials, so take
   care of the file in the same way you care of your private SSH key;
   Move the downloaded JSON to ``~/.config/gspread_pandas/google_secret.json``
   (or you can configure the directory and file name by directly calling
   ``gspread_pandas.conf.get_config``


Thanks to similar project
`df2gspread <https://github.com/maybelinot/df2gspread>`__ for this great
description of how to get the client credentials.

You can read more about it in the `configuration docs <https://gspread-pandas.readthedocs.io/en/latest/>`__
including how to change the default behavior.

Example
=======

.. code:: python

    from __future__ import print_function
    import pandas as pd
    from gspread_pandas import Spread, Client

    file_name = "http://stats.idre.ucla.edu/stat/data/binary.csv"
    df = pd.read_csv(file_name)

    # 'Example Spreadsheet' needs to already exist and your user must have access to it
    spread = Spread('Example Spreadsheet')
    # This will ask to authenticate if you haven't done so before

    # Display available worksheets
    spread.sheets

    # Save DataFrame to worksheet 'New Test Sheet', create it first if it doesn't exist
    spread.df_to_sheet(df, index=False, sheet='New Test Sheet', start='A2', replace=True)
    spread.update_cells('A1', 'A1', ['Created by:', spread.email])
    print(spread)
    # <gspread_pandas.client.Spread - User: '<example_user>@gmail.com', Spread: 'Example Spreadsheet', Sheet: 'New Test Sheet'>

    # You can now first instanciate a Client separately and query folders and
    # instanciate other Spread objects by passing in the Client
    client = Client()
    # Assumming you have a dir called 'example dir' with sheets in it
    available_sheets = client.find_spreadsheet_files_in_folders('example dir')
    spreads = []
    for sheet in available_sheets.get('example dir', []):
        spreads.append(Spread(sheet['id'], client=client))

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
