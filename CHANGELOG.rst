Change Log
==========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`_
and this project adheres to `Semantic Versioning <http://semver.org/>`_.

[Unreleased]
------------

Added
-----

-  Test python 3.7, Windows, and MacOS
-  You can now iterate over worksheets like: ``for sheet in spread``
-  ``Spread.df_to_sheet`` can now flatten multi-level headers using the
   ``flatten_headers_sep`` param
-  Add ability to set permissions on spreadsheets
-  Add ability to create and move folders and spreadsheets
-  A session can now be passed directly to a ``Client``

Removed
-------

-  BREAKING: Removed ``start/end_row/col`` params from add_filter
-  BREAKING: Removed ``user_creds_or_client`` param from Spread
-  BREAKING: Removed ``user_or_creds`` param from Client

Changed
-------

-  The ``credentials`` param is now called ``creds`` everywhere
-  Test suite is now a lot more robust
-  Use google-auth instead of the now deprecated oauth2client library.
   This moves the retry code into that library.
-  Default config will now be in ``C:\Users\<user>\AppData\gspread_pandas``
   on Windows


Fixed
-----

-  Things should now work when passing a ``Worksheet`` object to ``Spread.open``


[1.3.1] - 2019-05-17
-----------------------------

Fixed
~~~~~

-  Passing 0 to ``sheet``` param in any function should work now
-  When using multi-row column headers in a spreadsheet, the index name
   should now be better identified
-  Spread;update_cells should now work when passing a single cell value
-  When start != 'A1', freeze_rows/headers should now correctly freeze
   the right amount of rows/headers so the index and columns are frozen

[1.3.0] - 2019-04-30
-----------------------------

Added
~~~~~

-  Function to merge_cells
-  Function to unmerge_cells
-  Option to merge_headers in df_to_sheet
-  Retry when exceeding the 100s quota

Fixed
~~~~~

-  Fix passing 0 for freeze_index or freeze_headers. This essentially
   "unfreezes"
-  When the index has no name and you have a multi-level header, it will
   no longer fill in "index" as the index header

Deprecated
~~~~~~~~~~

-  Spread will no longer use the 'user_creds_or_client' param in v2. Instead, it
   will have optional 'credentials', 'client', and 'user' params. If creds or a
   client are passed, the user will be ignored. Otherwise, it'll use the user,
   which will default to "default"
-  Client will no longer use the 'user_or_creds' param in v2. Instead, it
   will have optional 'credentials' and 'user' params. If creds passed, the user
   will be ignored. Otherwise, it'll use the user, which will default to "default"
-  Spread.add_filter will be standardized to use 'start' and 'end' like other
   functions and the start/end_row/col are deprecated and will be removed in v2

Changed
~~~~~~~

-  Exceptions are no longer raised while handling another exception. This should
   prevent the "During handling of the above exception, another exception occurred"
   message
-  When opening a new Spreadsheet, the SpreadsheetNotFound exception will no longer
   be a "catchall" for any errors. If an error other than actually not finding the
   Spreadsheet occurs, it'll be raised.
-  Default value for the user param in util.get_config was changed to "default"

[1.2.2] - 2019-04-15
-----------------------------

Fixed
~~~~~

-  Fix passing only one of freeze_index or freeze_headers = True

[1.2.1] - 2018-08-30
-----------------------------

Fixed
~~~~~

-  Fixed __version__ string for bumpversion using black

[1.2.0] - 2018-08-30
-----------------------------

Added
~~~~~

-  Add config files and pre-commit hooks for isort, black, and flake8
-  Add config files for isort, black, and flake8

Fixed
~~~~~

-  Fixed clear_sheet when there are frozen rows/cols
-  Small fixes in README

Changed
~~~~~~~

-  Changed from reST docstrings to numpy docstrings
-  Updated README to include more in contributing section

[1.1.3] - 2018-07-07
-----------------------------

Added
~~~~~

-  Added unit tests for util

Fixed
~~~~~

-  Fix parse_df_col_names when df has a multi-index
-  Fix parse_sheet_index when using last column as index
-  Fix fillna when using categorical variables

[1.1.2] - 2018-06-23
-----------------------------

Fixed
~~~~~

-  Fix issue with basestring usage

Changed
~~~~~~~

-  Remove Python 3.4 from travis tests

[1.1.1] - 2018-06-13
-----------------------------

Changed
~~~~~~~

-  ``Spread.clear_sheet`` now doesn't resize to 0 since V4 is much more efficient at making batch updates. This should help prevent formulas that point to these sheets from breaking.

[1.1.0] - 2018-06-02
-----------------------------

Fixed
~~~~~

-  Now works with gspread 3.0
-  Spread.freeze is working again

Changed
~~~~~~~

-  Moved a lot of the credential handling into functions in gspread_pandas.conf
-  New ``get_creds`` function allows you to get ``OAuth2Credentials`` and pass them in to a ``Client`` or ``Spread``
-  Some functions were moved to ``gspread_pandas.util``

Added
~~~~~

-  New function ``Spread.add_filter`` created so that you can add filters to worksheets
-  New param ``add_filter`` added to ``Spread.df_to_sheet`` to add a filter to uploaded data

[1.0.5] - 2018-04-14
-----------------------------

Fixed
~~~~~

-  Added limit to gspread version since 3.0 broke gspread-pandas

[1.0.4] - 2018-04-08
-----------------------------

Fixed
~~~~~

-  Change ValueInputOption to USER_ENTERED so dates and numbers are parsed correctly in Google Sheets

[1.0.3] - 2018-04-02
-----------------------------

Added
~~~~~

-  Basic initial test

[1.0.2] - 2018-04-02
-----------------------------

Changed
~~~~~~~

-  Some dependency changes
-  Travis deploy will only happen on python 3.6
-  Changes to reduce number of fetch_sheet_metadata calls

[1.0.1] - 2018-03-26
-----------------------------

Changed
~~~~~~~

-  Replace pypi-publisher with twine in dev reqs
-  Change download url, now it should match the tags from bumpversion

[1.0.0] - 2018-03-26
-----------------------------

Added
~~~~~

-  There is now a separate ``Client`` class that extends the gspread v4 Client class and adds some functionalty. This includes a monkeypatche and hacky workarounds for gspread 2.0 issues. Once they get fixed upstream I need to remove these.

Changed
~~~~~~~

-  Now supports gspread 2.0 which uses Spreadsheets V4 API, this provides much better performance and reliability. Some APIs might have changed.
-  No longer need to chunk update requests, and range requests can use larger chunks
-  Some code improvements enabled by gspread 2.0
-  Removed deprecated params and functions

[0.16.1] - 2018-03-24
-----------------------------

Fixed
~~~~~

-  Set up correct credentials for travis pypi push

[0.16.0] - 2018-03-24
-----------------------------

Added
~~~~~

-  Test on multiple versions using tox
-  Enable travis-ci

Fixed
~~~~~

-  Remove dir accidentally pushed by build

Changed
~~~~~~~

-  Moved dev requirements into requirements_dev.txt
-  Now using bumpversion for version management
-  Minor updates to README
-  Documentation now at Read The Docs
-  Minor code changes to please flake8
-  Deleted update_pypi.sh as releases are now handled by travis

[0.15.6] - 2018-03-12
-----------------------------

Fixed
~~~~~

-  Remove code accidentally pushed by build

[0.15.5] - 2018-03-12
-----------------------------

Fixed
~~~~~

-  Added dependency version limit for gspread; will remove in next version

[0.15.4] - 2018-02-13
-----------------------------

Fixed
~~~~~

-  README example now points to the correct URL (thanks @lionel)
-  Calling parse_sheet_headers on an empty sheet doesn't break anymore (thanks @taewookim)

Added
~~~~~

-  You can now use service account credentials in the config (thanks @marcojetson)

[0.15.3] - 2017-11-21
-----------------------------

Changed
~~~~~~~

-  Always return an Index object from parse_sheet_headers

[0.15.2] - 2017-11-18
-----------------------------

Fixed
~~~~~

-  Fix sheet_to_df when headers are present with no data

Changed
~~~~~~~

-  Minimum Pandas version .20 now required

[0.15.1] - 2017-10-05
-----------------------------

Fixed
~~~~~

-  When there are merged cells outside the data range, an exception is no longer
   thrown.
-  Cast keys() to a list to fix Python 3 compat

[0.15.0] - 2017-09-11
-----------------------------

Changed
~~~~~~~

-  Added ``fill_value`` option to df_to_sheet

Fixed
~~~~~

-  Different application type credentials can be used now
-  Some safeguards to prevent certain exceptions
-  df_to_sheet won't fail when categorical columns have nulls

[0.14.3] - 2017-06-22
-----------------------------

Changed
~~~~~~~

-  Force gspread sheets refresh when refreshing sheets
-  Worksheet object can now be passed it to most functions with ``sheet`` param

[0.14.2] - 2017-06-18
-----------------------------

Added
~~~~~

-  Added ``url`` property for easy linking

Fixed
~~~~~

-  Fixed retry for _retry_get_all_values

[0.14.1] - 2017-06-05
-----------------------------

Changed
-------

-  Ensure sheet matadata is refreshed after sheet changing activitiesthrough use of a
   decorator
-  Retry when calling ``get_all_values``
-  More robust way to get index when a new sheet is created

[0.14.0] - 2017-05-25
-----------------------------

Added
~~~~~

-  Added function to freeze rows/columns to ``Spread``
-  Added ``freeze_index`` and ``freeze_headers`` flags to ``df_to_sheet``

Changed
~~~~~~~

-  Don't re-size again when using ``replace=True``
-  Switch away from deprecated ``gspread`` functions
-  Make functions in ``util`` non-private

Fixed
~~~~~

-  Prevent error when index > number of columns in ``sheet_to_df``

[0.13.0] - 2017-04-28
-----------------------------

Added
~~~~~

-  Added ``create_spread`` and ``create_sheet`` params for ``Spread`` class. This enables
   creating a spreadsheet or a worksheet during opening. This will require re-authenticating
   in order to use it

[0.12.1] - 2017-04-25
-----------------------------

Changed
~~~~~~~

-  If using multi-level headings, heading will be shifted up so the top level
   is not a blank string
-  Some functions that don't depend on ``self`` were moved into ``util.py``
-  The ``headers`` param in ``sheet_to_df`` was deprecated in favor of ``header_rows``

Fixed
~~~~~

-  I introduced some small bugs with the v4 api changes when a sheet is not found,
   they now work as expected even when a new sheet is created
-  The list of sheets is now refreshed when one is deleted

[0.12.0] - 2017-03-31
-----------------------------

Added
~~~~~

-  Add Sheets API v4 client to ``self.clientv4``

Fixed
~~~~~

-  Merged cells now all get the right value in ``sheet_to_df``
-  You can now pass ``replace=True`` when a sheet has frozen rows/cols

[0.11.2] - 2017-03-22
-----------------------------

Changed
~~~~~~~

-  Minor change to README

[0.11.1] - 2017-03-22
-----------------------------

Added
~~~~~

-  Added note about ``EOFError`` when verifying Oauth in ``Rodeo``

Changed
~~~~~~~

-  Add retry method for ``sheet.range`` to work around 'Connection Broken' error

Fixed
~~~~~

-  Fixed clearing only rows with ``clear_sheet``

[0.11.0] - 2017-02-14
-----------------------------

Changed
~~~~~~~

-  Only clear up to first row in ``clear_sheet`` so that data filters will persist
-  Moved default config from ``~/.google/`` to ``~/.config/gspread_pandas``

Fixed
~~~~~

-  Allow passing index ``0`` to ``open``
-  Fixed changelog

[0.10.1] - 2017-01-26
-----------------------------

Added
~~~~~

-  Added troubleshooting for ``certifi`` issue in ``README``

Changed
~~~~~~~

-  Only catch ``SpreadsheetNotFound`` exceptions when opening a spreadsheet


[0.10.0] - 2017-01-18
-----------------------------

Added
~~~~~

-  Added optional ``create`` param to ``open_sheet`` to create it if it doesn't exist
-  Added optional ``start`` param to ``df_to_sheet``, will take tuple or address as str

Changed
~~~~~~~

-  Improved docs, changed to ``rst``
-  Made some variables private
-  Improved ``__str__`` output
-  Switch to using exceptions from ``gspread``
-  ``spread`` param is now required for ``open``
-  When current sheet is deleted, ``self.sheet`` is set to ``None``
-  Improved versioning, switched to `Semantic Versioning <http://semver.org/>`_

