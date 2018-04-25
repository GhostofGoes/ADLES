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

import os
from setuptools import setup, find_packages


# Read in project metadata
about = {}
info_file = os.path.join(os.path.dirname(__file__), "adles", "__about__.py")
with open(info_file) as f:
    exec(f.read(), about)

# Loads in the README for PyPI
with open('README.rst') as f:
    long_description = f.read()


setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__email__'],
    description=about['__summary__'],
    long_description=long_description,  # This is what you see on PyPI page
    # TODO: convert README to markdown
    # long_description_content_type="text/markdown",
    url=about['__url__'],
    download_url='https://pypi.org/project/ADLES/',
    license=about['__license__'],
    entry_points={
        # These enable commandline usage of ADLES and the helper scripts
        'console_scripts': [
            'adles = adles.scripts.adles_main:main',
            'clone-vms = adles.scripts.clone_vms:main',
            'cleanup-vms = adles.scripts.cleanup_vms:main',
            'vm-power = adles.scripts.vm_power:main',
            'vsphere-info = adles.scripts.vsphere_info:main',
            'vm-snapshots = adles.scripts.vm_snapshots:main'
        ]
    },
    install_requires=[
        'pyyaml >= 3.12, < 4.0.0',   # Specification parsing
        'docopt == 0.6.2',  # Commandline argument parsing
        'argopt >= 0.4.0, < 5.0.0',  # argparse configured with docopt strings
        'colorlog >= 2.10, < 4.0.0',  # Colored commandline output using logging
        'tqdm == 4.19.6',  # Terminal progress bars

        'pyvmomi >= 6.5, < 7.0.0',  # TODO: move this into a extra?

        'ipaddress;python_version<"3.3"'  # Python 2.7 compatibility
    ],
    extras_require={
        'docker': ['docker >= 2.4.2'],
        'cloud': ['apache-libcloud >= 2.3.0']
    },
    data_files=[('man/man1', ['docs/adles.1'])],
    packages=find_packages(exclude=['test']) + ['specifications', 'examples'],
    include_package_data=True,
    zip_safe=False,
    test_suite='test',
    platforms=['Windows', 'Linux', 'Mac OS-X'],
    keywords="adles virtualization automation vmware vsphere yaml labs virtual "
             "vms vm python pyvmomi cybersecurity education uidaho radicl "
             "environments deployment docker libcloud setup cloud computing",
    classifiers=[  # Used by PyPI to classify the project and make it searchable
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Education',
        'Topic :: Education :: Testing',
        'Topic :: Security',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Installation/Setup',
        'Topic :: Utilities'
    ]
)
