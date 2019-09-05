---
layout: default
---

# What is ADLES?

ADLES is a tool that automates the creation of system environments for educational purposes. 
The goal of the system is to enable educators to easily build environments for their courses, 
without the need for a specific platform or advanced IT knowledge.


Complete documentation can be found at ReadTheDocs: [adles.readthedocs.io](https://adles.readthedocs.io)

Publication describing the system: [doi.org](https://doi.org/10.1016/j.cose.2017.12.007)


## Getting started

```bash
pip3 install adles
adles -h
adles --print-spec exercise
adles --print-spec infra
adles --list-examples
adles --print-example competition
```


## Usage
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


## Requirements

Python: 3.5+

ADLES will run on any platform supported by Python. It has been tested on:

* Windows 10 (Anniversary and Creators)
* Ubuntu 14.04 and 16.04 (Including Bash on Ubuntu on Windows)
* CentOS 7


### VM requirements

**VMware vSphere**

* vCenter Server: 6.0+
* ESXi: 6.0+


# License
This project is licensed under the Apache License, Version 2.0. See
LICENSE for the full license text, and NOTICES for attributions to
external projects that this project uses code from.


# Project History

The system began as a proof of concept implementation of my Master's thesis research at the
University of Idaho in Fall of 2016. It was originally designed to run on the RADICL lab.
