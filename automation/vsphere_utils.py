#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyVmomi import vim
from pyVmomi import vmodl
from sys import stdout

# From: various files in pyvmomi-community-samples
def get_obj(content, vimtype, name):
    """
    Recursively finds and returns named object of specified type
    :param content: vim.Content to search in
    :param vimtype: List of vimtype objects to look for
    :param name: string name of the object
    :return: The vimtype object found with the specified name, or None if no object was found
    """
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    obj = None
    for c in container.view:
        if c.name == name:
            obj = c
            break
    container.Destroy()
    return obj


# From: https://github.com/sijis/pyvmomi-examples/vmutils.py
def get_objs(content, vimtype):
    """
    Get ALL the vSphere objects associated with a given type
    :param content: vim.Content to search in
    :param vimtype: List of vimtype objects to look for
    :return: List of all vimtype objects found
    """
    obj = []
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        obj.append(c)
    container.Destroy()
    return obj


# TODO: function to apply a given operation to all objects in a view


# From: tools/tasks.py in pyvmomi-community-samples
def wait_for_tasks(service_instance, tasks):
    """
    Given the service instance si and tasks, it returns after all the tasks are complete
    :param service_instance: Service instance as returned by pyVim.connect.SmartConnect()
    :param tasks: List of tasks to wait for
    """
    property_collector = service_instance.content.propertyCollector
    task_list = [str(task) for task in tasks]
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task) for task in tasks]  # Create filter
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
    Wait for a single vCenter task to finish and return it's result
    :param task:  vim.Task object of the task to wait for
    :return: Task result information
    """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result
        if task.info.state == 'error':
            print("There was an error while completing task ", task.name)
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
    print("Unregistering and deleting EVERYTHING in folder {}".format(folder.name))
    folder.UnregisterAndDestroy_Task()


# From: list_dc_datastore_info.py in pyvmomi-community-samples
# http://stackoverflow.com/questions/1094841/
def sizeof_fmt(num):
    """
    Returns the human readable version of a file size
    :param num:
    :return:
    """
    for item in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, item)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


# From: list_dc_datastore_info.py in pyvmomi-community-samples
def print_datastore_info(ds_obj):
    """
    Prints human-readable summary of a Datastore
    :param ds_obj: vim.Datastore
    """
    summary = ds_obj.summary
    ds_capacity = summary.capacity
    ds_freespace = summary.freeSpace
    ds_uncommitted = summary.uncommitted if summary.uncommitted else 0
    ds_provisioned = ds_capacity - ds_freespace + ds_uncommitted
    ds_overp = ds_provisioned - ds_capacity
    ds_overp_pct = (ds_overp * 100) / ds_capacity if ds_capacity else 0
    print("Name                  : {}".format(summary.name))
    print("URL                   : {}".format(summary.url))
    print("Capacity              : {} GB".format(sizeof_fmt(ds_capacity)))
    print("Free Space            : {} GB".format(sizeof_fmt(ds_freespace)))
    print("Uncommitted           : {} GB".format(sizeof_fmt(ds_uncommitted)))
    print("Provisioned           : {} GB".format(sizeof_fmt(ds_provisioned)))
    if ds_overp > 0:
        print("Over-provisioned      : {} GB / {} %".format(sizeof_fmt(ds_overp), ds_overp_pct))
    print("Hosts                 : {}".format(len(ds_obj.host)))
    print("Virtual Machines      : {}".format(len(ds_obj.vm)))


# From: virtual_machine_power_cycle_and_question.py in pyvmomi-community-samples
def _create_char_spinner():
    """ Creates a generator yielding a char based spinner """
    while True:
        for c in '|/-\\':
            yield c

_spinner = _create_char_spinner()


def spinner(label=''):
    """
    Prints label with a spinner. When called repeatedly from inside a loop this prints a one line CLI spinner.
    :param label: (Optional) The message to display while spinning (e.g "Loading", or the current percentage)
    """
    stdout.write("\r\t%s %s" % (label, next(_spinner)))
    stdout.flush()
