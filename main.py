#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://multivax.com/last_question.html

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ADLES: Automated Deployment of Lab Environments System.
Uses YAML specifications to manage and create virtual environments.

Usage:
    main.py [options] --check-syntax FILE
    main.py [options] (--create-masters | --deploy) -s FILE
    main.py [options] --package-dir NAME
    main.py [options] (--cleanup-masters | --cleanup-enviro) [--network-cleanup] -s FILE
    main.py --version
    main.py --help

Options:
    -h, --help                  Shows this help
    --version                   Prints current version
    --no-color                  Do not color termianl output
    -v, --verbose               Emit debugging logs to terminal
    -c, --check-syntax FILE     Validates syntax is valid per specification
    -s, --spec FILE             YAML file with the environment specification
    -p, --package-dir NAME      Filepath of the exercise package directory
    -m, --create-masters        Master creation phase of specification
    -d, --deploy                Environment deployment phase of specification
    --cleanup-masters           Cleanup masters created by a specification
    --cleanup-enviro            Cleanup environment created by a specification
    --network-cleanup           Cleanup networks created during either phase

Examples:
    main.py --check-syntax examples/tutorial.yaml
    main.py -v --create-masters --spec examples/experiment.yaml
    main.py -d -s examples/competition.yaml
    main.py --cleanup-masters --network-cleanup -s examples/competition.yaml

"""

import logging
from sys import exit

from docopt import docopt

from adles.interfaces import Interface
from adles.parser import parse_file, verify_syntax
from adles.utils import time_execution, setup_logging


@time_execution
def main():
    """ Primary entrypoint into the system.
    Calls the appropirate interfaces or functions based on the arguments """

    if args["--spec"]:
        spec = check_syntax(args["--spec"])
        interface = Interface(spec)
        if args["--create-masters"]:
            interface.create_masters()
            logging.info("Finished creation of Masters for environment %s",
                         str(spec["metadata"]["name"]))
        elif args["--deploy"]:
            interface.deploy_environment()
            logging.info("Finished deployment of environment %s",
                         str(spec["metadata"]["name"]))
        elif args["--cleanup-masters"]:
            interface.cleanup_masters(args["--network-cleanup"])
        elif args["--cleanup-enviro"]:
            interface.cleanup_environment(args["--network-cleanup"])
        else:
            logging.error("Invalid flags for --spec. Argument dump:\n%s",
                          str(args))

    elif args["--check-syntax"]:
        check_syntax(args["--check-syntax"])

    elif args["--package-dir"]:
        logging.error("CURRENTLY UNSUPPORTED")

    else:
        logging.error("Invalid arguments. Argument dump:\n%s", str(args))


@time_execution
def check_syntax(specfile_path):
    """
    Checks the syntax of a specification file
    :param specfile_path: Path to the specification file
    :return: The specification
    """
    from os.path import exists, basename

    if not exists(specfile_path):
        logging.error("Could not find specification file in path %s",
                      str(specfile_path))
        exit(1)
    spec = parse_file(specfile_path)
    logging.info("Successfully ingested specification file %s",
                 str(basename(specfile_path)))
    logging.info("Checking syntax...")
    errors, warnings = verify_syntax(spec)
    if errors == 0 and warnings == 0:
        logging.info("Syntax check successful!")
        return spec
    elif errors == 0:
        logging.info("Syntax check successful, but there were %d warnings",
                     warnings)
        return spec
    else:
        logging.error("Syntax check failed! Errors: %d\tWarnings: %d",
                      errors, warnings)
        exit(1)


if __name__ == '__main__':
    from adles import __version__
    args = docopt(__doc__, version=__version__, help=True)

    from adles.utils import setup_logging
    colors = (True if args["--no-color"] else False)
    setup_logging(filename='main.log', colors=colors,
                  console_verbose=args["--verbose"])

    main()
