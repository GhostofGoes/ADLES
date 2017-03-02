#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


def warning():
    """ Prints a warning prompt. """
    print("\n\n\n** YOU RUN THIS SCRIPT AT YOUR OWN RISK **"
          "\nPlease read the source code or documentation for information on proper script usage\n\n")


def script_setup(logging_filename, args):
    """

    :param logging_filename:
    :param args:
    :return: vSphere object
    """

    # Fix module imports
    import sys
    sys.path.append('../')

    # Setup logging
    from adles.automation.utils import setup_logging, make_vsphere
    setup_logging(filename=logging_filename, console_level=logging.DEBUG if args["--verbose"] else logging.INFO)

    # Print warning
    warning()

    # Create the vsphere object and return it
    return make_vsphere(args["--file"])
