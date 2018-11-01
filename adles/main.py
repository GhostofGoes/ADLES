# http://multivax.com/last_question.html

import logging
import sys
from os.path import basename, exists, splitext, join

from adles.args import parse_cli_args
from adles.interfaces import PlatformInterface
from adles.parser import check_syntax, parse_yaml
from adles.utils import handle_keyboard_interrupt, setup_logging


def run_cli():
    """Parse command line interface arguments and run ADLES."""
    args = parse_cli_args()
    exit_status = main(args=args)
    sys.exit(exit_status)


@handle_keyboard_interrupt
def main(args) -> int:
    """
    :param args:
    :return: The exit status of the program
    """
    # Configure logging, including console colors and syslog server
    colors = (False if args.no_color else True)
    syslog = (args.syslog, 514) if args.syslog else None
    setup_logging(filename='adles.log', colors=colors,
                  console_verbose=args.verbose, server=syslog)

    # Set the sub-command to execute
    command = args.command

    # Just validate syntax, no building of environment
    if command == 'validate':
        if check_syntax(args.spec, args.validate_type) is None:
            return 1
    # Build an environment using a specification
    elif command in ['deploy', 'masters', 'cleanup', 'package']:
        override = None
        if command == 'package':  # Package specification
            package_spec = check_syntax(args.spec, spec_type='package')
            if package_spec is None:  # Ensure it passed the check
                return 1
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
            return 1
        if "name" not in spec["metadata"]:
            # Default name is the filename of the specification
            spec["metadata"]["name"] = splitext(basename(args.spec))[0]

        # Override the infra file defined in exercise/package specification
        if args.infra:
            infra_file = args.infra
            if not exists(infra_file):
                logging.error("Could not find infra file '%s' "
                              "to override with", infra_file)
            else:
                override = infra_file

        if override is not None:  # Override infra file in exercise config
            logging.info("Overriding infrastructure config "
                         "file with '%s'", override)
            spec["metadata"]["infra-file"] = override

        # Instantiate the Interface and call functions for the specified phase
        interface = PlatformInterface(infra=parse_yaml(
            spec["metadata"]["infra-file"]), spec=spec)
        if command == 'masters':
            interface.create_masters()
            logging.info("Finished Master creation for %s",
                         spec["metadata"]["name"])
        elif command == 'deploy':
            interface.deploy_environment()
            logging.info("Finished deployment of %s",
                         spec["metadata"]["name"])
        elif command == 'cleanup':
            if args.cleanup_type == 'masters':
                interface.cleanup_masters(args.cleanup_nets)
            elif args.cleanup_type == 'environment':
                interface.cleanup_environment(args.cleanup_nets)
            logging.info("Finished %s cleanup of %s", args.cleanup_type,
                         spec["metadata"]["name"])
        else:
            logging.error("INTERNAL ERROR -- Invalid command: %s", command)
            return 1
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
                return 1
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
            return 1
    # Handle invalid arguments
    else:
        logging.error("Invalid arguments. Argument dump:\n%s", str(vars(args)))
        return 1

    # Finished successfully
    return 0
