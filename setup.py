#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'A module containing base classes for creating console utilities',
    'author': 'Benjamin Bengfort', 
    'author_email': 'benjamin@bengfort.com',
    'version': '1.0.0',
    'install_requires': [],
    'packages': ['simpleconsole', 'simpleconsole.color', 'simpleconsole.utils'],
    'scripts': [],
    'name': 'console',
}

setup(**config)
