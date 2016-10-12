gspread-pandas
===============================

version number: 0.1
author: Diego Fernandez

Overview
--------

A package to easily open an instance of a Google spreadsheet and interact with worksheets through Pandas DataFrames.

When going to and from DataFrames, it can nicely handle headers and indexes.

Installation / Usage
--------------------

To install use pip:

    $ pip install gspread-pandas


Or clone the repo:

    $ git clone https://github.com/aiguofer/gspread-pandas.git
    $ python setup.py install

Get OAuth 2.0 client ID info from [Google](https://console.developers.google.com/apis/credentials) and download JSON as `~/.google/google_secret.json`

Contributing
------------

TBD

Example
-------

```
import pandas as pd
from gspread_pandas.client import Spread

file_name = "http://www.ats.ucla.edu/stat/data/binary.csv"
df = pd.read_csv(file_name)

# 'Example Spreadsheet' needs to already exist and your user must have access to it
spread = Spread('example_user', 'Example Spreadsheet')
# This will ask to authenticate if you haven't done so before for 'example_user'

# Display available worksheets
spread.sheets

# Save DataFrame to worksheet 'New Test Sheet', create it first if it doesn't exist
spread.df_to_sheet(df, index=False, sheet='New Test Sheet')
```
