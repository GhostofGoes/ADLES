# VMware vSphere Interface TODOs

## Vsphere
* Evaluate using WaitForTask from pyVim in pyvmomi instead of wait_for_task() in vsphere_utils
* Another possible method: (https://github.com/vmware/pyvmomi-tools/blob/master/pyvmomi_tools/extensions/task.py)
* Profile performance of current task waiting method
* Multi-thread or multi-process task waiting
* Implement vim.Folder power operations function
* Multi processing support throughout the module and interface.
  We should be able to clone several VMs simultaniously and stilll do other tasks, like create folders.
  This will help balance the load between the network connection to vCenter, vCenter itself, the ESXi hosts, and the Datastores.
* Support multiple VsphereInterface instances (e.g for remote labs)

### VsphereInterface
* Apply group permissions
* Apply master-group permissions
* _create_service(): Validate the configuration of an existing service template to a reasonable degree
* Implement configuration of "network-interface" for services in the "services" top-level section
* _get_net(): could use this to do network lookups on the server as well
* cleanup_masters(): finish implementing, look at getorphanedvms in pyvmomi-community-samples for how to do this
* cleanup_environment(): implement, ensure master-folder is skipped
* Implement layer 3 configuration of networks and services (subnets, addresses, etc.)
* Use Network folders to aid in network cleanup for both phases
* init(): Better vSwitch default
* Finish implementing hosts (since there's self.host and self.hosts currently)
* Deal with potential naming conflicts in self.masters cache of Master instances
* Make "template" and other platform identifiers global keywords per-interface
* Result collection methods
* Implement guest extensions installation/verification (This will have to be done using Ansible, based on my research)
* Include screenshots from VMs in results (argument)

### VM
* Implement get_all_snapshots_info()
* Configure guest IP address if statically assigned for add_nic()
* execute_program(): listprocesses/terminate process in guest, make helper func for guest authentication
* Automated installation of VMware Tools

### Host
* Use this class elsewhere in code
* Implement get_info() to get host information much like VM's get_info()
* Add edit_vswitch()
* Add edit_portgroup()

## Scripts
* cleanup_vms: add ability to select options using commandline arguments
* clone_vms: add ability to modify hardware of VMs being cloned (perhaps using arguments)
* vm_power: prefixes
* vm_power: nesting
* vm_power: maybe it would be easiest to implement as a vim.Folder function that is called
* vm_snapshots: implement "get" functions
* vm_snapshots: test and shake out the wrinkles
* Add a "edit-vms" script to do modifications en-masse? (e.g attach ISOs, edit hardware resources, etc.)
