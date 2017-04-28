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

from adles.utils import ask_question, pad, default_prompt, script_setup, resolve_path, is_vm
from adles.vsphere.vm import VM

__version__ = "0.6.0"


def main():
    args = docopt(__doc__, version=__version__, help=True)
    server = script_setup('clone_vms.log', args, (__file__, __version__))

    vms = []
    vm_names = []

    # Single-vm source
    if ask_question("Do you want to clone from a single VM?"):
        v, v_name = resolve_path(server, "VM", "or template you wish to clone")
        vms.append(v)
        vm_names.append(str(input("Base name for instances to be created: ")))
    # Multi-VM source
    else:
        folder_from, from_name = resolve_path(server, "folder", "you want to clone all VMs in")
        v = [VM(vm=x) for x in folder_from.childEntity if is_vm(x)]  # Get VMs in the folder
        # v, _ = folder_from.retrieve_items()  # Get VMs in the folder, ignore any folders
        vms.extend(v)
        logging.info("%d VMs found in source folder %s", len(v), from_name)
        if not ask_question("Keep the same names? "):
            names = []
            for i in range(len(v)):
                names.append(str(input("Enter base name for VM %d: " % i)))
        else:
            names = list(map(lambda x: x.name, v))  # Same names as sources
        vm_names.extend(names)

    create_in, create_in_name = resolve_path(server, "folder", "in which to create VMs")
    instance_folder_base = None
    if ask_question("Do you want to create a folder for each instance? "):
        instance_folder_base = str(input("Enter instance folder base name: "))

    num_instances = int(input("Number of instances to be created: "))

    pool_name = server.get_pool().name  # Determine what will be default, so we can tell user
    pool_name = default_prompt(prompt="Resource pool to assign VMs to", default=pool_name)
    pool = server.get_pool(pool_name)

    datastore_name = default_prompt(prompt="Datastore to put clones on")
    datastore = server.get_datastore(datastore_name)

    logging.info("Creating %d instances under folder %s", num_instances, create_in_name)
    for instance in range(num_instances):
        for vm, name in zip(vms, vm_names):
            # spec = server.gen_clone_spec(pool_name=pool_name)  # Generate clone specification
            if instance_folder_base:  # Create instance folders for a nested clone
                f = server.create_folder(instance_folder_base + pad(instance), create_in=create_in)
                vm_name = name
            else:
                f = create_in
                vm_name = name + pad(instance)    # Append instance number
            new_vm = VM(name=vm_name, folder=f, resource_pool=pool, datastore=datastore)
            new_vm.create(template=vm)  # TODO: allow user to modify specs of instances cloned!
            # vm.clone(folder=f, name=vm_name, clone_spec=spec)


if __name__ == '__main__':
    main()
