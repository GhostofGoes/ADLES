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
    :return: Task result information (task.info.result)
    """
    if not task:  # Check if there's actually a task
        logging.error("No task was specified to wait for")
        return None
    name = str(task.info.descriptionId)
    obj = str(task.info.entityName)
    try:
        while True:  # TODO: set a timeout, perhaps based on type of task
            if task.info.state == 'success':
                return task.info.result
            elif task.info.state == 'error':
                logging.error("Error during task %s on object '%s': %s",
                              name, obj, str(task.info.error.msg))
                return None
    except vim.fault.NoPermission as e:
        logging.error("Permission denied for task %s on %s: need privilege %s",
                      name, obj, e.privilegeId)
    except vim.fault.TaskInProgress as e:
        logging.error("Cannot complete task %s: task %s is already in progress on %s",
                      name, e.task.info.name, obj)
    except vim.fault.InvalidPowerState as e:
        logging.error("Cannot complete task %s: %s is in invalid power state %s",
                      name, obj, e.existingState)
    except vim.fault.InvalidState as e:
        logging.error("Cannot complete task %s: invalid state for %s\n%s", name, obj, str(e))
    except vim.fault.CustomizationFault:
        logging.error("Cannot complete task %s: invalid customization for %s", name, obj)
    except vim.fault.VmConfigFault:
        logging.error("Cannot complete task %s: invalid configuration for VM %s", name, obj)
    except vim.fault.InvalidName as e:
        logging.error("Cannot complete task %s for object %s: name '%s' is not valid",
                      name, obj, e.name)
    except vim.fault.DuplicateName as e:
        logging.error("Cannot complete task %s for %s: there is a duplicate named %s",
                      name, obj, e.name)
    except vim.fault.InvalidDatastore as e:
        logging.error("Cannot complete task %s for %s: invalid Datastore '%s'",
                      name, obj, e.datastore)
    except vim.fault.AlreadyExists:
        logging.error("Cannot complete task %s: %s already exists", name, obj)
    except vim.fault.NotFound:
        logging.error("Cannot complete task %s: %s does not exist", name, obj)
    except vim.fault.ResourceInUse:
        logging.error("Cannot complete task %s: resource %s is in use", name, obj)
    finally:
        return None


# From: list_dc_datastore_info in pyvmomi-community-samples
def get_datastore_info(ds_obj):
    """
    Gets a human-readable summary of a Datastore
    :param ds_obj: vim.Datastore
    :return: String with datastore information
    """
    if not ds_obj:
        logging.error("No Datastore was given to get_datastore_info")
        return ""
    from adles.utils import sizeof_fmt
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
    info_string += "Capacity              : %s\n" % sizeof_fmt(ds_capacity)
    info_string += "Free Space            : %s\n" % sizeof_fmt(ds_freespace)
    info_string += "Uncommitted           : %s\n" % sizeof_fmt(ds_uncommitted)
    info_string += "Provisioned           : %s\n" % sizeof_fmt(ds_provisioned)
    if ds_overp > 0:
        info_string += "Over-provisioned      : %s / %s %%\n" \
                       % (sizeof_fmt(ds_overp), ds_overp_pct)
    info_string += "Hosts                 : %d\n" % len(ds_obj.host)
    info_string += "Virtual Machines      : %d" % len(ds_obj.vm)
    return info_string


def is_folder(obj):
    """
    Checks if object is a vim.Folder
    :param obj: object to check
    :return: Bool
    """
    return hasattr(obj, "childEntity")


def is_vm(obj):
    """
    Checks if object is a vim.VirtualMachine
    :param obj: object to check
    :return: Bool
    """
    return hasattr(obj, "summary")


def is_vnic(device):
    """
    Checks if the device is a VirtualEthernetCard
    :param device: device to check
    :return: Bool
    """
    return isinstance(device, vim.vm.device.VirtualEthernetCard)
