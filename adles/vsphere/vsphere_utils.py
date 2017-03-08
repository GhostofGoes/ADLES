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

from pyVmomi import vim


def wait_for_task(task):
    """
    Waits for a single vCenter task to finish and return it's result
    :param task: vim.Task object of the task to wait for
    :return: Task result information
    """
    if not task:
        logging.error("No task was specified to wait for")
        return None
    while True:
        if task.info.state == 'success':
            return task.info.result
        elif task.info.state == 'error':
            logging.error("There was an error while completing a task: '%s'", str(task.info.error.msg))
            return None


# From: various files in pyvmomi-community-samples
def get_obj(content, vimtype, name, container=None, recursive=True):
    """
    Finds and returns named vSphere object of specified type
    :param content: vim.Content to search in
    :param vimtype: List of vimtype objects to look for
    :param name: string name of the object
    :param container: Container to search in [default: content.rootFolder]
    :param recursive: Recursively descend or only look in the current level [default: True]
    :return: The vimtype object found with the specified name, or None if no object was found
    """
    container = content.viewManager.CreateContainerView(container if container else content.rootFolder,
                                                        vimtype, recursive)
    obj = None
    for c in container.view:
        if c.name.lower() == name.lower():
            obj = c
            break
    container.Destroy()
    return obj


# From: https://github.com/sijis/pyvmomi-examples/vmutils.py
def get_objs(content, vimtype, container=None, recursive=True):
    """
    Get all the vSphere objects associated with a given type
    :param content: vim.Content to search in
    :param vimtype: Object to search for
    :param container: Container to search in [default: content.rootFolder]
    :param recursive: Recursively descend or only look in the current level [default: True]
    :return: List of all vimtype objects found, or None if none were found
    """
    obj = []
    container = content.viewManager.CreateContainerView(container if container else content.rootFolder,
                                                        vimtype, recursive)
    for c in container.view:
        obj.append(c)
    container.Destroy()
    return obj


def get_item(content, vimtype, name):
    """
    Get a item of specified name and type from content
    :param content: Content to search in
    :param vimtype: Type of item
    :param name: Name of item
    :return: The item found
    """
    if not name:
        return get_objs(content, [vimtype])[0]
    else:
        return get_obj(content, [vimtype], name)


def map_objs(content, vimtype, func, name=None, container=None, recursive=True):
    """
    Apply a function to item(s)
    :param content: vim.Content to search in
    :param vimtype: List of vimtype objects to look for
    :param func: Function to apply
    :param name: Name of item to apply to [default: None]
    :param container: Container to search in [default: content.rootFolder]
    :param recursive: Recursively descend or only look in the current level [default: True]
    """
    container = content.viewManager.CreateContainerView(container if container else content.rootFolder,
                                                        vimtype, recursive)
    for item in container.view:
        if name:
            if hasattr(item, 'name') and item.name.lower() == name.lower():
                func(item)
        else:
            func(item)


# Similar to: https://docs.python.org/3/library/pprint.html


# From: list_dc_datastore_info.py in pyvmomi-community-samples
def get_datastore_info(ds_obj):
    """
    Gets a human-readable summary of a Datastore
    :param ds_obj: vim.Datastore
    :return: String with datastore information
    """
    if not ds_obj:
        logging.error("No Datastore was given to get_datastore_info")
        return None
    import adles.utils as utils
    info_string = "\n"
    summary = ds_obj.summary
    ds_capacity = summary.capacity
    ds_freespace = summary.freeSpace
    ds_uncommitted = summary.uncommitted if summary.uncommitted else 0
    ds_provisioned = ds_capacity - ds_freespace + ds_uncommitted
    ds_overp = ds_provisioned - ds_capacity
    ds_overp_pct = (ds_overp * 100) / ds_capacity if ds_capacity else 0

    info_string += "Name                  : %s\n" % summary.name
    info_string += "URL                   : %s\n" % summary.url
    info_string += "Capacity              : %s\n" % utils.sizeof_fmt(ds_capacity)
    info_string += "Free Space            : %s\n" % utils.sizeof_fmt(ds_freespace)
    info_string += "Uncommitted           : %s\n" % utils.sizeof_fmt(ds_uncommitted)
    info_string += "Provisioned           : %s\n" % utils.sizeof_fmt(ds_provisioned)
    if ds_overp > 0:
        info_string += "Over-provisioned      : %s / %s %%\n" % (utils.sizeof_fmt(ds_overp), ds_overp_pct)
    info_string += "Hosts                 : %s\n" % str(len(ds_obj.host))
    info_string += "Virtual Machines      : %s" % str(len(ds_obj.vm))
    return info_string


def is_folder(obj):
    """
    Checks if object is a vim.Folder
    :param obj: object to check
    :return: Bool
    """
    return bool(hasattr(obj, "childEntity"))


def is_vm(obj):
    """
    Checks if object is a vim.VirtualMachine
    :param obj: object to check
    :return: Bool
    """
    return bool(hasattr(obj, "summary"))


def is_vnic(device):
    """
    Checks if the device is a VirtualEthernetCard
    :param device: device to check
    :return: Bool
    """
    return bool(isinstance(device, vim.vm.device.VirtualEthernetCard))
