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

from adles import adles_cli
from adles.args import parse_cli_args
from adles.utils import setup_logging


def main():
    # Parse CLI arguments
    args = parse_cli_args()

    # Set if console output should be colored
    colors = (False if args.no_color else True)

    # Syslog server
    if args.syslog:
        syslog = (str(args.syslog), 514)
    else:
        syslog = None

    # Configure logging
    setup_logging(filename='adles.log', colors=colors,
                  console_verbose=args.verbose, server=syslog)

    # Run ADLES
    adles_cli.main(args=args)


if __name__ == '__main__':
    main()
