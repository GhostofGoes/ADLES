List of tasks and TODOs for ADLES.
These range from minor tweaks, fixes, and improvements to major tasks and feature additions.


# Code

## Main Application
### Parser
* Make the parser a class to enable passing of state between methods
* Add type checking to _checker()
* Check if networks, services, groups, and resources are properly configured and matched.
* Verify group existance

### Utils
* Add Splunk logging handler to setup_logging() (https://github.com/zach-taylor/splunk_handler)

## Interface
* Subprocess the API calls by the Interface to its composite interfaces (e.g vSphere, Docker, etc).
That way they can run independantly and improve usage of network resources.
* Support multiple VsphereInterface instances (e.g for remote labs)
* Fix _instances_handler() workaround for AD-groups once they're implemented.
* Is method of loading login information for platform secure?

### VsphereInterface
* Apply group permissions
* Apply master-group permissions
* Take "template" and other platform identifiers global keywords per-interface

## Vsphere
* Evaluate using WaitForTask from pyVim in pyvmomi instead of wait_for_task() in vsphere_utils
* Another possible method: (https://github.com/vmware/pyvmomi-tools/blob/master/pyvmomi_tools/extensions/task.py)
* Profile performance of current task waiting method
* Multi-thread or multi-process task waiting

### VM
* Implement get_all_snapshots_info()
* Configure guest IP address if statically assigned for add_nic()
* execute_program(): listprocesses/terminate process in guest, make helper func for guest authentication

### Host
* Use this class elsewhere in code
* Implement get_info() to get host information much like VM's get_info()
* Add edit_vswitch()
* Add edit_portgroup()


## Scripts

# Additions

# Features

