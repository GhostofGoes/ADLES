#!/usr/bin/env python3

import argparse
import sys

from adles.utils import setup_logging
from adles.vsphere.vsphere_scripts import VSPHERE_SCRIPTS


def main():
    # Parse CLI arguments
    # TODO: generalize this between other scripts and adles main?
    args = parse_args()

    # Set if console output should be colored
    colors = False if args.no_color else True

    # Configure logging
    setup_logging(
        filename="vsphere_scripts.log", colors=colors, console_verbose=args.verbose
    )

    script = args.script(args.server_info)
    script.run()


def parse_args():
    parser = argparse.ArgumentParser(
        prog="vsphere",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Single-purpose CLI scripts for interacting with vSphere",
    )
    subparsers = parser.add_subparsers(title="vSphere scripts")

    for s in VSPHERE_SCRIPTS:
        subp = subparsers.add_parser(name=s.name, help=s.__doc__)
        subp.set_defaults(script=s)
        subp.add_argument("--version", action="version", version=s.get_ver())
        subp.add_argument(
            "-f",
            "--server-info",
            type=str,
            default=None,
            metavar="FILE",
            help="Name of JSON file with vSphere " "server connection information",
        )
        subp.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Emit debugging logs to terminal",
        )
        subp.add_argument(
            "--no-color", action="store_true", help="Do not color terminal output"
        )

    # Default to printing usage if no arguments are provided
    if len(sys.argv) == 1:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
