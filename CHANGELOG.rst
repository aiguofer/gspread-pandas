Change Log
==========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`_
and this project adheres to `Semantic Versioning <http://semver.org/>`_.

[Unreleased]
------------

Changed
~~~~~~~

-  Moved a lot of the credential handling into functions in gspread_pandas.conf
-  New ``get_creds`` function allows you to get ``OAuth2Credentials`` and pass them in to a ``Client`` or ``Spread``

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
