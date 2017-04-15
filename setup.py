#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages
from adles import __version__, __email__, __author__, __url__, __license__


with open('requirements.txt') as f:
    required = f.read().splitlines()

with open('README.rst') as f:
    long_description = f.read()


setup(
    name='ADLES',
    version=__version__,
    packages=find_packages(exclude=['test']) + ['specifications', 'examples'],
    include_package_data=True,
    zip_safe=False,
    install_requires=required,
    entry_points={
        'console_scripts': [
            'adles = adles.scripts.adles_main:main',
            'clone-vms = adles.scripts.clone_vms:main',
            'cleanup-vms = adles.scripts.cleanup_vms:main',
            'vm-power = adles.scripts.vm_power:main',
            'vsphere-info = adles.scripts.vsphere_info:main'
        ]
    },
    author=__author__,
    author_email=__email__,
    description='Automated Deployment of Lab Environments System (ADLES)',
    long_description=long_description,
    url=__url__,
    download_url='https://pypi.python.org/pypi/ADLES',
    license=__license__,
    keywords="adles virtualization automation vmware vsphere yaml labs virtual vms python pyvmomi "
             "cybersecurity education uidaho radicl environments deployment docker lol 1337 setup",
    setup_requires=[
        "pytest-runner==2.11.1"
    ],
    tests_require=[
        "pytest==3.0.7",
        "pytest-cov==2.4.0"
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Education',
        'Topic :: Education :: Testing',
        'Topic :: Security',
        'Topic :: Software Development',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
        'Natural Language :: English'
    ]
)
