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
from pyVmomi import vmodl
from posixpath import split  # We want to always parse as forward-slashes, regardless of platform we're running on


# From: various files in pyvmomi-community-samples
def get_obj(content, vimtype, name, recursive=True):
    """
    Finds and returns named vSphere object of specified type
    :param content: vim.Content to search in
    :param vimtype: List of vimtype objects to look for
    :param name: string name of the object
    :param recursive: (Optional) Whether to recursively descend or only look in the current level
    :return: The vimtype object found with the specified name, or None if no object was found
    """
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, recursive)
    obj = None
    for c in container.view:
        if c.name == name:
            obj = c
            break
    container.Destroy()
    return obj


# From: https://github.com/sijis/pyvmomi-examples/vmutils.py
def get_objs(content, vimtype, recursive=True):
    """
    Get all the vSphere objects associated with a given type
    :param content: vim.Content to search in
    :param vimtype: List of vimtype objects to look for
    :param recursive: (Optional) Whether to recursively descend or only look in the current level
    :return: List of all vimtype objects found, or None if none were found
    """
    obj = []
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, recursive)
    for c in container.view:
        obj.append(c)
    container.Destroy()
    return obj


def get_item(content, vimtype, name):
    """
    Get a item of specified name and type from content
    :param content:
    :param vimtype:
    :param name:
    :return:
    """
    if not name:
        return get_objs(content, [vimtype])[0]
    else:
        return get_obj(content, [vimtype], name)

# TODO: function to apply a given operation to all objects in a view


def find_in_folder(folder, name, recursive=False):
    """
    Finds and returns an object in a folder
    :param folder: vim.Folder object to search in
    :param name: Name of the object to find
    :param recursive: Recurse into sub-folders [default: False]
    :return: Object found or None if nothing was found
    """
    for item in folder.childEntity:
        if hasattr(item, 'name') and item.name == name:  # Check if it has name, and if the name matches
            return item
        elif recursive and is_folder(item):  # Recurse into sub-folders
            find_in_folder(folder=item, name=name, recursive=recursive)
    return None


def traverse_path(root, path):
    """
    Traverses a folder path to find a object with a specific name
    :param root: vim.Folder root to search in
    :param path: String with path in POSIX format (Example: Templates/Servers/Windows/ to get the 'Windows' folder)
    :return: Object at end of path
    """
    logging.debug("Traversing path. Root: %s\tPath: %s", root.name, path)
    folder_path, name = split(path)         # Separate basename, if any
    folder_path = folder_path.split('/')    # Transform into list

    current = root
    for folder in folder_path:
        for item in current.childEntity:
            if is_folder(item) and item.name == folder:
                current = item      # Found the next folder in path,
                break               # Break to check this folder for next part of the path

    if name:  # Look for item with a specific name
        for item in current.childEntity:
            if (is_vm(item) or is_folder(item)) and item.name == name:
                return item
        logging.error("Could not find item %s while traversing path %s from root %s", name, path, root.name)
        return None
    else:  # Just return whatever we found
        return current


def enumerate_folder(folder, recursive=True):
    """
    Enumerates a folder structure and returns the result as a python object with the same structure
    :param folder: vim.Folder
    :param recursive: Whether to recurse into any sub-folders
    :return: The nested python object with the enumerated folder structure
    """
    children = []
    for item in folder.childEntity:
        if is_folder(item):
            if recursive:
                children.append(enumerate_folder(item, recursive))
            else:
                children.append(item)
        elif is_vm(item):
            children.append(item)
        else:
            children.append("UNKNOWN ITEM: %s" % str(item))
    return {folder.name, children}


