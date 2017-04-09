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
Uses formal YAML specifications to create virtual environments for educational purposes.

Usage:
    adles.py [options] -c SPEC
    adles.py [options] (-m | -d) [-p] -s SPEC
    adles.py [options] (--cleanup-masters | --cleanup-enviro) [--network-cleanup] -s SPEC
    adles.py --version
    adles.py (-h | --help)

Options:
    --no-color                  Do not color terminal output
    -v, --verbose               Emit debugging logs to terminal
    -c, --check-syntax SPEC     Validates syntax of an exercise specification
    -s, --spec SPEC             YAML file with the exercise environment specification
    -p, --package               Build environment from package specification
    -m, --create-masters        Master creation phase of specification
    -d, --deploy                Environment deployment phase of specification
    --cleanup-masters           Cleanup masters created by a specification
    --cleanup-enviro            Cleanup environment created by a specification
    --network-cleanup           Cleanup networks created during either phase
    -i, --infra FILE            Specifies the infrastructure configuration file to use
    -h, --help                  Shows this help
    --version                   Prints current version

Examples:
    adles.py --check-syntax examples/tutorial.yaml
    adles.py --verbose --create-masters --spec examples/experiment.yaml
    adles.py -v -d -s examples/competition.yaml
    adles.py --cleanup-masters --network-cleanup -s examples/competition.yaml

License:    Apache 2.0
Author:     Christopher Goes <goes8945@vandals.uidaho.edu>
Project:    https://github.com/GhostofGoes/ADLES

"""

import logging

from docopt import docopt
from pyVmomi import vim

from adles.interfaces import Interface
from adles.parser import check_syntax, parse_file
from adles.utils import setup_logging
from adles import __version__


def main():
    args = docopt(__doc__, version=__version__, help=True)
    colors = (False if args["--no-color"] else True)
    setup_logging(filename='adles.log', colors=colors, console_verbose=args["--verbose"])

    if args["--spec"]:
        if args["--package"]:
            # TODO: implement basic extraction of environment spec from package spec
            logging.error("Package specifications are not implemented yet")
            exit(1)

        spec = check_syntax(args["--spec"])
        if spec is None:
            logging.error("Syntax check failed")
            exit(1)
        if "name" not in spec["metadata"]:
            from os.path import basename, splitext
            spec["metadata"]["name"] = splitext(basename(args["--spec"]))[0]

        if args["--infra"]:
            from os.path import exists
            infra_file = args["--infra"]
            if not exists(infra_file):
                logging.error("Specified infrastructure config file '%s' could not be found,"
                              " falling back to exercise configuration", infra_file)
            else:
                logging.debug("Overriding infrastructure config file with '%s'", infra_file)
                spec["metadata"]["infrastructure-config-file"] = infra_file

        try:
            interface = Interface(spec, parse_file(spec["metadata"]["infrastructure-config-file"]))
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
        except vim.fault.NoPermission as e:
            logging.error("Permission error: \n%s", str(e))
            exit(1)
        except KeyboardInterrupt:
            logging.error("User terminated session prematurely")
            exit(1)
    elif args["--check-syntax"]:
        if check_syntax(args["--check-syntax"]) is None:
            logging.error("Syntax check failed")
    else:
        logging.error("Invalid arguments. Argument dump:\n%s", str(args))

if __name__ == '__main__':
    main()
