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

| ADLES automates the creation of virtualized environments for the
  purpose of cybersecurity and IT education.
| The system enables educators to easily build deterministic and
  portable environments for their courses, saving significant amounts of
  time and effort, and alieviates the requirement of possessing advanced IT knowledge.

The system is a proof of concept implementation of my thesis research
as part of the requirements for a Master of Computer Science at the University of Idaho.


Getting started
===============

.. code:: bash


   pip3 install adles
   adles -h


-  Read some of the examples, and try running a fews
-  Read the exercise specification at specifications/exercise-specification.yaml
-  Try writing your own! You can check it's syntax using ``adles -c example.yaml``


System Requirements
===================

Client Software
---------------

**Python**: 2.7+, 3.4, 3.5, 3.6 (Reccomended)


Python Packages
~~~~~~~~~~~~~~~

See ``requirements.txt`` for specific versions

-  pyvmomi
-  docopt
-  pyyaml
-  netaddr
-  colorlog
-  setuptools (If you are installing manually or developing)

Virtualization Platforms
------------------------

VMware vSphere
~~~~~~~~~~~~~~

-  **vSphere** >= 6.0
-  **ESXi** >= 6.0

vSphere/ESXi 5.5 should work as well, but is untested.


Project Goals
=============

| The short-term goal is to create a system that allows instructors and students
  teaching using virtual environments to automate their workloads.
| Long-term, I’d like to see the creation of a open-source repository, similiar to
  Hashicorp’s Atlas and Docker’s Hub, where educators can share packages
  and contribute to improving cyber education globally.

Current Goals
-------------

Currently, I am focusing on implementing the following components:

-  Overall system

   -  Interface module system
   -  Specification injestion, parsing, and semantic checking
   -  Master-creation phase
   -  Deployment phase
   -  Post-phase cleanups
   -  User interface, logging, and basic result collection

-  Specifications

   -  Exercise specification (The core spec that defines the exercise environment)
   -  Package specification
   -  Infrastructure specification

-  VMware vSphere Interface module
-  Documentation of API, system, and examples
-  Basic Unit and Functional tests
-  Packaging for PyPI

Future Goals
------------

-  Interfaces

   -  Docker (Good for simulating large environments, with low resource overhead and quick load times)
   -  Hyper-V server (Free, good for schools that are heavily invested in the Microsoft ecosystem)
   -  Vagrant (Enables interaction with VirtualBox, desktop Hyper-V, and VMware Workstation)
   -  Xen (Rich introspection possibilities for monitoring extensions using the Xen API)
   -  KVM (LibVMI provides rich introspecition possibilities for this as well)

-  Environment specification

   -  Monitoring extensions
   -  Resource extensions for testbeds (ICS/SCADA, Wireless, USB devices, car computers, etc.)
   -  Lab connectors

-  Vagrantfile that builds a lightweight VM running the system
-  Dockerfile that builds a lightweight image running the system
-  Public repository of packages
-  More example tutorials
-  Improved documentation on how to make a package, how to setup a platform for system, etc.


License
=======

This project is licensed under the Apache License, Version 2.0. See
LICENSE for the full license text, and NOTICES for attributions to
external projects that this project uses code from.


