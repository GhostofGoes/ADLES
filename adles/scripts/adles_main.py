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
    adles [options]
    adles [options] [-t TYPE] -c SPEC
    adles [options] (-m | -d) [-p] -s SPEC
    adles [options] (--cleanup-masters | --cleanup-enviro) [--nets] -s SPEC

Options:
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

Examples:
    adles --list-examples
    adles -c examples/pentest-tutorial.yaml
    adles --verbose --masters --spec examples/experiment.yaml
    adles -vds examples/competition.yaml
    adles --cleanup-masters --nets -s examples/competition.yaml
    adles -v -t infra -c examples/infra.yaml

License:    Apache 2.0
Author:     Christopher Goes <goesc@acm.org>
Project:    https://github.com/GhostofGoes/ADLES

"""

import logging
from os.path import basename, exists, splitext, join

from pyVmomi import vim

from adles.interfaces import PlatformInterface
from adles.parser import check_syntax, parse_yaml
from adles.utils import get_args
from adles import __version__


def main():
    args = get_args(__doc__, __version__, 'adles.log')

    # Build an environment using a specification
    if args.spec:
        override = None
        if args.package:  # Package specification
            package_spec = check_syntax(args.spec, spec_type="package")
            if package_spec is None:  # Ensure it passed the check
                exit(1)
            # Extract exercise spec filename
            spec_filename = package_spec["contents"]["environment"]
            if "infrastructure" in package_spec["contents"]:
                # Extract infra spec filename
                override = package_spec["contents"]["infrastructure"]
        else:
            spec_filename = args.spec
        # Validate specification syntax before proceeding
        spec = check_syntax(spec_filename)
        if spec is None:  # Ensure it passed the check
            exit(1)
        if "name" not in spec["metadata"]:
            # Default name is the filename of the specification
            spec["metadata"]["name"] = splitext(basename(args.spec))[0]

        # Override the infra file defined in exercise/package specification
        if args.infra:
            infra_file = args.infra
            if not exists(infra_file):
                logging.error("Could not find infra file '%s' to override with",
                              infra_file)
            else:
                override = infra_file

        if override is not None:  # Override infra file in exercise config
            logging.info("Overriding infrastructure config file with '%s'",
                         override)
            spec["metadata"]["infra-file"] = override

        # Instantiate the Interface and call functions for the specified phase
        try:
            interface = PlatformInterface(infra=parse_yaml(
                spec["metadata"]["infra-file"]), spec=spec)
            if args.masters:
                interface.create_masters()
                logging.info("Finished Master creation for %s",
                             spec["metadata"]["name"])
            elif args.deploy:
                interface.deploy_environment()
                logging.info("Finished deployment of %s",
                             spec["metadata"]["name"])
            elif args.cleanup_masters:
                interface.cleanup_masters(args.nets)
                logging.info("Finished master cleanup of %s",
                             spec["metadata"]["name"])
            elif args.cleanup_enviro:
                interface.cleanup_environment(args.nets)
                logging.info("Finished cleanup of %s",
                             spec["metadata"]["name"])
            else:
                logging.critical("Invalid flags for --spec. "
                                 "Argument dump:\n%s", str(vars(args)))
        except vim.fault.NoPermission as e:  # Log permission errors
            logging.error("Permission error: \n%s", str(e))
            exit(1)
        except KeyboardInterrupt:  # Handle user exits gracefully
            print()
            logging.warning("User terminated session prematurely")
            exit(1)

    # Just validate syntax, no building of environment
    elif args.validate:
        if args.type:
            spec_type = args.type
        else:
            spec_type = "exercise"
        if check_syntax(args.validate, spec_type) is None:
            logging.error("Syntax check failed")

    # Show examples on commandline
    elif args.list_examples or args.print_example:
        from pkg_resources import Requirement, resource_filename
        from os import listdir
        example_dir = resource_filename(Requirement.parse("ADLES"), "examples")
        # Filter non-YAML files from the listdir output
        examples = [x[:-5] for x in listdir(example_dir) if ".yaml" in x]
        if args.list_examples:  # List all examples and their metadata
            print("Example scenarios that can be printed "
                  "using --print-example <name>")
            # Print header for the output
            print("Name".ljust(25) + "Version".ljust(10) + "Description")
            for example in examples:
                if "infra" in example:
                    continue
                metadata = parse_yaml(
                    join(example_dir, example + ".yaml"))["metadata"]
                name = str(example).ljust(25)
                ver = str(metadata["version"]).ljust(10)
                desc = str(metadata["description"])
                print(name + ver + desc)
        else:
            example = args.print_example
            if example in examples:
                # Print out the complete content of a named example
                with open(join(example_dir, example + ".yaml")) as file:
                    print(file.read())
            else:
                logging.error("Invalid example: %s", example)

    # Show specifications on commandline
    elif args.print_spec:
        from pkg_resources import Requirement, resource_filename
        spec = args.print_spec
        specs = ["exercise", "package", "infrastructure"]

        # Find spec in package installation directory and print it
        if spec in specs:
            # Extract specifications from their package installation location
            filename = resource_filename(Requirement.parse("ADLES"),
                                         join("specifications",
                                              spec + "-specification.yaml"))
            with open(filename) as file:
                print(file.read())
        else:
            logging.error("Invalid specification: %s", spec)

    # Handle invalid arguments
    else:
        logging.error("Invalid arguments. Argument dump:\n%s", str(vars(args)))


if __name__ == '__main__':
    main()
