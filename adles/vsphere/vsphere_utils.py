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
from posixpath import split  # We want to always parse as forward-slashes, regardless of platform we're running on

from pyVmomi import vim


# From: clone_vm.py in pyvmomi-community-samples
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
            logging.debug("Task result: '%s'", str(task.info.result))
            return task.info.result
        elif task.info.state == 'error':
            logging.error("There was an error while completing a task: '%s'", str(task.info.error.msg))
            return None


def check_folder(func):
    """
    Wrapper that checks that folder type is properly defined
    :param func: Function to wrap
    :return: Wrapped function
    """
    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], vim.Folder):
            return func(*args)
        elif kwargs and isinstance(kwargs["folder"], vim.Folder):
            return func(**kwargs)
        else:
            logging.error("Invalid type for a folder passed to function %s: %s", str(func.__name__),
                          str(type(kwargs["folder"] if kwargs and "folder" in kwargs else args[0])))
    return wrapper


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


@check_folder
def get_in_folder(folder, name, recursive=False, vimtype=None):
    """
    Retrieves an item from a datacenter folder
    :param folder: vim.Folder to search in
    :param name: Name of object to find
    :param recursive: Recurse into sub-folders [default: False]
    :param vimtype: Type of object to search for [default: None]
    :return: Object found or None if nothing was found
    """
    if name:
        item = find_in_folder(folder, name, recursive=recursive, vimtype=vimtype)
    else:
        item = None
    if not item:
        if len(folder.childEntity) > 0:
            if not vimtype:
                return folder.childEntity[0]
            else:
                for item in folder.childEntity:
                    if isinstance(item, vimtype):
                        return item
                return None
        else:
            logging.error("There are no items in folder %s", folder.name)
            return None
    else:
        return item


@check_folder
def find_in_folder(folder, name, recursive=False, vimtype=None):
    """
    Finds and returns an specific object in a folder
    :param folder: vim.Folder object to search in
    :param name: Name of the object to find
    :param recursive: Recurse into sub-folders [default: False]
    :param vimtype: Type of object to search for [default: None]
    :return: Object found or None if nothing was found
    """
    for item in folder.childEntity:
        if hasattr(item, 'name') and item.name.lower() == name.lower():  # Check if it has name, and if the name matches
            if vimtype and not isinstance(item, vimtype):
                continue
            return item
        elif recursive and is_folder(item):  # Recurse into sub-folders
            find_in_folder(folder=item, name=name, recursive=recursive, vimtype=vimtype)
    return None


@check_folder
def traverse_path(root, path):
    """
    Traverses a folder path to find a object with a specific name
    :param root: vim.Folder root to search in
    :param path: String with path in POSIX format (Example: Templates/Servers/Windows/ to get the 'Windows' folder)
    :return: Object at end of path
    """
    logging.debug("Traversing path. Root: '%s'\tPath: '%s'", root.name, path)
    folder_path, name = split(path)         # Separate basename, if any
    folder_path = folder_path.lower().split('/')    # Transform into list

    current = root
    for folder in folder_path:
        for item in current.childEntity:
            if is_folder(item) and item.name.lower() == folder:
                current = item      # Found the next folder in path,
                break               # Break to check this folder for next part of the path

    if name:  # Look for item with a specific name
        for item in current.childEntity:
            if (is_vm(item) or is_folder(item)) and item.name.lower() == name.lower():
                return item
        logging.error("Could not find item %s while traversing path '%s' from root '%s'", name, path, root.name)
        return None
    else:  # Just return whatever we found
        return current


@check_folder
def enumerate_folder(folder, recursive=True):
    """
    Enumerates a folder structure and returns the result as a python object with the same structure
    :param folder: vim.Folder
    :param recursive: Whether to recurse into any sub-folders [default: True]
    :return: The nested python object with the enumerated folder structure
    """
    children = []
    for item in folder.childEntity:
        if is_folder(item):
            if recursive:
                children.append(enumerate_folder(item, recursive))
            else:
                children.append('- ' + item.name)
        elif is_vm(item):
            children.append('* ' + item.name)
        else:
            children.append("UNKNOWN ITEM: %s" % str(item))
    return '+ ' + folder.name, children  # Return tuple of parent and children


# Similar to: https://docs.python.org/3/library/pprint.html
def format_structure(structure, indent=4, _depth=0):
    """
    Converts a nested structure of folders into a formatted string
    :param structure: structure to format
    :param indent: Number of spaces to indent each level of nesting [default: 4]
    :param _depth: Current depth (USE INTERNALLY BY FUNCTION)
    :return: Formatted string
    """
    fmat = ""
    newline = '\n' + str(_depth * str(indent * ' '))

    if type(structure) == tuple:
        fmat += newline + str(structure[0])
        fmat += format_structure(structure[1], indent, _depth + 1)
    elif type(structure) == list:
        for item in structure:
            fmat += format_structure(item, indent, _depth)
    elif type(structure) == str:
        fmat += newline + structure
    else:
        logging.error("Unexpected type in folder structure for item %s: %s", str(structure), str(type(structure)))
    return fmat


