#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyVmomi import vim
from pyVmomi import vmodl


# From: various files in pyvmomi-community-samples
def get_obj(content, vimtype, name):
    """
    Recursively finds and returns named object of specified type
    :param content:
    :param vimtype:
    :param name:
    :return: The object found with the specified name, or None if no object was found
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


# From: https://github.com/sijis/pyvmomi-examples/vmutils.py
def get_objs(content, vimtype):
    """
    Get ALL the vSphere objects associated with a given type
    :param content:
    :param vimtype: vim type to find
    :return: List of all vimtype objects found
    """
    obj = []
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        obj.append(c)
    return obj


# TODO: function to apply a given operation to all objects in a view


# From: tools/tasks.py in pyvmomi-community-samples
def wait_for_tasks(service_instance, tasks):
    """
    Given the service instance si and tasks, it returns after all the tasks are complete
    :param service_instance:
    :param tasks:
    """
    property_collector = service_instance.content.propertyCollector
    task_list = [str(task) for task in tasks]
    # Create filter
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                 for task in tasks]
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                               pathSet=[],
                                                               all=True)
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = [property_spec]
    pcfilter = property_collector.CreateFilter(filter_spec, True)
    try:
        version, state = None, None
        # Loop looking for updates till the state moves to a completed state.
        while len(task_list):
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
                            # Remove task from taskList
                            task_list.remove(str(task))
                        elif state == vim.TaskInfo.State.error:
                            raise task.info.error
            # Move to next version
            version = update.version
    finally:
        if pcfilter:
            pcfilter.Destroy()


# From: clone_vm.py in pyvmomi-community-samples
def wait_for_task(task):
    """
    Wait for a single vCenter task to finish and return it's result
    :param task:  vim.Task object of the task to wait for
    :return:  Task result information
    """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print
            "there was an error"
            task_done = True


def move_into_folder(folder, entity_list):
    """
    Moves a list of managed entities into the named folder. The folder's type MUST match those of the entity_list!
    :param folder: vim.Folder object
    :param entity_list: List of vim.ManagedEntity
    """
    folder.MoveIntoFolder_Task(entity_list)


def destroy_everything(folder):
    """
    Unregisters and deletes all VMs and Folders under the given folder
    :param folder: vim.Folder object
    """
    folder.UnregisterAndDestroy_Task()
