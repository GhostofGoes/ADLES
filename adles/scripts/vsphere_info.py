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

"""Query information about a vSphere environment and objects within it.

Usage:
    vsphere-info [options]

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -n, --no-color       Do not color terminal output
    -v, --verbose       Emit debugging logs to terminal
    -f, --file FILE     Name of JSON file with server connection information

Examples:
    vsphere-info -vf logins.json

"""

import logging

from docopt import docopt

from adles.utils import script_setup, resolve_path, ask_question
from adles.vsphere.folder_utils import format_structure

__version__ = "0.6.4"


def main():
    args = docopt(__doc__, version=__version__, help=True)
    server = script_setup('vsphere_info.log', args, (__file__, __version__))

    thing_type = str(input("What type of thing do you want"
                           "to get information on?"
                           " (vm | datastore | vsphere | folder) "))

    # Single Virtual Machine
    if thing_type == "vm":
        vm = resolve_path(server, "vm", "you want to get information on")[0]
        logging.info(vm.get_info(detailed=True, uuids=True,
                                 snapshot=True, vnics=True))

    # Datastore
    elif thing_type == "datastore":
        ds = server.get_datastore(str(input("Enter name of the Datastore"
                                            "[leave blank for "
                                            "first datastore found]: ")))
        logging.info(ds.get_info())

    # vCenter server
    elif thing_type == "vsphere":
        logging.info(str(server))

    # Folder
    elif thing_type == "folder":
        folder, folder_name = resolve_path(server, "folder")
        if "VirtualMachine" in folder.childType \
                and ask_question("Want to see power state "
                                 "of VMs in the folder?"):
            contents = folder.enumerate(recursive=True, power_status=True)
        else:
            contents = folder.enumerate(recursive=True, power_status=False)
        logging.info("Information for Folder %s\n"
                     "Types of items folder can contain: %s\n%s",
                     folder_name, str(folder.childType),
                     format_structure(contents))

    # That's not a thing!
    else:
        logging.info("Invalid selection: %s", thing_type)


if __name__ == '__main__':
    main()
