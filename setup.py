# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup, find_packages

path = os.path.dirname(__file__)
sys.path.insert(0, path)

import dash
version = dash.version

f = open('README.md')
readme = f.read().strip()

f = open('LICENSE.md')
license = f.read().strip()

setup(
    name='dash',
    version=version,
    description='Dash, software configuration for artists',
    long_description=readme,
    author='Abstract Factory Ltd.',
    author_email='marcus@abstractfactory.com',
    url='https://github.com/abstractfactory/dash',
    license=license,
    packages=find_packages(),
    package_data={
        'dash': [
                 '*.pyw',
                 '*.css',
                 'bin/*.py'
                 'bin/*.pyw',
        ],
    },
    include_package_data=True,
)
