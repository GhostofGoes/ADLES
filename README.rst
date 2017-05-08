.. image:: https://badge.fury.io/py/ADLES.svg
   :target: https://badge.fury.io/py/ADLES
   :alt: PyPI Version
.. image:: https://travis-ci.org/GhostofGoes/ADLES.svg?branch=master
   :target: https://travis-ci.org/GhostofGoes/ADLES
   :alt: Build Status
.. image:: https://www.versioneye.com/user/projects/589eac206a7781003b24318b/badge.svg
   :target: https://www.versioneye.com/user/projects/589eac206a7781003b24318b
   :alt: Dependency Status
.. image:: https://codeclimate.com/github/GhostofGoes/ADLES/badges/gpa.svg
   :target: https://codeclimate.com/github/GhostofGoes/ADLES
   :alt: Code Climate
.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License

Overview
========

Automated Deployment of Lab Environments System (ADLES)

| ADLES automates the deterministic creation of virtualized environments for use in
  Cybersecurity and Information Technology (IT) education.
| The system enables educators to easily build deterministic and
  portable environments for their courses, saving significant amounts of
  time and effort, and alieviates the requirement of possessing advanced IT knowledge.


.. image:: documentation/system-overview-diagram.png
   :width: 40pt
   :align: center
   :alt: Overview of the system


Getting started
===============

.. code:: bash


   pip3 install adles
   adles -h
   adles --print-spec exercise
   adles --print-spec infra
   adles --list-examples
   adles --print-example competition


Usage
=====

How to use:

-  Read the exercise and infrastructure specifications and examples of them.
-  Write an infrastructure specification for your platform. (Currently, VMware vSphere is the only platform supported)
-  Write an exercise specification with the environment you want created.
-  Check its syntax, run the mastering phase, make your changes, and then run the deployment phase.

.. code:: bash


   adles -c my-competition.yaml
   adles -m -s my-competition.yaml
   adles -d -s my-competition.yaml


.. image:: documentation/usage-flowchart.png
   :width: 40pt
   :align: center
   :alt: Usage flowchart


System requirements
===================

**Python**:

-  3.4+     (Recommended)
-  2.7.6+   (Will be deprecated in the future)

ADLES will run on any platform supported by Python. It has been tested on:

-  Windows 10 (Anniversary and Creators)
-  Ubuntu 14.04 and 16.04 (Including Bash on Ubuntu on Windows)
-  CentOS 7


Python packages
~~~~~~~~~~~~~~~

See ``requirements.txt`` for specific versions

-  pyvmomi
-  docopt
-  pyyaml
-  netaddr
-  colorlog
-  setuptools (If you are installing manually or developing)


Platforms
~~~~~~~~~

**VMware vSphere**

-  vCenter Server: 6.0+
-  ESXi: 6.0+


**Docker**
|   Docker is currently in a pre-alpha development state. Eventually, the DockerInterface will
    support Docker Machine, Docker Compose, and potentially Docker Swarm.


Contributing
============

Contributions are most definitely welcome! See ``TODO.md`` for a list of what needs to be done.
Before submitting a pull request, do ensure you follow the general style and conventions used.
Just read the code for a bit to get a feel for how things are done, and stay consistent with that.


Goals and TODO
==============
The overall goal of ADLES is to create a easy to use and rock-solid system that allows instructors
and students teaching using virtual environments to automate their workloads.

Long-term, I’d like to see the creation of a open-source repository, similiar to
Hashicorp’s Atlas and Docker’s Hub, where educators can share packages
and contribute to improving cyber education globally.


Main things on the radar (see ``TODO.md`` for full list):

-  User and group implementation for Vsphere
-  Post-phase cleanups
-  Result collection
-  Provisioners
-  Automated testing for utils and ideally Vsphere
-  Working Docker platform implementation
-  Implement a cloud platform interface, with Amazon AWS or Microsoft Azure being the easiest picks


License
=======

This project is licensed under the Apache License, Version 2.0. See
LICENSE for the full license text, and NOTICES for attributions to
external projects that this project uses code from.


Project History
===============

The system began as a proof of concept implementation of my Master's thesis research at the
University of Idaho in Fall of 2016. It was originally designed to run on the RADICL lab.
