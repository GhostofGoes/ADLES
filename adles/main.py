# http://multivax.com/last_question.html

import logging
from os.path import basename, exists, splitext, join
from pathlib import Path

from adles.interfaces import PlatformInterface
from adles.parser import check_syntax, parse_yaml, parse_yaml_file, validate_spec
from adles.utils import handle_keyboard_interrupt
from adles import __version__

import click


def validate_spec_file(ctx, param, value) -> dict:
    spec = parse_yaml_file(value)
    if spec is None:
        raise click.BadParameter("Failed to parse specifciation file %s" % value.name)
    elif validate_spec(spec):
        return spec
    else:
        raise click.BadParameter("Specification %s failed validation" % value.name)


@click.command(context_settings=dict(auto_envvar_prefix='ADLES'))
@click.version_option(__version__)
@click.option('-v', '--verbose', is_flag=True,
              help='Increase the amount of terminal output')
@click.option('-q', '--quiet', is_flag=True,
              help='Do not output to the terminal')
@click.option('--color/--no-color', default=True,
              help='Do not color terminal output')
@click.option('--syslog-server', type=str,
              help='Send logs to the specified Syslog server on port 514')
@click.option('--validate', 'command', flag_value='validate', default=True)
@click.option('--create-masters', 'command', flag_value='masters')
@click.option('--deploy', 'command', flag_value='deploy')
@click.option('--create-package', 'command', flag_value='package')
@click.option('--cleanup-package', 'command', flag_value='package')
@click.argument('spec', type=click.File('r'), callback=validate_spec_file)
@click.pass_context
def cli(ctx, verbose, quiet, color, syslog_server, command, spec):
    """SPEC: YAML specification to use """
    pass


@handle_keyboard_interrupt
def main(args):
    """
    :param args:
    :return: The exit status of the program
    """
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
