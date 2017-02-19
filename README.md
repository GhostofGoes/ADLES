

# Overview 
[![Build Status](https://travis-ci.org/GhostofGoes/cybersecurity-environment-automation.svg?branch=master)](https://travis-ci.org/GhostofGoes/cybersecurity-environment-automation) 
[![Dependency Status](https://www.versioneye.com/user/projects/589eac206a7781003b24318b/badge.svg?style=flat-square)](https://www.versioneye.com/user/projects/589eac206a7781003b24318b)
[![Code Climate](https://codeclimate.com/github/GhostofGoes/cybersecurity-environment-automation/badges/gpa.svg)](https://codeclimate.com/github/GhostofGoes/cybersecurity-environment-automation)

Automating the creation of virtualized cybersecurity educational environments and testbeds using a formal specification.

This is the Proof of Concept implementation of my thesis research for a Master of Computer Science at the University of Idaho.


# Installation

## Windows
```cmd
git clone https://github.com/GhostofGoes/cybersecurity-environment-automation.git
cd cybersecurity-environment-automation
pip install -r requirements.txt
python main.py --help
```

## Linux
```bash
git clone https://github.com/GhostofGoes/cybersecurity-environment-automation.git
cd cybersecurity-environment-automation
pip3 install -r requirements.txt
sudo chmod +x main.py
./main.py --help
```

## Just the RADICL scripts
```
git clone https://github.com/GhostofGoes/cybersecurity-environment-automation.git
cd cybersecurity-environment-automation/automation/radicl-scripts/
pip install -r radicl-requirements.txt
python clone_vms.py --help
```


# Getting started

* Poke through the examples folder and try running a few of them.
* Run `main.py --help` for usage information.
* See specification/environment-specification.yaml for the exercise specification, built on YAML 1.1.


# System Requirements

### Software
Python: 3.2+

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
