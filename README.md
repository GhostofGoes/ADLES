

# Overview 
[![Build Status](https://travis-ci.org/GhostofGoes/cybersecurity-environment-automation.svg?branch=master)](https://travis-ci.org/GhostofGoes/cybersecurity-environment-automation) 
[![Dependency Status](https://www.versioneye.com/user/projects/589eac206a7781003b24318b/badge.svg?style=flat-square)](https://www.versioneye.com/user/projects/589eac206a7781003b24318b)
[![Code Climate](https://codeclimate.com/github/GhostofGoes/cybersecurity-environment-automation/badges/gpa.svg)](https://codeclimate.com/github/GhostofGoes/cybersecurity-environment-automation)

Automated Deployment of Lab Environments System (ADLES). 

The ADLES system automates the creation of virtualized cybersecurity educational environments and testbeds using a portable package format and  YAML specifications. This provides allows educators to deterministically create secure environments that map to learning objectives without the need for advanced IT training and experience.

The system is a Proof of Concept implementation of my thesis research for a Master of Computer Science at the University of Idaho. I am implementing the overall system, the specifications, and the interface modules required to run on a VMware vSphere cluster. The short-term goal (other than graduating of course) is to create a system that allows instructors and students using the RADICL lab to automate their workloads. Long-term, I'd like to see the creation of a repository, similiar to Hashicorp's Atlas and Docker's Hub, where educators can share packages and contribute to the overall ability to conduct security and IT education globally.


# Installation

## Windows
```cmd

git clone https://github.com/GhostofGoes/ADLES.git
cd ADLES
pip install -r requirements.txt
python main.py --help
```

## Linux
```bash

git clone https://github.com/GhostofGoes/ADLES.git
cd ADLES
pip3 install -r requirements.txt
sudo chmod +x main.py
./main.py --help
```

# Getting started

* Poke through the examples folder and try running a few of them.
* Run `main.py --help` for usage information.
* See specification/environment-specification.yaml for the exercise specification, built on YAML 1.1.


# Building a portable package
There are several scripts to support importing the system into RADICL, which is isolated. Currently, there are build scripts for Windows (cmd) and Linux (Bash), and a install script for Linux (Bash).

The build scripts:

* Download the neccessary python modules and their dependancies from PyPI
* Package the system code and python modules into a ZIP file

The install scripts:

* Unzip the package
* Install the python modules


# System Requirements

### Software
Python: 3.4+

### Python Packages
See requirements.txt for specific versions
* pyvmomi 
* docopt
* pyyaml
* netaddr

### Virtualization Platforms
* vSphere >= 6.0
* ESXi >= 6.0 U2


# Licensing

This project is licensed under the Apache License, Version 2.0. See LICENSE for the full license text, and NOTICES for attributions to external projects that this project uses code from.
