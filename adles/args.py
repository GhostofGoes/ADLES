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

from adles.__about__ import __version__


description = """
ADLES: Automated Deployment of Lab Environments System.
Uses formal YAML specifications to create virtual environments for educational purposes.
"""


epilog = """
License:    Apache 2.0
Author:     Christopher Goes <goesc@acm.org>
Project:    https://github.com/GhostofGoes/ADLES
"""


def parse_cli_args():
    main_parser = argparse.ArgumentParser(
        prog='adles', formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description, epilog=epilog
    )
    main_parser.set_defaults(script='main')
    main_parser.add_argument('--version', action='version',
                             version='ADLES %s' % __version__)
    main_parser.add_argument('-v', '--verbose', action='store_true',
                             help='Emit debugging logs to terminal')
    main_parser.add_argument('--no-color', action='store_true',
                             help='Do not color terminal output')

    # TODO: break out logging config into a separate group
    main_parser.add_argument('--syslog', type=str, metavar='SERVER',
                             help='Send logs to a Syslog server on port 514')

    # Example/spec printing
    examples = main_parser.add_argument_group(title='Print examples and specs')
    examples.add_argument('--list-examples', action='store_true',
                          help='Prints the list of available example scenarios')
    examples.add_argument('--print-spec', type=str, default='exercise',
                          help='Prints the named specification', metavar='NAME',
                          choices=['exercise', 'package', 'infrastructure'])
    examples.add_argument('--print-example', type=str, metavar='NAME',
                          help='Prints the named example')

    # TODO: cleanup
    # TODO: title for mutually exclusive group?
    # cleanup_group = main_parser.add_mutually_exclusive_group()

    # ADLES sub-commands
    adles_subs = main_parser.add_subparsers(title='ADLES Subcommands')

    # TODO: validate
    validate = adles_subs.add_parser(name='validate',
                                     help='Validate syntax of a specification')
    validate.add_argument('-t', '--type', type=str,
                          metavar='TYPE', default='exercise',
                          choices=['exercise', 'package', 'infra'],
                          help='Type of specification to validate')

    # TODO: deploy
    deploy = adles_subs.add_parser(name='deploy', help='Deploy an environment')

    # TODO: packages
    # package = adles_subs.add_parser(name='package', help='Create a package')

    # Default to printing usage if no arguments are provided
    if len(sys.argv) == 1:
        main_parser.print_usage()
        sys.exit(1)

    args = main_parser.parse_args()
    return args



