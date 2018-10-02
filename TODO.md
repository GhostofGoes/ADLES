List of tasks and TODOs for ADLES.
These range from minor tweaks, fixes, and improvements to major tasks and feature additions.

If you need help getting spun up on the VMware vSphere Python library, pyvmomi, I highly suggest checking out 
[pyvmomi-community-samples](https://github.com/vmware/pyvmomi-community-samples) and 
[pyvmomi](https://github.com/vmware/pyvmomi). You'll find references to it throughout the code.

Documentation for vSphere is [here](https://pubs.vmware.com/vsphere-60/index.jsp?topic=%2Fcom.vmware.wssdk.apiref.doc%2Fright-pane.html).

# Project
* Unit tests for vSphere. These could run when there is access to a server, or using the [`vcrpy`](https://pypi.python.org/pypi/vcrpy) module.
* Unit tests for other interfaces. (again, vcrpy)
* Unit tests for utils (doctests for those functions as well)
* Look at using doctests elsewhere
* Call unit testing tool (pytest, tox, whatever) from travis
* Move script tests from .travis.yml to their own shell script, then call that from travis
* Cleanup the amount of files at the project root
* Make man page generation automated
* `pipenv`: Pipfile, update documentation, add handy commands


# Documentation
* Setup and use [waffle.io](https://waffle.io/) project management board.
* Update design docs with new class structure
* Development guide: how to setup development environment, contribute, etc.
* Put READMEs in sub-directories with code, e.g for Vsphere, Interfaces
* Ensure Sphinx docs get updated when code changes are made
* Spec writing guides, how much time it takes
* Overall tutorial walkthrough and usage guide
* GIFs with overview of operation
* Screenshots of output
* How to extend specificiation and implement the extension
* Package specification example
* Add stuff from thesis/paper
* Triple/quadruple nested folder exercise example
* Logo or icon image for the project
* Insert terminology definitions and links into docs, e.g "Master", "Template", etc.


# Specs
* Add network folder(s) to vsphere infrastructure specification
* Add example of infrastructure specification
* Add example of package specification

## Exercise
* Add more network services to networks section, e.g DNS/DHCP configs, NTP
* Add "split-group" to enable finer grained isolated. 
e.g we want 30 students, each in their own VM, with no ability to see or mess with other students.


# Code


## Main Application
* Add ability to load configurations from an INI file (for main and scripts)

* Add resiliency using [`shelve`](https://docs.python.org/3/library/shelve.html) module and other methods, so long-running phases aren't killed by simple errors.
* Implement provisioners
* Evaluate alternatives to current syntax validator. The best I've found is [Swagger](http://swagger.io/) and it's [Python binding, `connexion`](https://pypi.python.org/pypi/connexion).
* Improve Groups: implement AD support, flesh out
* Move pyvmomi to optional-requirements

### Parser
* Make the parser a class to enable passing of state between methods
* Add type checking to _checker()
* Check if networks, services, groups, and resources are properly configured and matched.
* Verify group existance

### Utils
* setup_logging(): Add [Splunk logging handler](https://github.com/zach-taylor/splunk_handler).
* Compression utility for implementing packages (Use [`gzip`](https://docs.python.org/3.5/library/gzip.html) standard library module for this. Intro to it [here](https://pymotw.com/3/gzip/))


## Interface
* Subprocess the API calls by the Interface to its composite interfaces (e.g vSphere, Docker, etc).
That way they can run independantly and improve usage of network resources.
* Support multiple VsphereInterface instances (e.g for remote labs)
* Fix _instances_handler() workaround for AD-groups once they're implemented.
* Is method of loading login information for platform secure?

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

### DockerInterface
* Implement
* Test

## Vsphere
* Evaluate using WaitForTask from pyVim in pyvmomi instead of wait_for_task() in vsphere_utils
* Another possible method: (https://github.com/vmware/pyvmomi-tools/blob/master/pyvmomi_tools/extensions/task.py)
* Profile performance of current task waiting method
* Multi-thread or multi-process task waiting
* Implement vim.Folder power operations function
* Multi processing support throughout the module and interface. 
We should be able to clone several VMs simultaniously and stilll do other tasks, like create folders. 
This will help balance the load between the network connection to vCenter, vCenter itself, the ESXi hosts, and the Datastores.

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


# Goals and Additions
Long-term, I’d like to see the creation of a open-source repository, similiar to
Hashicorp’s Atlas and Docker’s Hub, where educators can share packages
and contribute to improving cyber education globally.

## Use Apache libcloud to implement cloud platforms
Use Apache [libcloud](https://libcloud.readthedocs.io/en/latest/compute/examples.html) to support all cloud platforms!
While this has a VMware vSphere driver, it is limited (can't create nodes!) and is based on pysphere, which isn't as well supported as pyVmomi, stuck on python 2.7, not official, and only works for vsphere 5.5...

* ~~Implement CloudInterface~~
* Improve hardware aspects of specs, make part of interface
* Use Groups to do permissions properly
* We need configuration management support to fully make use of libcloud


## Use Libvirt to implement hypervisors
Use [Libvirt](http://libvirt.org/drivers.html#hypervisor) to support most hypervisor platforms

* ~~Add LibvirtInterface~~
* Implement LibvirtInterface

## Additional platforms to support
* Docker: good for simulating large environments, with low resource overhead and quick load times
    * Docker Machine
    * Docker Compose
    * Docker Swarm
* Hyper-V server: free academic license, good for schools invested in the Microsoft ecosystem
* Vagrant: brings the platform to workstations and personal machines. Enables interaction with
   VirtualBox, desktop Hyper-V, and VMware Workstation
* Xen: free and open-source, scalable, robust. Rich introspection possibilities for monitoring
   extensions using the Xen API
* KVM: free and open-source, good for schools with a strong Linux background.
   LibVMI provides rich introspection possibilities here as well.
* Various cloud platforms, such as Microsoft Azure, Amazon AWS, Google Cloud Platform,
   or DigitalOcean. Clouds are dynamic, scalable, and cost only for the time utilized,
   making them perfect for short-lived tutorials or competitions.

## Specification extensions
* Monitoring extensions. This extension would add data collection configurations to relevant
   areas of the specifications, enabling the implementation of high-fidelity data collection. This
   would greatly enhance the system's research applicability, and enable other extensions such as
   fully automated grading of results, visualizations, and data analytics. Some examples of these
   configurations are:
    * Secondary interfaces on services for aggregating their log data, such as Windows Event Logs,
      Unix Syslog, application logs, etc.
    * Network packet captures. These could be obtained by enabling promiscuous mode on a vSwitch, or
      enabling a SPAN monitoring port to aggregate the network traffic.
    * Configuration of a centralized logging server to collect data, such as Splunk or ELK, including
      specifying how the data aggregated should be "frozen" for inclusion with a package.
    * Configuration of Virtual Machine Introspection (VMI) on supported platforms for a high-fidelity
      view of exercises during execution.
    * Instrumentation of the platforms and aggregation of the resulting log data, including the logs
      created by ADLES itself.
* Further Resource extensions for cyber-physical testbeds, and integration of Resources into more
   aspects of the exercise and package specifications. Examples of resources include testbeds for:
   ICS/SCADA, Wireless, USB devices, and car computers.
* Addition of ability to federate connections between separate lab environments, enabling the
   sharing of testbed resources, virtualization infrastructure, and collaboration between
   educational institutions. This could be implemented by extending the current Resources section
   or the addition of a new section.
* Visualization of an exercise in progress, notably for competitive environments.
* Extension of the Groups section in the exercise specification with explicit specification
   of user roles and permissions.
* Fully integrate and flesh out the role of exercise materials and other aspects of the Package
   specification.
* Specification of system resources required for a service, e.g CPU, RAM, storage space.
* Collaboration and communications for an exercise, e.g video conferencing, TeamSpeak,
   IRC channel, Discord server.
* Flag for selective toggling of parts of specifications where it would be useful to do
   so without having to remove or comment out the content, e.g a folder.

## System improvements
* Improved documentation on how to make a package, how to setup a platform for system, etc.
* Finish vSphere implementation (Users and Permissions)
* Redo the syntax verification component. Currently, any changes in spec involve a non-trivial
   number of changes to the source code of the component. This is brittle and makes verifying new
   extensions difficult, as most implementers will not bother in updating the component with the
   new syntax of their extensions.
    * Swagger is a possible solution, as it enables automatic generation of APIs from a spec
    * Implement verification of syntax for:
        * Non-vSphere platforms
        * Package specification
        * JSON files containing user information and platform logins
        * Scoring criteria and other related files
* Two-way transformation. Scan an existing environment and generate the specification for it.
* Graphical user interface. Ideally, this would be web-based for portability. In the short term,
   this could be accomplished with a minimal amount of work using the EasyGUI Python module.
* Visualization of what the network and service structure of a given exercise or package
   specification will look like without actually building the environment, including any
   cyber-physical testbeds, connected labs, and monitoring components if their corresponding
   extensions are implemented.
* Ability to pause/freeze an in-progress exercise, ideally as a simple commandline argument.
* Public repository of packages.
* More examples:
    * Examples of other types of competitions, notably CTFs
    * Experiment examples
    * Greater variety of tutorials
* Simplify system setup for educators beyond what a Python package provides
    * Vagrantfile that builds a lightweight VM running the system
    * Dockerfile that builds a lightweight Docker image running the system


# Stretch goals
* Dockerfile/Vagrantfile to setup a server instance that can run ADLES