@check_folder
def move_into_folder(folder, entity_list):
    """
    Moves a list of managed entities into the named folder.
    :param folder: vim.Folder object with type matching the entity list
    :param entity_list: List of vim.ManagedEntity
    """
    wait_for_task(folder.MoveIntoFolder_Task(entity_list))


@check_folder
def create_folder(folder, folder_name):
    """
    Creates a VM folder in the specified folder
    :param folder: vim.Folder object to create the folder in
    :param folder_name: Name of folder to create
    :return: The created vim.Folder object
    """
    # "folder" is confusing, but only way I can use wrapper for now....
    exists = find_in_folder(folder, folder_name)  # Check if the folder already exists
    if exists:
        logging.warning("Folder '%s' already exists in folder '%s'", folder_name, folder.name)
        return exists  # Return the folder that already existed
    else:
        logging.debug("Creating folder '%s' in folder '%s'", folder_name, folder.name)
        try:
            return folder.CreateFolder(folder_name)  # Create the folder and return it
        except vim.fault.DuplicateName as dupe:
            logging.error("Could not create folder '%s' in '%s': folder already exists as '%s'",
                          folder_name, folder.name, dupe.name)
        except vim.fault.InvalidName as invalid:
            logging.error("Could not create folder '%s' in '%s': Invalid folder name '%s'",
                          folder_name, folder.name, invalid.name)
    return None


@check_folder
def cleanup(folder, prefix=None, recursive=False, destroy_folders=False, destroy_self=False):
    """
    Destroys VMs and (optionally) folders under the specified folder.
    :param folder: vim.Folder object
    :param prefix: Only destroy VMs with names starting with the prefix [default: None]
    :param recursive: Recursively descend into any sub-folders [default: False]
    :param destroy_folders: Destroy folders in addition to VMs [default: False]
    :param destroy_self: Destroy the folder specified [default: False]
    """
    logging.debug("Cleaning folder %s", folder.name)
    from adles.vsphere.vm_utils import destroy_vm
    for item in folder.childEntity:
        if is_vm(item):  # Handle VMs
            if prefix:
                if str(item.name).startswith(prefix):  # Only destroy the VM if it begins with the prefix
                    destroy_vm(item)
            else:
                destroy_vm(item)  # This ensures the VM folders get deleted off the datastore
        elif is_folder(item):  # Handle folders
            if recursive or destroy_folders:  # Destroys folder and it's sub-objects
                cleanup(item, prefix, recursive, destroy_folders, destroy_self=destroy_folders)
        else:  # It's not a VM or a folder...
            logging.warning("Unknown item encountered while cleaning in folder '%s': %s", folder.name, str(item))
    if destroy_self:  # Note: UnregisterAndDestroy does not delete VM files off datastore
        wait_for_task(folder.UnregisterAndDestroy_Task())  # Final cleanup


@check_folder
def retrieve_items(folder, prefix=None, recursive=False):
    """
    Retrieves VMs and folders from a folder structure
    :param folder: vim.Folder to begin search in (is NOT returned in list of folders)
    :param prefix: Prefix to search for [default: None]
    :param recursive: Recursively descend into sub-folders [default: False]
    :return: ([VMs], [folders])
    """
    vms = []
    folders = []

    for item in folder.childEntity:
        if prefix:
            if is_vm(item) and str(item.name).startswith(prefix):
                vms.append(item)
            elif is_folder(item) and str(item.name).startswith(prefix):
                folders.append(item)
        else:
            if is_vm(item):
                vms.append(item)
            elif is_folder(item):
                folders.append(item)

        if recursive and is_folder(item):
            v, f = retrieve_items(item, prefix, recursive)
            vms.extend(v)
            folders.extend(f)
    return vms, folders


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
    from adles.utils import sizeof_fmt
    info_string = "\n"

    summary = ds_obj.summary
    ds_capacity = summary.capacity
    ds_freespace = summary.freeSpace
    ds_uncommitted = summary.uncommitted if summary.uncommitted else 0
    ds_provisioned = ds_capacity - ds_freespace + ds_uncommitted
    ds_overp = ds_provisioned - ds_capacity
    ds_overp_pct = (ds_overp * 100) / ds_capacity if ds_capacity else 0

    info_string += "Name                  : %s" % summary.name
    info_string += "URL                   : %s" % summary.url
    info_string += "Capacity              : %s" % sizeof_fmt(ds_capacity)
    info_string += "Free Space            : %s" % sizeof_fmt(ds_freespace)
    info_string += "Uncommitted           : %s" % sizeof_fmt(ds_uncommitted)
    info_string += "Provisioned           : %s" % sizeof_fmt(ds_provisioned)
    if ds_overp > 0:
        info_string += "Over-provisioned      : %s / %s %%" % (sizeof_fmt(ds_overp), ds_overp_pct)
    info_string += "Hosts                 : %s" % str(len(ds_obj.host))
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
