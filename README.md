
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
and alleviates the requirement of possessing advanced IT knowledge.

Complete documentation can be found at [ReadTheDocs](https://adles.readthedocs.io).

[Publication describing the system.](https://doi.org/10.1016/j.cose.2017.12.007)

# Getting started
```bash
# Install
pip3 install adles

# Usage
adles -h

# Specification syntax
adles --print-spec exercise
adles --print-spec infra

# Examples
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
# Validate spec
adles validate my-competition.yaml

# Create Master images
adles masters my-competition.yaml

# Deploy the exercise
adles deploy my-competition.yaml

# Cleanup the environment
adles cleanup my-competition.yaml
```

## Complete usage
```bash
usage: adles [-h] [--version] [-v] [--syslog SERVER] [--no-color]
             [--list-examples] [--print-spec NAME] [--print-example NAME]
             [-i INFRA]
             {validate,deploy,masters,package,cleanup} ...

Examples:
    adles --list-examples
    adles --print-example competition | adles validate -
    adles validate examples/pentest-tutorial.yaml
    adles masters examples/experiment.yaml
    adles -v deploy examples/experiment.yaml
    adles cleanup -t masters --cleanup-nets examples/competition.yaml
    adles validate -t infra examples/infra.yaml

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v, --verbose         Emit debugging logs to terminal
  --syslog SERVER       Send logs to a Syslog server on port 514
  --no-color            Do not color terminal output
  -i INFRA, --infra INFRA
                        Override the infrastructure specification to be used

Print examples and specs:
  --list-examples       Prints the list of available example scenarios
  --print-spec NAME     Prints the named specification
  --print-example NAME  Prints the named example

ADLES Subcommands:
  {validate,deploy,masters,package,cleanup}
    validate            Validate the syntax of your specification
    deploy              Environment deployment phase of specification
    masters             Master creation phase of specification
    package             Create a package
    cleanup             Cleanup and remove existing environments
```

## vSphere Utility Scripts
There are a number of utility scripts to make certain vSphere tasks bearable.
```bash
usage: vsphere [-h] {cleanup,clone,power,info,snapshot} ...

Single-purpose CLI scripts for interacting with vSphere

optional arguments:
  -h, --help            show this help message and exit

vSphere scripts:
  {cleanup,clone,power,info,snapshot}
    cleanup             Cleanup and Destroy Virtual Machines (VMs) and VM
                        Folders in a vSphere environment.
    clone               Clone multiple Virtual Machines in vSphere.
    power               Power operations for Virtual Machines in vSphere.
    info                Query information about a vSphere environment and
                        objects within it.
    snapshot            Perform Snapshot operations on Virtual Machines in a
                        vSphere environment.
```

# System requirements

Python: 3.6+

ADLES will run on any platform supported by Python. It has been tested on:

* Windows 10 (Anniversary and Creators)
* Ubuntu 14.04 and 16.04 (Including Bash on Ubuntu on Windows)
* CentOS 7

## Python packages
See ``setup.py`` for specific versions
* pyyaml
* colorlog
* humanfriendly
* tqdm
* pyvmomi (If you are using VMware vSphere)
* setuptools (If you are installing manually or developing)

## Platforms
**VMware vSphere**
* vCenter Server: 6.0+
* ESXi: 6.0+

# Contributing
Contributors are more than welcome!
See the [contribution guide](CONTRIBUTING.md) to get started,
and checkout the [todo list](TODO.md) for a full list of tasks and bugs.

The [Python Discord server](https://discord.gg/python) is a good place
to ask questions or discuss the project (Handle: @KnownError).

## Contributors
* Christopher Goes (ghostofgoes)
* Daniel Conte de Leon (dcontedeleon)

# Goals and TODO
The overall goal of ADLES is to create a easy to use and rock-solid system that allows instructors
and students teaching using virtual environments to automate their workloads.

Long-term, I’d like to see the creation of a open-source repository, similar to
Hashicorp’s Atlas and Docker’s Hub, where educators can share packages
and contribute to improving cyber education globally.

Full list of TODOs are in `documentation/TODO.md` and the GitHub issues.

# License
This project is licensed under the Apache License, Version 2.0. See
LICENSE for the full license text, and NOTICES for attributions to
external projects that this project uses code from.

# Project History
The system began as a proof of concept implementation of my Master's thesis research at the
University of Idaho in Fall of 2016. It was originally designed to run on the RADICL lab.
