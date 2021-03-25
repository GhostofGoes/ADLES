#!/usr/bin/env python3

import os

from setuptools import find_packages, setup

# Read in project metadata
about = {}
info_file = os.path.join(os.path.dirname(__file__), "adles", "__about__.py")
with open(info_file, encoding='utf-8') as f:
    exec(f.read(), about)  # nosec

# Build the page that will be displayed on PyPI from the README and CHANGELOG
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()
long_description += '\n\n'
with open('CHANGELOG.md', encoding='utf-8') as f:
    long_description += f.read()

install_requires = [
    'pyyaml == 5.4',   # Specification parsing
    'colorlog == 3.1.4',  # Colored commandline output using logging
    'tqdm == 4.19.6',  # Terminal progress bars
    'humanfriendly >= 4.12.1, < 5',  # User interface tools

    'pyvmomi >= 6.5, < 7.0.0',  # TODO: move this into a extra?
]

extras_require = {
    'docker': ['docker >= 2.4.2'],
    'cloud': ['apache-libcloud >= 2.3.0'],
}

data_files = [
    ('man/man1', ['docs/adles.1']),  # Man page
]

entry_points = {
    # These enable commandline usage of ADLES and the helper scripts
    'console_scripts': [
        'adles = adles.__main__:run_cli',
        'vsphere = adles.vsphere.__main__:main',
    ]
}

setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__email__'],
    description=about['__summary__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=about['__url__'],
    project_urls=about['__urls__'],
    license=about['__license__'],
    entry_points=entry_points,
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires='>=3.6',
    data_files=data_files,
    packages=find_packages(exclude=['test']) + ['specifications', 'examples'],
    include_package_data=True,
    zip_safe=False,
    keywords=[
        'virtualization', 'vmware', 'vsphere',
        'cybersecurity', 'education', 'radicl',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',

        'Operating System :: OS Independent',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: MacOS',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',

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
        'Topic :: Utilities',
    ]
)
