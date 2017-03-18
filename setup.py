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

setup(
    name='ADLES',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=required,
    entry_points={
        'console_scripts': [
            'adles = adles.scripts.adles.py:__main__',
            'clone-vms = adles.scripts.clone_vms.py:__main__',
            'cleanup-vms = adles.scripts.cleanup_vms.py:__main__',
            'power-vms = adles.scripts.vm_power.py:__main__',
            'vsphere-info = adles.scripts.vsphere_info.py:__main__'
        ]
    },
    scripts=['adles/scripts/adles.py', 'adles/scripts/clone_vms.py',
             'adles/scripts/cleanup_vms.py',
             'adles/scripts/vm_power.py', 'adles/scripts/vsphere_info.py'],
    author=__author__,
    author_email=__email__,
    description='Automated Deployment of Lab Environments System',
    url=__url__,
    license=__license__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Education',
        'Topic :: Education :: Testing',
        'Topic :: Security',
        'Topic :: Software Development'
    ]
)
