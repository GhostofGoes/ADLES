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
from os.path import split

from pyVmomi import vim

from adles.vsphere.vsphere_utils import is_folder, is_vm, wait_for_task


def check_folder(func):
    """
    Wrapper that checks that folder type is properly defined
    :param func: Function to wrap
    :return: Wrapped function
    """
    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], vim.Folder):
            return func(*args, **kwargs)
        elif kwargs and isinstance(kwargs["folder"], vim.Folder):
            return func(*args, **kwargs)
        else:
            logging.error("Invalid type for a folder passed to function %s: %s", str(func.__name__),
                          str(type(kwargs["folder"] if kwargs and "folder" in kwargs else args[0])))
    return wrapper


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
        if hasattr(item, 'name') and item.name.lower() == name.lower():  # Check if the name matches
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
    logging.debug("Traversing path '%s' from root '%s'", path, root.name)

    folder_path, name = split(path)                 # Separate basename, if any
    folder_path = folder_path.lower().split('/')    # Transform into list

    current = root                          # Start with the defined root
    for folder in folder_path:              # Try each folder name in the path
        for item in current.childEntity:    # Iterate through items in the current folder
            if is_folder(item) and item.name.lower() == folder:  # Match if the item is part of the path
                current = item  # This is the next folder in the path
                break           # Break to outer loop to check this folder for the next part of the path

    if name:  # Look for item with a specific name (basically, the split had a basename)
        for item in current.childEntity:
            if (is_vm(item) or is_folder(item)) and item.name.lower() == name.lower():
                return item
        logging.debug("Could not find item %s while traversing path '%s' from root '%s'", name, path, root.name)
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
        logging.error("Unexpected type in folder structure for item %s: %s",
                      str(structure), str(type(structure)))
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
def cleanup(folder, vm_prefix=None, folder_prefix=None, recursive=False,
            destroy_folders=False, destroy_self=False):
    """
    Destroys VMs and (optionally) folders under the specified folder.
    :param folder: vim.Folder object
    :param vm_prefix: Only destroy VMs with names starting with the prefix [default: None]
    :param folder_prefix: Only destroy or search in Folders with names starting with the prefix [default: None]
    :param recursive: Recursively descend into any sub-folders [default: False]
    :param destroy_folders: Destroy folders in addition to VMs [default: False]
    :param destroy_self: Destroy the folder specified [default: False]
    """
    logging.debug("Cleaning folder '%s'", folder.name)
    import adles.vsphere.vm_utils as vm_utils

    for item in folder.childEntity:
        if is_vm(item):         # Handle VMs
            if vm_prefix:       # If prefix is set, match only if name begins with it
                if str(item.name).startswith(vm_prefix):  # Only destroy the VM if it begins with the prefix
                    vm_utils.destroy_vm(item)  # Delete the VM from the Datastore and remove from registry
            else:
                vm_utils.destroy_vm(item)  # Delete the VM from the Datastore and remove from registry
        elif is_folder(item):   # Handle folders
            if folder_prefix:   # If prefix is set, match only if name begins with it
                if str(item.name).startswith(folder_prefix):
                    if destroy_folders:  # Destroys folder and ALL of it's sub-objects
                        cleanup(folder=item, vm_prefix=None, folder_prefix=None, recursive=True,
                                destroy_folders=True, destroy_self=True)
                    elif recursive:  # Simply recurses to find more VMs
                        cleanup(folder=item, vm_prefix=vm_prefix, folder_prefix=folder_prefix,
                                recursive=True, destroy_folders=False, destroy_self=False)
            else:
                if destroy_folders:  # Destroys folder and ALL of it's sub-objects
                    cleanup(folder=item, vm_prefix=None, folder_prefix=None, recursive=True,
                            destroy_folders=True, destroy_self=True)
                elif recursive:  # Simply recurses to find more items
                    cleanup(folder=item, vm_prefix=vm_prefix, folder_prefix=folder_prefix,
                            recursive=True, destroy_folders=False, destroy_self=False)
        else:  # It's not a VM or a folder...
            logging.error("Unknown item encountered while cleaning in folder '%s': %s",
                          folder.name, str(item))

    # Note: UnregisterAndDestroy does NOT delete VM files off datastore, only use if folder is empty
    if destroy_self:
        logging.debug("Unregistering and Destroying folder: '%s'", folder.name)
        wait_for_task(folder.UnregisterAndDestroy_Task())


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

        if recursive and is_folder(item):  # Recurse into sub-folders
            v, f = retrieve_items(item, prefix, recursive)
            vms.extend(v)
            folders.extend(f)
    return vms, folders
