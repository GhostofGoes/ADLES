# Overview
[![Build Status](https://travis-ci.org/GhostofGoes/ADLES.svg?branch=master)](https://travis-ci.org/GhostofGoes/ADLES)
[![Dependency Status](https://www.versioneye.com/user/projects/589eac206a7781003b24318b/badge.svg?style=flat-square)](https://www.versioneye.com/user/projects/589eac206a7781003b24318b)
[![Code Climate](https://codeclimate.com/github/GhostofGoes/ADLES/badges/gpa.svg)](https://codeclimate.com/github/GhostofGoes/ADLES)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Automated Deployment of Lab Environments System (ADLES)

ADLES automates the creation of virtualized environments for the purpose of cybersecurity and IT education.
The system enables educators to easily build deterministic and portable environments for their courses, saving significant amounts of time and effort, and removes the need for advanced IT knowledge.

The system is a proof of concept implementation of my thesis research for a Master of Computer Science at the University of Idaho.


# Installation

## Windows
```cmd

git clone https://github.com/GhostofGoes/ADLES.git
cd ADLES
python setup.py install
adles -h
```

## Linux
```bash

git clone https://github.com/GhostofGoes/ADLES.git
cd ./ADLES
sudo chmod +x setup.py
sudo python3 ./setup.py install
adles -h
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

## Software
Python: 3.3+ (2.7 is untested, but should work)

### Python Packages
See requirements.txt for specific versions
* pyvmomi 
* docopt
* pyyaml
* netaddr
* colorlog

## Virtualization Platform

### VMware vSphere
* vSphere >= 6.0
* ESXi >= 6.0 (May work with 5.5, your mileage may vary)


# Project Goals

The short-term goal (other than graduating of course) is to create a system that allows instructors and students using the RADICL lab to automate their workloads.
Long-term, I'd like to see the creation of a repository, similiar to Hashicorp's Atlas and Docker's Hub, where educators can share packages and contribute to the overall ability to conduct security and IT education globally.

## Current Goals
In order to graduate on time, I am focusing on implementing the following components:

* Overall system
  * Interface module system
  * Specification injestion, parsing, and semantic checking
  * Master-creation phase
  * Deployment phase
  * Post-phase cleanups
  * User interface, logging, and basic result collection
* Specifications
  * Environment specification (The core spec that defines the environment)
  * Package specification
  * Infrastructure specification
* VMware vSphere Interface module
* Documentation of API, system, and examples
* Basic unit and functional tests
* Packaging for PyPI and Linux

## Future Goals

* Interfaces
  * Docker (Good for simulating large environments with low resource cost, very fast, very deterministic)
  * Hyper-V server (Free, good for schools that are heavily invested in the Microsoft ecosystem)
  * Vagrant (This enables interaction with VirtualBox, desktop Hyper-V, and VMware Workstation)
  * Xen (Rich introspection possibilities for monitoring extensions using Xen API)
  * KVM (LibVMI provides rich introspecition possibilities for this as well)
* Environment specification
  * Monitoring extensions
  * Resource extensions for testbeds (ICS/SCADA, Wireless, USB devices, car computers, etc.)
  * Lab connectors
* Vagrant image with a pre-configured VM running the system
* Windows installer for the system
* Public repository of packages
* More example packages
* Improved documentation on how to make a package, how to run the system, etc.


# License

This project is licensed under the Apache License, Version 2.0. See LICENSE for the full license text, and NOTICES for attributions to external projects that this project uses code from.
