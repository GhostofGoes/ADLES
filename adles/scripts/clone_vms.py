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

"""Clone multiple Virtual Machines in vSphere.

Usage:
    clone-vms [options]
    clone-vms --version
    clone-vms (-h | --help)

Options:
    -h, --help          Prints this page
    --version           Prints current version
    -n, --no-color      Do not color terminal output
    -v, --verbose       Emit debugging logs to terminal
    -f, --file FILE     Name of JSON file with server connection information

Examples:
    clone-vms -vf logins.json

"""

import logging

from docopt import docopt

from adles.utils import prompt_y_n_question, pad, default_prompt, script_setup, resolve_path
from adles.vsphere.vm_utils import clone_vm
from adles.vsphere.folder_utils import format_structure, retrieve_items

__version__ = "0.5.3"


def main():
    args = docopt(__doc__, version=__version__, help=True)
    server = script_setup('clone_vms.log', args, (__file__, __version__))

    vms = []
    vm_names = []

    # Single-vm source
    if prompt_y_n_question("Do you want to clone from a single VM?"):
        v, v_name = resolve_path(server, "VM", "or template you wish to clone")
        vms.append(v)
        vm_names.append(str(input("Base name for instances to be created: ")))
    # Multi-VM source
    else:
        folder_from, from_name = resolve_path(server, "folder", "you want to clone all VMs in")
        v, _ = retrieve_items(folder_from)  # Get VMs in the folder, ignore any folders
        vms.extend(v)
        logging.info("%d VMs found in source folder %s\n%s",
                     len(v), from_name, format_structure(v))
        if not prompt_y_n_question("Keep the same names? "):
            names = []
            for i in range(len(v)):
                names.append(str(input("Enter base name for VM %d: " % i)))
        else:
            names = list(map(lambda x: x.name, v))  # Same names as sources
        vm_names.extend(names)

    create_in, create_in_name = resolve_path(server, "folder", "in which to create VMs")
    instance_folder_base = None
    if prompt_y_n_question("Do you want to create a folder for each instance? "):
        instance_folder_base = str(input("Enter instance folder base name: "))

    num_instances = int(input("Number of instances to be created: "))

    pool = server.get_pool().name
    pool = default_prompt(prompt="Resource pool to assign VMs to", default=pool)

    logging.info("Creating %d instances under folder %s", num_instances, create_in_name)
    for instance in range(num_instances):
        for vm, name in zip(vms, vm_names):
            spec = server.gen_clone_spec(pool_name=pool)  # Generate clone specification
            if instance_folder_base:  # Create instance folders for a nested clone
                f = server.create_folder(instance_folder_base + pad(instance), create_in=create_in)
                vm_name = name
                clone_vm(vm=vm, folder=f, name=vm_name, clone_spec=spec)
            else:
                vm_name = name + pad(instance)    # Append instance number
                clone_vm(vm=vm, folder=create_in, name=vm_name, clone_spec=spec)


if __name__ == '__main__':
    main()
