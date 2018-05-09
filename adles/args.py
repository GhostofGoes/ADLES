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

from .__about__ import __version__


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

    examples = main_parser.add_argument_group(title='Print examples and specs')
    examples.add_argument('--list-examples', action='store_true',
                          help='Prints the list of available example scenarios')
    examples.add_argument('--print-spec', type=str, default='exercise',
                          help='Prints the named specification', metavar='NAME',
                          choices=['exercise', 'package', 'infrastructure'])
    examples.add_argument('--print-example', type=str, metavar='NAME',
                          help='Prints the named example')

    # TODO: cleanup
    # TODO: title?
    # cleanup_group = main_parser.add_mutually_exclusive_group()
    # cleanup_group.add_argument()

    # ADLES sub-commands
    adles_subs = main_parser.add_subparsers(title='ADLES Subcommands')

    validate = adles_subs.add_parser(name='validate',
                                     help='Validate syntax of a specification')
    validate.add_argument('-t', '--type', type=str,
                          metavar='TYPE', default='exercise',
                          choices=['exercise', 'package', 'infra'],
                          help='Type of specification to validate')
    # validate.add_argument()

    deploy = adles_subs.add_parser(name='deploy', help='Deploy an environment')

    # TODO: packages
    # package = adles_subs.add_parser(name='package', help='Create a package')

    # vSphere scripts
    # TODO: cli args instead of filename
    # e.g. "--vsphere-user" on all vsphere scripts, so ConfigArgParse can do it's thing globally
    # vs_subs = main_parser.add_subparsers(title='vSphere Scripts')
    from .scripts.vsphere_scripts import VSPHERE_SCRIPTS
    for s in VSPHERE_SCRIPTS:
        subp = adles_subs.add_parser(name=s.name, help=str(s))
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
        main_parser.print_usage()
        sys.exit(1)

    args = main_parser.parse_args()
    return args



