*******************************************************
Automated Deployment of Lab Environments System (ADLES)
*******************************************************

SYNOPSIS
========

  adles [options] [-]
  adles [options] [-t TYPE] -c SPEC [-]
  adles [options] (-m | -d) [-p] -s SPEC [-]
  adles [options] (--cleanup-masters | --cleanup-enviro) [--nets] -s SPEC [-]


DESCRIPTION
===========

Automated Deployment of Lab Environments System (ADLES)

| ADLES automates the deterministic creation of virtualized environments for use in
  Cybersecurity and Information Technology (IT) education.
| The system enables educators to easily build deterministic and
  portable environments for their courses, saving significant amounts of
  time and effort, and alieviates the requirement of possessing advanced IT knowledge.

Complete documentation can be found at ReadTheDocs: https://adles.readthedocs.io

Project source code and examples can be found on GitHub: https://github.com/GhostofGoes/ADLES


COMMAND LINE OPTIONS
====================

  -n, --no-color          Do not color terminal output
  -v, --verbose           Emit debugging logs to terminal
  -c, --validate SPEC     Validates syntax of an exercise specification
  -t, --type TYPE         Type of specification to validate: exercise, package, infra
  -s, --spec SPEC         Name of a YAML specification file
  -i, --infra FILE        Override infra spec with the one in FILE
  -p, --package           Build environment from package specification
  -m, --masters           Master creation phase of specification
  -d, --deploy            Environment deployment phase of specification
  --cleanup-masters       Cleanup masters created by a specification
  --cleanup-enviro        Cleanup environment created by a specification
  --nets                  Cleanup networks created during either phase
  --print-spec NAME       Prints the named specification: exercise, package, infrastructure
  --list-examples         Prints the list of examples available
  --print-example NAME    Prints the named example
  -h, --help              Shows this help
  --version               Prints current version


USAGE
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


EXAMPLES
========
    adles --list-examples
    adles -c examples/tutorial.yaml
    adles --verbose --masters --spec examples/experiment.yaml
    adles -vds examples/competition.yaml
    adles --cleanup-masters --nets -s examples/competition.yaml
    adles --print-example competition | adles -v -c -


LICENSING
=========

This project is licensed under the Apache License, Version 2.0. See
LICENSE for the full license text, and NOTICES for attributions to
external projects that this project uses code from.


PROJECT HISTORY
===============

The system began as a proof of concept implementation of my Master's thesis research at the
University of Idaho in Fall of 2016. It was originally designed to run on the RADICL lab.

