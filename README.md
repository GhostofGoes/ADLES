
[![Latest version on PyPI](https://badge.fury.io/py/ADLES.svg)](https://pypi.org/project/ADLES/)
[![Travis CI build status](https://travis-ci.org/GhostofGoes/ADLES.svg?branch=master)](https://travis-ci.org/GhostofGoes/ADLES)
[![Documentation](https://readthedocs.org/projects/adles/badge/)](http://adles.readthedocs.io/en/latest/)
[![DOI Reference](https://zenodo.org/badge/68841026.svg)](https://zenodo.org/badge/latestdoi/68841026)


# Overview
Automated Deployment of Lab Environments System (ADLES)

ADLES automates the deterministic creation of virtualized environments for use
in Cybersecurity and Information Technology (IT) education.

The system enables educators to easily build deterministic and portable
environments for their courses, saving significant amounts of time and effort,
and alieviates the requirement of possessing advanced IT knowledge.


Complete documentation can be found at [ReadTheDocs](https://adles.readthedocs.io).

[Publication describing the system.](https://doi.org/10.1016/j.cose.2017.12.007)


# Getting started
```bash
pip3 install adles
adles -h
adles --print-spec exercise
adles --print-spec infra
adles --list-examples
adles --print-example competition
```


# Usage
Creating an environment using ADLES:
* Read the exercise and infrastructure specifications and examples of them.
* Write an infrastructure specification for your platform. (Currently, VMware vSphere is the only platform supported)
* Write an exercise specification with the environment you want created.
* Check its syntax, run the mastering phase, make your changes, and then run the deployment phase.

```bash
adles -c my-competition.yaml
adles -m -s my-competition.yaml
adles -d -s my-competition.yaml
```


# System requirements

Python: 3.5+

ADLES will run on any platform supported by Python. It has been tested on:

* Windows 10 (Anniversary and Creators)
* Ubuntu 14.04 and 16.04 (Including Bash on Ubuntu on Windows)
* CentOS 7


## Python packages
See ``requirements.txt`` for specific versions
* pyvmomi
* docopt
* pyyaml
* colorlog
* setuptools (If you are installing manually or developing)
* pyvmomi (If you are using VMware vSphere)


## Platforms
**VMware vSphere**
* vCenter Server: 6.0+
* ESXi: 6.0+


# Contributing
Contributions are most definitely welcome! See ``TODO.md`` for a list of what needs to be done.
Before submitting a pull request, do ensure you follow the general style and conventions used.
Just read the code for a bit to get a feel for how things are done, and stay consistent with that.

If you have questions about the system, don't hesitate to contact me by email or Twitter.
(Email is in init.py, Twitter handle is same as GitHub).


# Goals and TODO
The overall goal of ADLES is to create a easy to use and rock-solid system that allows instructors
and students teaching using virtual environments to automate their workloads.

Long-term, I’d like to see the creation of a open-source repository, similiar to
Hashicorp’s Atlas and Docker’s Hub, where educators can share packages
and contribute to improving cyber education globally.


### Main things on the radar (see ``TODO.md`` for full list)

* User and group implementation for Vsphere
* Post-phase cleanups
* Result collection
* Provisioners
* Automated testing for utils and ideally Vsphere
* Working Docker platform implementation
* Implement a cloud platform interface, with Amazon AWS or Microsoft Azure being the easiest picks


# Contributing
Contributers are more than welcome!
See the [contribution guide](CONTRIBUTING.md) to get started,
and checkout the [todo list](TODO.md) for a full list of tasks and bugs.

The [Python Discord server](https://discord.gg/python) is a good place
to ask questions or discuss the project (Handle: @KnownError).

## Contributers
* Christopher Goes (ghostofgoes)
* Daniel Conte de Leon (dcontedeleon)


# License
This project is licensed under the Apache License, Version 2.0. See
LICENSE for the full license text, and NOTICES for attributions to
external projects that this project uses code from.


# Project History
The system began as a proof of concept implementation of my Master's thesis research at the
University of Idaho in Fall of 2016. It was originally designed to run on the RADICL lab.
