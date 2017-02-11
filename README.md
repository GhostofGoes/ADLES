

# Introduction [![Build Status](https://travis-ci.org/GhostofGoes/cybersecurity-environment-automation.svg?branch=master)](https://travis-ci.org/GhostofGoes/cybersecurity-environment-automation)

Automating the creation of virtualized cybersecurity educational environments and testbeds using a formal specification.

This is the Proof of Concept implementation of my thesis research for a Master of Computer Science at the University of Idaho.


# Installation

```
git clone https://github.com/GhostofGoes/thesis-research.git
cd thesis-research
pip3 install -r requirements.txt
./main.py --help
```


# Getting started

Poke through the examples folder and try running a few of them. Use --help on main.py for usage information.
See specification/specification.yaml for the exercise specification, built on YAML 1.1.


# System Requirements

## Local system
* Python 3.6

## Platform
* vSphere >= 6.0
* ESXi >= 6.0 U2


# Tested Platforms

* Windows 10 Anniversary x64
* Debian 7
* vSphere 6.5
* ESXi 6.5
* CPython 3.3, 3.4, 3.5, 3.6
    

# Licensing

This project is licensed under the Apache License, Version 2.0. See LICENSE for the full license text, and NOTICES for attributions to external projects that this project uses code from.
