#!/bin/sh

python setup.py sdist upload
python setup.py bdist_egg upload
