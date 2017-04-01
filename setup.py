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

import distutils

with open('requirements.txt') as f:
    required = f.read().splitlines()

class YapfCommand(distutils.cmd.Command):
    description = 'Format python files using yapf'
    user_options = []
    
    def initialize_options(self):
        pass
        
    def finalize_options(self):
        pass
        
    def run(self):
        import yapf
        yapf.main(['yapf', '--recursive', '--in-place'] +find_packages())

setup(
    name='ADLES',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
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
    scripts=['adles/scripts/adles_main.py', 'adles/scripts/clone_vms.py',
             'adles/scripts/cleanup_vms.py', 'adles/scripts/vm_power.py',
             'adles/scripts/vsphere_info.py'],
    author=__author__,
    author_email=__email__,
    description='Automated Deployment of Lab Environments System',
    url=__url__,
    license=__license__,
    keywords="adles virtualization automation vmware vsphere yaml "
             "cybersecurity education uidaho radicl environments",
    cmdclass={
        'yapf': YapfCommand
    },
    setup_requires=[
        "yapf==0.16.1"
    ],
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