# From: tools/tasks.py in pyvmomi-community-samples
def wait_for_tasks(service_instance, tasks):
    """
    Waits for a list of tasks to complete
    :param service_instance: Service instance as returned by pyVim.connect.SmartConnect()
    :param tasks: List of tasks to wait for
    """
    if not tasks:
        logging.error("No tasks were specified to wait for")
        return None
    logging.debug("Waiting for tasks. Instance: %s\tTasks: %s", str(service_instance), str(tasks))
    property_collector = service_instance.content.propertyCollector
    task_list = [str(task) for task in tasks]
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task) for task in tasks]
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task, pathSet=[], all=True)
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = [property_spec]
    pcfilter = property_collector.CreateFilter(filter_spec, True)
    try:
        version, state = None, None
        while len(task_list):  # Loop looking for updates till the state moves to a completed state
            update = property_collector.WaitForUpdates(version)
            for filter_set in update.filterSet:
                for obj_set in filter_set.objectSet:
                    task = obj_set.obj
                    for change in obj_set.changeSet:
                        if change.name == 'info':
                            state = change.val.state
                        elif change.name == 'info.state':
                            state = change.val
                        else:
                            continue

                        if not str(task) in task_list:
                            continue

                        if state == vim.TaskInfo.State.success:
                            task_list.remove(str(task))  # Remove task from taskList
                        elif state == vim.TaskInfo.State.error:
                            raise task.info.error
            version = update.version  # Move to next version
    finally:
        if pcfilter:
            pcfilter.Destroy()


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
            logging.debug("Task result: %s", str(task.info.result))
            return task.info.result
        elif task.info.state == 'error':
            logging.error("There was an error while completing a task: %s", str(task.info.error.msg))
            return None


def move_into_folder(folder, entity_list):
    """
    Moves a list of managed entities into the named folder.
    :param folder: vim.Folder object with type matching the entity list
    :param entity_list: List of vim.ManagedEntity
    """
    wait_for_task(folder.MoveIntoFolder_Task(entity_list))


def cleanup(folder, prefix=None, recursive=False, destroy_folders=False, destroy_self=False):
    """
    Destroys VMs and (optionally) folders under the specified folder.
    :param folder: vim.Folder object
    :param prefix: Only destroy VMs with names starting with the prefix [default: None]
    :param recursive: Recursively descend into any sub-folders [default: False]
    :param destroy_folders: Destroy folders in addition to VMs [default: False]
    :param destroy_self: Destroy the folder specified [default: False]
    """
    if folder:  # Checks to make sure folder is not None
        from automation.vsphere.vm_utils import destroy_vm
        logging.info("Cleaning folder %s", folder.name)
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
                logging.warning("Unknown item encountered while cleaning in folder %s: %s", folder.name, str(item))
        if destroy_self:  # Note: UnregisterAndDestroy does not delete VM files off datastore
            wait_for_task(folder.UnregisterAndDestroy_Task())  # Final cleanup
    else:
        logging.error("Cannot destroy a None object!")


# From: list_dc_datastore_info.py in pyvmomi-community-samples
def print_datastore_info(ds_obj):
    """
    Prints human-readable summary of a Datastore
    :param ds_obj: vim.Datastore
    """
    from automation.utils import sizeof_fmt
    summary = ds_obj.summary
    ds_capacity = summary.capacity
    ds_freespace = summary.freeSpace
    ds_uncommitted = summary.uncommitted if summary.uncommitted else 0
    ds_provisioned = ds_capacity - ds_freespace + ds_uncommitted
    ds_overp = ds_provisioned - ds_capacity
    ds_overp_pct = (ds_overp * 100) / ds_capacity if ds_capacity else 0
    logging.info("Name                  : %s", summary.name)
    logging.info("URL                   : %s", summary.url)
    logging.info("Capacity              : %s", sizeof_fmt(ds_capacity))
    logging.info("Free Space            : %s", sizeof_fmt(ds_freespace))
    logging.info("Uncommitted           : %s", sizeof_fmt(ds_uncommitted))
    logging.info("Provisioned           : %s", sizeof_fmt(ds_provisioned))
    if ds_overp > 0:
        logging.info("Over-provisioned      : %s / %s %%", sizeof_fmt(ds_overp), ds_overp_pct)
    logging.info("Hosts                 : %s", (len(ds_obj.host)))
    logging.info("Virtual Machines      : %s", (len(ds_obj.vm)))


def is_folder(obj):
    """
    Checks if object is a vim.Folder
    :param obj: object to check
    :return:
    """
    return hasattr(obj, "childEntity")


def is_vm(obj):
    """
    Checks if object is a vim.VirtualMachine
    :param obj: object to check
    :return:
    """
    return hasattr(obj, "summary")
