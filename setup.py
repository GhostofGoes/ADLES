#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

__version__ = "0.5.0"
__author__ = "Christopher Goes"
__email__ = "<goes8945@vandals.uidaho.edu>"


with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='radicl',
    version=__version__,
    packages=find_packages('automation'),
    author=__author__,
    author_email=_-__email__,
    description='Cybersecurity environment automation using formal specifications',
    url='https://github.com/GhostofGoes/cybersecurity-environment-automation',
    license='License :: OSI Approved :: Apache Software License',
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
