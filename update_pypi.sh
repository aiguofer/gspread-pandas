#!/bin/sh

python setup.py sdist upload
python setup.py bdist_egg upload
python3 setup.py bdist_egg upload
