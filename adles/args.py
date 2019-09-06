import argparse
import sys

from adles.__about__ import __version__

description = """
ADLES: Automated Deployment of Lab Environments System.
Uses formal YAML specifications to create virtual environments for educational purposes.

Examples:
    adles --list-examples
    adles --print-example competition | adles validate -
    adles validate examples/pentest-tutorial.yaml
    adles masters examples/experiment.yaml
    adles -v deploy examples/experiment.yaml
    adles cleanup -t masters --cleanup-nets examples/competition.yaml
    adles validate -t infra examples/infra.yaml
"""


epilog = """
License:    Apache 2.0
Author:     Christopher Goes <goesc@acm.org>
Project:    https://github.com/GhostofGoes/ADLES
"""


# TODO: Gooey
def parse_cli_args() -> argparse.Namespace:
    main_parser = argparse.ArgumentParser(
        prog="adles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description,
        epilog=epilog,
    )
    main_parser.set_defaults(command="main")
    main_parser.add_argument(
        "--version", action="version", version="ADLES %s" % __version__
    )
    main_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Emit debugging logs to terminal"
    )

    # TODO: break out logging config into a separate group
    main_parser.add_argument(
        "--syslog",
        type=str,
        metavar="SERVER",
        help="Send logs to a Syslog server on port 514",
    )
    main_parser.add_argument(
        "--no-color", action="store_true", help="Do not color terminal output"
    )

    # Example/spec printing
    examples = main_parser.add_argument_group(title="Print examples and specs")
    examples.add_argument(
        "--list-examples",
        action="store_true",
        help="Prints the list of available example scenarios",
    )
    examples.add_argument(
        "--print-spec",
        type=str,
        default="exercise",
        help="Prints the named specification",
        metavar="NAME",
        choices=["exercise", "package", "infrastructure"],
    )
    examples.add_argument(
        "--print-example", type=str, metavar="NAME", help="Prints the named example"
    )

    main_parser.add_argument(
        "-i",
        "--infra",
        type=str,
        metavar="INFRA",
        help="Override the infrastructure " "specification to be used",
    )

    # ADLES sub-commands (TODO)
    adles_subs = main_parser.add_subparsers(title="ADLES Subcommands")

    # Validate
    validate = adles_subs.add_parser(
        name="validate", help="Validate the syntax " "of your specification"
    )
    validate.set_defaults(command="validate")
    validate.add_argument(
        "-t",
        "--validate-type",
        type=str,
        metavar="TYPE",
        default="exercise",
        choices=["exercise", "package", "infra"],
        help="Type of specification to validate",
    )
    # TODO:
    #   type=argparse.FileType(encoding='UTF-8')
    #   '-' argument...
    validate.add_argument("spec", help="The YAML specification file to validate")

    # Deployment phase
    deploy = adles_subs.add_parser(
        name="deploy", help="Environment deployment " "phase of specification"
    )
    deploy.set_defaults(command="deploy")
    deploy.add_argument("spec", help="The YAML specification file to deploy")

    # Mastering phase
    masters = adles_subs.add_parser(
        name="masters", help="Master creation phase " "of specification"
    )
    masters.set_defaults(command="masters")
    masters.add_argument(
        "spec", help="The YAML specification file " "to create masters from"
    )

    # TODO: packages
    package = adles_subs.add_parser(name="package", help="Create a package")
    package.set_defaults(command="package")
    package.add_argument("spec", help="The package specification to use")

    # Cleanup
    cleanup = adles_subs.add_parser(
        name="cleanup", help="Cleanup and remove " "existing environments"
    )
    cleanup.set_defaults(command="cleanup")
    cleanup.add_argument(
        "-t",
        "--cleanup-type",
        type=str,
        metavar="TYPE",
        choices=["masters", "environment"],
        help="Type of cleanup to perform",
    )
    cleanup.add_argument(
        "--cleanup-nets",
        action="store_true",
        help="Cleanup networks created during either phase",
    )
    cleanup.add_argument(
        "spec",
        help="The YAML specification file defining " "the environment to cleanup",
    )

    # Default to printing usage if no arguments are provided
    if len(sys.argv) == 1:
        main_parser.print_usage()
        sys.exit(1)

    args = main_parser.parse_args()
    return args
