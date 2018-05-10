#!/usr/bin/env python3

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

# TODO: ConfigArgParse
# TODO: Gooey
import argparse
import sys

from adles.vsphere.vsphere_scripts import VSPHERE_SCRIPTS
from adles.utils import setup_logging


def main():
    # Parse CLI arguments
    # TODO: generalize this between other scripts and adles main?
    args = parse_args()

    # Set if console output should be colored
    colors = (False if args.no_color else True)

    # Configure logging
    setup_logging(filename='vsphere_scripts.log', colors=colors,
                  console_verbose=args.verbose)

    script = args.script(args.server_info)
    script.run()


def parse_args():
    parser = argparse.ArgumentParser(
        prog='vsphere', formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Single-purpose CLI scripts for interacting with vSphere'
    )
    subparsers = parser.add_subparsers(title='vSphere scripts')

    # TODO: cli args instead of filename
    #   e.g. "--vsphere-user" on all vsphere scripts,
    #   so ConfigArgParse can do it's thing globally.
    for s in VSPHERE_SCRIPTS:
        subp = subparsers.add_parser(name=s.name, help=s.__doc__)
        subp.set_defaults(script=s)
        subp.add_argument('--version', action='version',
                          version=s.get_ver())
        subp.add_argument('-f', '--server-info', type=str,
                          default=None, metavar='FILE',
                          help='Name of JSON file with vSphere '
                               'server connection information')
        subp.add_argument('-v', '--verbose', action='store_true',
                          help='Emit debugging logs to terminal')
        subp.add_argument('--no-color', action='store_true',
                          help='Do not color terminal output')

    # Default to printing usage if no arguments are provided
    if len(sys.argv) == 1:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
