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


Getting started
===============

.. code:: bash


   pip3 install adles
   adles -h


-  Read some of the examples, and try running a fews
-  Read the exercise specification at specifications/exercise-specification.yaml
-  Try writing your own! You can check it's syntax using ``adles -c example.yaml``


System requirements
===================

Client software
---------------

**Python**: 3.4+ (Recommended), 2.7.6+


Note on 2.7: While efforts have been made to maintain backward compatibility, Python 2.7 will be deprecated in
the future when full multi-lingual support and asyncronous operations are implemented. Therefore,
it is reccomended that Python 3 is used unless absolutely neccessary. (e.g CentOS 6)


Python packages
~~~~~~~~~~~~~~~

See ``requirements.txt`` for specific versions

-  pyvmomi
-  docopt
-  pyyaml
-  netaddr
-  colorlog
-  setuptools (If you are installing manually or developing)

Virtualization platforms
------------------------

VMware vSphere
~~~~~~~~~~~~~~

-  **vSphere** >= 6.0
-  **ESXi** >= 6.0

vSphere/ESXi 5.5 should work as well, but is untested.

Docker
~~~~~~

Docker is currently in a pre-alpha development state. Eventually, the DockerInterface will
support Docker Machine, Docker Compose, and potentially Docker Swarm.


Current goals
=============
The short-term goal is to create a system that allows instructors and students
teaching using virtual environments to automate their workloads.

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
-  Documentation of the system as a whole and its component APIs
-  Providing a number of examples of how to use the specifications in practice
-  Basic Unit and Functional tests
-  Packaging for PyPI


Future goals
============

Long-term, I’d like to see the creation of a open-source repository, similiar to
Hashicorp’s Atlas and Docker’s Hub, where educators can share packages
and contribute to improving cyber education globally.


Support for additional platforms
--------------------------------

-  Docker: good for simulating large environments, with low resource overhead and quick load times

   -  Docker Machine
   -  Docker Compose
   -  Docker Swarm

-  Hyper-V server: free academic license, good for schools invested in the Microsoft ecosystem
-  Vagrant: brings the platform to workstations and personal machines. Enables interaction with
   VirtualBox, desktop Hyper-V, and VMware Workstation
-  Xen: free and open-source, scalable, robust. Rich introspection possibilities for monitoring
   extensions using the Xen API
-  KVM: free and open-source, good for schools with a strong Linux background.
   LibVMI provides rich introspection possibilities here as well.
-  Various cloud platforms, such as Microsoft Azure, Amazon AWS, Google Cloud Platform,
   or DigitalOcean. Clouds are dynamic, scalable, and cost only for the time utilized,
   making them perfect for short-lived tutorials or competitions.


Specification extensions
------------------------

-  Monitoring extensions. This extension would add data collection configurations to relevant
   areas of the specifications, enabling the implementation of high-fidelity data collection. This
   would greatly enhance the system's research applicability, and enable other extensions such as
   fully automated grading of results, visualizations, and data analytics. Some examples of these
   configurations are:

   -  Secondary interfaces on services for aggregating their log data, such as Windows Event Logs,
      Unix Syslog, application logs, etc.
   -  Network packet captures. These could be obtained by enabling promiscuous mode on a vSwitch, or
      enabling a SPAN monitoring port to aggregate the network traffic.
   -  Configuration of a centralized logging server to collect data, such as Splunk or ELK, including
      specifying how the data aggregated should be "frozen" for inclusion with a package.
   -  Configuration of Virtual Machine Introspection (VMI) on supported platforms for a high-fidelity
      view of exercises during execution.
   -  Instrumentation of the platforms and aggregation of the resulting log data, including the logs
      created by ADLES itself.

-  Further Resource extensions for cyber-physical testbeds, and integration of Resources into more
   aspects of the exercise and package specifications. Examples of resources include testbeds for:
   ICS/SCADA, Wireless, USB devices, and car computers.
-  Addition of ability to federate connections between separate lab environments, enabling the
   sharing of testbed resources, virtualization infrastructure, and collaboration between
   educational institutions. This could be implemented by extending the current Resources section
   or the addition of a new section.
-  Visualization of an exercise in progress, notably for competitive environments.
-  Extension of the Groups section in the exercise specification with explicit specification
   of user roles and permissions.
-  Fully integrate and flesh out the role of exercise materials and other aspects of the Package
   specification.
-  Specification of system resources required for a service, e.g CPU, RAM, storage space.
-  Collaboration and communications for an exercise, e.g video conferencing, TeamSpeak,
   IRC channel, Discord server.
-  Flag for selective toggling of parts of specifications where it would be useful to do
   so without having to remove or comment out the content, e.g a folder.


System improvements
-------------------

-  Improved documentation on how to make a package, how to setup a platform for system, etc.
-  Finish vSphere implementation (Users and Permissions)
-  Redo the syntax verification component. Currently, any changes in spec involve a non-trivial
   number of changes to the source code of the component. This is brittle and makes verifying new
   extensions difficult, as most implementers will not bother in updating the component with the
   new syntax of their extensions.

   - Swagger is a possible solution, as it enables automatic generation of APIs from a spec
   - Implement verification of syntax for:

      -  Non-vSphere platforms
      -  Package specification
      -  JSON files containing user information and platform logins
      -  Scoring criteria and other related files

-  Two-way transformation. Scan an existing environment and generate the specification for it.
-  Graphical user interface. Ideally, this would be web-based for portability. In the short term,
   this could be accomplished with a minimal amount of work using the EasyGUI Python module.
-  Visualization of what the network and service structure of a given exercise or package
   specification will look like without actually building the environment, including any
   cyber-physical testbeds, connected labs, and monitoring components if their corresponding
   extensions are implemented.
-  Ability to pause/freeze an in-progress exercise, ideally as a simple commandline argument.
-  Public repository of packages.
-  More examples:

   -  Examples of other types of competitions, notably CTFs
   -  Experiment examples
   -  Greater variety of tutorials

-  Simplify system setup for educators beyond what a Python package provides

   -  Vagrantfile that builds a lightweight VM running the system
   -  Dockerfile that builds a lightweight Docker image running the system



License
=======

This project is licensed under the Apache License, Version 2.0. See
LICENSE for the full license text, and NOTICES for attributions to
external projects that this project uses code from.


Project History
===============

The system began as a proof of concept implementation of my Master's thesis research at the
University of Idaho in Fall of 2016. It was originally designed to run on the RADICL lab.
