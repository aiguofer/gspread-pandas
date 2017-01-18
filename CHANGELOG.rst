Change Log
==========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`_
and this project adheres to `Semantic Versioning <http://semver.org/>`_.

[Unreleased]
------------

[0.10.0] - 2017-01-18
---------------------

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
------------------

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
------------------

Added
~~~~~

-  Add python 3 build to ``update_pypi.sh`` script

Fixed
~~~~~

-  Oauth flow now uses correct properties

[0.7] - 2016-11-10
------------------

Changed
~~~~~~~

-  Made python 3 compatible using future

[0.6] - 2016-10-27
------------------

Changed
~~~~~~~

-  Change defaults in ``sheet_to_df`` to include index and header
-  Raise error when missing google client config file

[0.5] - 2016-10-19
------------------

Changed
~~~~~~~

-  Improve decorators more using ``decorator.decorator``

[0.4] - 2016-10-19
------------------

Added
~~~~~

-  Pypi update script

Changed
-------

-  Improve decorators using ``functools.wraps``

[0.3] - 2016-10-19
------------------

Changed
~~~~~~~

-  Add ``ensure_auth`` decorator to most functions to re-auth if needed
-  Chunk requests to prevent timeouts
-  Improved ``clear_sheet`` by resizing instead of deleting and
   re-creating

[0.2] - 2016-10-12
------------------

Added
~~~~~

-  Code migrated
-  Example usage in README
-  Add requirements

[0.1] - 2016-10-11
------------------

Added
~~~~~

-  README
-  initial code migrated