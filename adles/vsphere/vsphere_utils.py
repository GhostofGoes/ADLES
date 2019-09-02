import logging
from time import sleep, time

from pyVmomi import vim

from adles.utils import read_json, user_input

SLEEP_INTERVAL = 0.05
LONG_SLEEP = 1.0


class VsphereException(Exception):
    pass


def wait_for_task(task, timeout=60.0, pause_timeout=True):
    """
    Waits for a single vim.Task to finish and returns its result.

    :param task: The task to wait for
    :type task: vim.Task
    :param float timeout: Number of seconds to wait before terminating task
    :param bool pause_timeout: Pause timeout counter while task
    is queued on server
    :return: Task result information (task.info.result)
    :rtype: str or None
    """
    if not task:  # Check if there's actually a task
        logging.error("No task was specified to wait for")
        return None
    name = str(task.info.descriptionId)
    obj = str(task.info.entityName)
    wait_time = 0.0
    end_time = time() + float(timeout)  # Set end time
    try:
        while True:
            if task.info.state == 'success':  # It succeeded!
                # Return the task result if it was successful
                return task.info.result
            elif task.info.state == 'error':  # It failed...
                logging.error("Error during task %s on object '%s': %s",
                              name, obj, str(task.info.error.msg))
                return None
            elif time() > end_time:  # Check if it has exceeded the timeout
                logging.error("Task %s timed out after %s seconds",
                              name, str(wait_time))
                task.CancelTask()  # Cancel the task since we've timed out
                return None
            elif task.info.state == 'queued':
                sleep(LONG_SLEEP)  # Sleep longer if it's queued up on system
                # Don't count queue time against the timeout
                if pause_timeout is True:
                    end_time += LONG_SLEEP
                wait_time += LONG_SLEEP
            else:
                # Wait a bit so we don't waste resources checking state
                sleep(SLEEP_INTERVAL)
                wait_time += SLEEP_INTERVAL
    except vim.fault.NoPermission as e:
        logging.error("Permission denied for task %s on %s: need privilege %s",
                      name, obj, e.privilegeId)
    except vim.fault.TaskInProgress as e:
        logging.error("Cannot complete task %s: "
                      "task %s is already in progress on %s",
                      name, e.task.info.name, obj)
    except vim.fault.InvalidPowerState as e:
        logging.error("Cannot complete task %s: "
                      "%s is in invalid power state %s",
                      name, obj, e.existingState)
    except vim.fault.InvalidState as e:
        logging.error("Cannot complete task %s: "
                      "invalid state for %s\n%s", name, obj, str(e))
    except vim.fault.CustomizationFault:
        logging.error("Cannot complete task %s: "
                      "invalid customization for %s", name, obj)
    except vim.fault.VmConfigFault:
        logging.error("Cannot complete task %s: "
                      "invalid configuration for VM %s", name, obj)
    except vim.fault.InvalidName as e:
        logging.error("Cannot complete task %s for object %s: "
                      "name '%s' is not valid", name, obj, e.name)
    except vim.fault.DuplicateName as e:
        logging.error("Cannot complete task %s for %s: "
                      "there is a duplicate named %s", name, obj, e.name)
    except vim.fault.InvalidDatastore as e:
        logging.error("Cannot complete task %s for %s: "
                      "invalid Datastore '%s'", name, obj, e.datastore)
    except vim.fault.AlreadyExists:
        logging.error("Cannot complete task %s: "
                      "%s already exists", name, obj)
    except vim.fault.NotFound:
        logging.error("Cannot complete task %s: "
                      "%s does not exist", name, obj)
    except vim.fault.ResourceInUse:
        logging.error("Cannot complete task %s: "
                      "resource %s is in use", name, obj)
    return None


# This line allows calling "<task>.wait(<params>)"
# instead of "wait_for_task(task, params)"
#
# This works because the implicit first argument
# to a class method call in Python is the instance
vim.Task.wait = wait_for_task  # Inject into vim.Task class


# From: list_dc_datastore_info in pyvmomi-community-samples
def get_datastore_info(ds_obj):
    """
    Gets a human-readable summary of a Datastore.

    :param ds_obj: The datastore to get information on
    :type ds_obj: vim.Datastore
    :return: The datastore's information
    :rtype: str
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


vim.Datastore.get_info = get_datastore_info


def make_vsphere(filename=None):
    """
    Creates a vSphere object using either a JSON file or by prompting the user.

    :param str filename: Name of JSON file with connection info
    :return: vSphere object
    :rtype: :class:`Vsphere`
    """
    from adles.vsphere.vsphere_class import Vsphere
    if filename is not None:
        info = read_json(filename)
        if info is None:
            raise VsphereException("Failed to create vSphere object")
        return Vsphere(username=info.get("user"),
                       password=info.get("pass"),
                       hostname=info.get("host"),
                       port=info.get("port", 443),
                       datacenter=info.get("datacenter"),
                       datastore=info.get("datastore"))
    else:
        logging.info("Enter information to connect to the vSphere environment")
        datacenter = input("Datacenter  : ")
        datastore = input("Datastore   : ")
        return Vsphere(datacenter=datacenter, datastore=datastore)


def resolve_path(server, thing, prompt=""):
    """
    This is a hacked together script utility to get folders or VMs.

    :param server: Vsphere instance
    :type server: :class:`Vsphere`
    :param str thing: String name of thing to get (folder | vm)
    :param str prompt: Message to display
    :return: (thing, thing name)
    :rtype: tuple(vimtype, str)
    """
    # TODO: use pathlib
    from adles.vsphere.vm import VM
    if thing.lower() == "vm":
        get = server.get_vm
    elif thing.lower() == "folder":
        get = server.get_folder
    else:
        logging.error("Invalid thing passed to resolve_path: %s", thing)
        raise ValueError
    res = user_input("Name of or path to %s %s: " % (thing, prompt), thing,
                     lambda x: server.find_by_inv_path("vm/" + x)
                     if '/' in x else get(x))
    if thing.lower() == "vm":
        return VM(vm=res[0]), res[1]
    else:
        return res


def is_folder(obj):
    """
    Checks if object is a vim.Folder.

    :param obj: The object to check
    :return: If the object is a folder
    :rtype: bool
    """
    return hasattr(obj, "childEntity")


def is_vm(obj):
    """
    Checks if object is a vim.VirtualMachine.

    :param obj: The object to check
    :return: If the object is a VM
    :rtype: bool
    """
    return hasattr(obj, "summary")
