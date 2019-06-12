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

Testing
-------

Our tests levarage `betamax <https://github.com/betamaxpy/betamax>`__ to remember HTTP
interactions with the API. In order to add new tests that change the requests to
betamax, you'll need to have Service Account credentials stored as ``google_secret.json``
in the root project directory. You can then re-record tests by deleting the necessary
cassetes in ``tests/cassettes`` then running:

.. code-block:: console

     $ GSPREAD_RECORD=true pytest <path_to_test>

NOTE: Currently, the tests don't do any setup and teardown of expected directories/files
in the Google Drive. My main concern in implementing this is that somehow it might
mistakenly use a specific user's credentials and delete important stuff. If you have
any ideas here I'd be happy to discuss.

Versions
--------

In order to bump versions, we use `bumpversion <https://github.com/peritus/bumpversion>`__.
This will take care of adding an entry in the CHANGELOG for the new version and bumping
the version everywhere it needs to. This will also create a git tag for the specific
version.


CI
---

Tests will run on Travis CI using Tox, and they'll test on a variety of Python versions
on Linux, and test only latest Python on Mac and Windows. If a version tag is pushed and
the tests pass, the new version will be pushed to PyPi by Travis.
