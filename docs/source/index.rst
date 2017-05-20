
*******************************************************
Automated Deployment of Lab Environments System (ADLES)
*******************************************************

ADLES automates the deterministic creation of virtualized environments for use in Cybersecurity and Information Technology (IT) education.


Installation
============
.. code:: bash

   pip install adles


Getting started
===============


.. code:: bash


   adles -h
   adles --print-spec exercise
   adles --print-spec infra
   adles --list-examples
   adles --print-example competition


Usage
=====

Creating an environment using ADLES:

* Read the exercise and infrastructure specifications and examples of them.
* Write an infrastructure specification for your platform. (Currently, VMware vSphere is the only platform supported)
* Write an exercise specification with the environment you want created.
* Check its syntax, run the mastering phase, make your changes, and then run the deployment phase.


.. code:: bash


   adles -c my-competition.yaml
   adles -m -s my-competition.yaml
   adles -d -s my-competition.yaml


API Documentation
=================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   interfaces
   platforms
   scripts
   utils


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

