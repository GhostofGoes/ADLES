#!/usr/bin/env python3

import sys

from adles import main
from adles.args import parse_cli_args
from adles.utils import setup_logging


def main():
    # Parse CLI arguments
    args = parse_cli_args()

    # Set if console output should be colored
    colors = (False if args.no_color else True)

    # Syslog server
    syslog = (args.syslog, 514) if args.syslog else None

    # Configure logging
    setup_logging(filename='adles.log', colors=colors,
                  console_verbose=args.verbose, server=syslog)

    # Run ADLES
    exit_status = main.main(args=args)
    sys.exit(exit_status)


if __name__ == '__main__':
    main()