Fixed
~~~~~

-  Fixed chunk calculation in Python 3
-  Sheet names are case insensitive, fixed ``find_sheet``

Deprecated
~~~~~~~~~~

-  Deprecate ``open_or_create_sheet`` function in favor of ``create=True`` param
   for ``open_sheet``
-  Deprecate ``start_row`` and ``start_col`` in ``df_to_sheet`` in favor of ``start``
   param

[0.9] - 2016-12-07
-----------------------------

Added
~~~~~

-  Add ``__repr__`` and ``__str__`` to show the active
-  Add user's email as a property to Spread. I recommend deleting
   existing Oauth credentials and re-creating them with new permissions
-  Allow importing with: ``from gspread_pandas import Spread``
-  Added ``CHANGELOG.md``

Changed
~~~~~~~

-  Restrict scope to only necessary endpoints
-  Add retry for updating cells in case an error occurrs
-  Minor changes to ``README.md``

Fixed
~~~~~

-  Fixed the use of ``start_row`` > 1

[0.8] - 2016-11-11
-----------------------------

Added
~~~~~

-  Add python 3 build to ``update_pypi.sh`` script

Fixed
~~~~~

-  Oauth flow now uses correct properties

[0.7] - 2016-11-10
-----------------------------

Changed
~~~~~~~

-  Made python 3 compatible using future

[0.6] - 2016-10-27
-----------------------------

Changed
~~~~~~~

-  Change defaults in ``sheet_to_df`` to include index and header
-  Raise error when missing google client config file

[0.5] - 2016-10-19
-----------------------------

Changed
~~~~~~~

-  Improve decorators more using ``decorator.decorator``

[0.4] - 2016-10-19
-----------------------------

Added
~~~~~

-  Pypi update script

Changed
-------

-  Improve decorators using ``functools.wraps``

[0.3] - 2016-10-19
-----------------------------

Changed
~~~~~~~

-  Add ``ensure_auth`` decorator to most functions to re-auth if needed
-  Chunk requests to prevent timeouts
-  Improved ``clear_sheet`` by resizing instead of deleting and
   re-creating

[0.2] - 2016-10-12
-----------------------------

Added
~~~~~

-  Code migrated
-  Example usage in README
-  Add requirements

[0.1] - 2016-10-11
-----------------------------

Added
~~~~~

-  README
-  initial code migrated
