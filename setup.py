#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from adles import __version__, __email__, __author__, __url__, __license__

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='adles',
    version=__version__,
    packages=find_packages('adles'),
    author=__author__,
    author_email=__email__,
    description='Automated Deployment of Lab Environments System',
    url=__url__,
    license=__license__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        'Topic :: Education',
        'Topic :: Education :: Testing',
        'Topic :: Security'
    ],
    install_requires=required,
    scripts=['main.py']
)
