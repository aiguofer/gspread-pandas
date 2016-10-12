from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = '0.2'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs
                    if x.startswith('git+')]

setup(
    name='gspread-pandas',
    version=__version__,
    description='A package to easily open an instance of a Google spreadsheet and interact with worksheets through Pandas DataFrames.',
    long_description=long_description,
    url='https://github.com/aiguofer/gspread-pandas',
    download_url='https://github.com/aiguofer/gspread-pandas/tarball/' +
    __version__,
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='gspread pandas google spreadsheets',
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    author='Diego Fernandez',
    install_requires=install_requires,
    extras_require={
        'dev': [
            'sphinx',
            'sphinx_rtd_theme',
            'nose',
            'coverage',
            'pypi-publisher'
        ]
    },
    dependency_links=dependency_links,
    author_email='aiguo.fernandez@gmail.com')
