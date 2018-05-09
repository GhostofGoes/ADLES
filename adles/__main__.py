#!/usr/bin/env python3

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

import logging
import inspect

from adles.args import parse_cli_args
from adles.utils import setup_logging


def main():
    # Parse CLI arguments
    args = parse_cli_args()

    # Configure logging
    setup_logging(filename='adles.log', colors=not args.no_color,
                  console_verbose=args.verbose, server=args.syslog)

    # Run the proper script
    if inspect.isclass(args.script):
        # The vSphere scripts
        script = args.script(args.server_info)
        script.run()
    elif args.script == 'main':
        # The main CLI interface
        from adles import adles_cli
        adles_cli.main(args=args)
    else:
        logging.error("Bad script value was set during argument parsing. "
                      "This should never happen.\nValue: %s", str(args.script))


if __name__ == '__main__':
    main()
