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
    adles.py [options] --check-syntax FILE
    adles.py [options] (--create-masters | --deploy) -s FILE
    adles.py [options] --package-dir NAME
    adles.py [options] (--cleanup-masters | --cleanup-enviro) [--network-cleanup] -s FILE
    adles.py --version
    adles.py (-h | --help)

Options:
    -h, --help                  Shows this help
    --version                   Prints current version
    --no-color                  Do not color terminal output
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
    adles.py --check-syntax examples/tutorial.yaml
    adles.py -v --create-masters --spec examples/experiment.yaml
    adles.py -d -s examples/competition.yaml
    adles.py --cleanup-masters --network-cleanup -s examples/competition.yaml

"""

import logging

from docopt import docopt

from adles.interfaces import Interface
from adles.parser import check_syntax
from adles.utils import setup_logging
from adles import __version__


args = docopt(__doc__, version=__version__, help=True)

colors = (False if args["--no-color"] else True)
setup_logging(filename='adles.log', colors=colors, console_verbose=args["--verbose"])

if args["--spec"]:
    spec = check_syntax(args["--spec"])
    if spec is None:
        logging.error("Syntax check failed")
        exit(0)

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
    logging.error("PACKAGES ARE CURRENTLY UNSUPPORTED")

else:
    logging.error("Invalid arguments. Argument dump:\n%s", str(args))
