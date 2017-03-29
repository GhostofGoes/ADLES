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
    adles.py [options] -c SPEC
    adles.py [options] (-m | -d) -s SPEC
    adles.py [options] -p PATH
    adles.py [options] (--cleanup-masters | --cleanup-enviro) [--network-cleanup] -s SPEC
    adles.py --version
    adles.py (-h | --help)

Options:
    --no-color                  Do not color terminal output
    -v, --verbose               Emit debugging logs to terminal
    -c, --check-syntax SPEC     Validates syntax is valid per specification
    -s, --spec SPEC             YAML file with the exercise environment specification
    -p, --package-dir PATH      Filepath of the exercise package directory
    -m, --create-masters        Master creation phase of specification
    -d, --deploy                Environment deployment phase of specification
    --cleanup-masters           Cleanup masters created by a specification
    --cleanup-enviro            Cleanup environment created by a specification
    --network-cleanup           Cleanup networks created during either phase
    -h, --help                  Shows this help
    --version                   Prints current version

Examples:
    adles.py --check-syntax examples/tutorial.yaml
    adles.py --verbose --create-masters --spec examples/experiment.yaml
    adles.py -v -d -s examples/competition.yaml
    adles.py --cleanup-masters --network-cleanup -s examples/competition.yaml

"""

import logging

from docopt import docopt

from adles.interfaces import Interface
from adles.parser import check_syntax
from adles.utils import setup_logging
from adles import __version__


def main():
    args = docopt(__doc__, version=__version__, help=True)
    colors = (False if args["--no-color"] else True)
    setup_logging(filename='adles.log', colors=colors, console_verbose=args["--verbose"])

    if args["--spec"]:
        spec = check_syntax(args["--spec"])
        if spec is None:
            logging.error("Syntax check failed")
            exit(1)

        interface = Interface(spec)
        if args["--create-masters"]:
            interface.create_masters()
            logging.info("Finished creation of Masters for environment %s",
                         spec["metadata"]["name"])
        elif args["--deploy"]:
            interface.deploy_environment()
            logging.info("Finished deployment of environment %s", spec["metadata"]["name"])
        elif args["--cleanup-masters"]:
            interface.cleanup_masters(args["--network-cleanup"])
        elif args["--cleanup-enviro"]:
            interface.cleanup_environment(args["--network-cleanup"])
        else:
            logging.error("Invalid flags for --spec. Argument dump:\n%s", str(args))

    elif args["--check-syntax"]:
        if check_syntax(args["--check-syntax"]) is None:
            logging.error("Syntax check failed")

    elif args["--package-dir"]:
        from os.path import exists
        if not exists(args["--package-dir"]):
            logging.error("Could not find package directory '%s'", args["--package-dir"])
            exit(1)
        logging.error("PACKAGES ARE CURRENTLY UNSUPPORTED")

    else:
        logging.error("Invalid arguments. Argument dump:\n%s", str(args))

if __name__ == '__main__':
    main()
