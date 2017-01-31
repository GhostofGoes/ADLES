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
    :return:
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

# TODO: function to apply a given operation to all objects in a view


# From: tools/tasks.py in pyvmomi-community-samples
def wait_for_tasks(service_instance, tasks):
    """
    Given the service instance si and tasks, it returns after all the tasks are complete
    :param service_instance:
    :param tasks:
    :return:
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


# From: getallvms.py in pyvmomi-community-samples
def print_vm_info(virtual_machine):
    """
    Print human-readable information for a virtual machine object
    :param virtual_machine:
    :return:
    """
    summary = virtual_machine.summary
    print("Name          : ", summary.config.name)
    print("Template      : ", summary.config.template)
    print("Path          : ", summary.config.vmPathName)
    print("Guest         : ", summary.config.guestFullName)
    print("Instance UUID : ", summary.config.instanceUuid)
    print("Bios UUID     : ", summary.config.uuid)
    print("State         : ", summary.runtime.powerState)
    if summary.guest:
        print("VMware-tools  : ", summary.guest.toolsStatus)
        print("IP            : ", summary.guest.ipAddress)
    if summary.runtime.question:
        print("Question  : ", summary.runtime.question.text)
    if summary.config.annotation:
        print("Annotation    : ", summary.config.annotation)
