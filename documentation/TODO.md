List of tasks and TODOs for ADLES.
These range from minor tweaks, fixes, and improvements to major tasks and feature additions.

If you need help getting spun up on the VMware vSphere Python library, pyvmomi, I highly suggest checking out 
[pyvmomi-community-samples](https://github.com/vmware/pyvmomi-community-samples) and 
[pyvmomi](https://github.com/vmware/pyvmomi). You'll find references to it throughout the code.

Documentation for vSphere is [here](https://pubs.vmware.com/vsphere-60/index.jsp?topic=%2Fcom.vmware.wssdk.apiref.doc%2Fright-pane.html).


# Version 2
**Focus**: The Cloud
* Support for cloud platforms
* Overhaul of internal design to support the changes in this and future releases

## Features
#### Major
* Full support for cloud providers
    * Addition of a pricing-related sections to specification(s)
    * Improvements and additions to infrastructure spec for compute nodes
    * Specification of system resources required for a service, e.g CPU, RAM, storage space.
    * Implement generic containers using Libcloud
* Support for Docker provider (possibly through libcloud)
* Initial support for provisioning
    * Improve the specifications for provisioning
    * Shell scripts
* (Internal) Change the syntax validation to be dependant on the specifications,
 versus the current method of hard-coding the logic in Python.
* Parser
    * Make the parser a class to enable passing of state between methods
    * Add type checking to _checker()
    * Check if networks, services, groups, and resources are properly configured and matched.
    * Verify group existence

#### Minor
* Move `pyvmomi` from required dependencies into extra dependencies?
* Add ability to load configurations from a file (for main and scripts, INI/JSON/other)
* Add network folder(s) to vsphere infrastructure specification
* Exercise specification
    * Add more network services to networks section, e.g DNS/DHCP configs, NTP
    * Add "split-group" to enable finer grained isolated.
     (e.g we want 30 students, each in their own VM, with no ability to see or mess with other students.)
* Add some resiliency using [`shelve`](https://docs.python.org/3/library/shelve.html)
    module or other methods, so long-running phases aren't killed by simple errors.
* Improve users/permissions ("Groups")
    * Better define the spec
    * Is method of loading login information for platform secure?
    * Extension of the Groups section in the exercise specification with explicit specification of user roles and permissions.
* Performance improvements (subprocess, vsphere tweaks)
* Flag for selective toggling of parts of specifications where it would be useful to do
   so without having to remove or comment out the content, e.g a folder.
* Fix base classes to import from `module`, which is the new and recommended style
* Subprocess the API calls by the Interface to its composite interfaces (e.g vSphere, Docker, etc).
That way they can run independently and improve usage of network resources.

## Tests
* Add functional tests for the main `adles` script (using [`bats`](https://github.com/sstephenson/bats)).
 Remove the list of tests from .travis.yml and put into the .bats script.
* Complete unit testing of utils
* Unit tests for parser
* Unit tests for group

## Project
* Automated GitHub releases: tag, zip, wheel, changelog
* Overhaul Travis: deploy, testing platforms, test scripts, etc.

## Documentation
#### Minor
* Ensure ReadTheDocs is being auto-generated properly when code changes are made
* Update supported and tested platforms
* Triple and quadruple nested folder exercise examples
* Add a "Contributing" (Hacking?) section to the docs (in addition to CONTRIBUTING.md)
* Add a "Tutorial" section, walk through usage at a high level
* Add a "FAQ" section
* Add a "Examples" section
* Add example of infrastructure specification
* Add example of package specification
* Add sections with the full specifications
* Add a "Terminology" section with terminology definitions
* Link to Terminology section from docs, e.g "Master", "Template", etc.

#### Major
* Introduction that outlines philosophy of project, clarifies where this
 and other systems (e.g. Salt Stack, etc.) differ, what the primary purpose is.
 Need to be precise and explicit. Address concerns raised at defense.
* Add a "Design and Architecture" section with overall design of ADLES
* Add several sections on how to write specifications
* Improve documentation of classes
* Full examples of specs and commandline usage
* Add recordings of key examples (using [AsciiCinema](https://asciinema.org/))
* Add screenshots of created environments, terminal usage
* Add stuff from thesis/paper
* Logo or icon image for the project
* More examples:
    * Examples of other types of competitions, notably CTFs
    * Experiment examples
    * Greater variety of tutorials


# Version 3
**Focus**: Rounding out the core
* Implementing remaining core features: Packages, Provisioning
* Full Test coverage
* Robust documentation
* Solid user experience

## Features

### Major
* Full support for Packages: creating environments from packages, parsing, etc.
    * Fully integrate and flesh out the role of exercise materials and other aspects of the Package specification.
* Full support for provisioning
    * Additions and improvements to the specifications for provisioning
    * Utilize a provisioner in the backend (Puppet, Chef, Ansible, or another)
    * Update installation to include tooling necessary for provisioning

### Minor
* Implement Active-Directory support for vSphere authentication of specified Groups
    * Fix _instances_handler() workaround for AD-groups once they're implemented.
* Clear most or all of the TODOs in [the vSphere TODO list](vsphere-TODO.md)

## Tests
* Unit tests for vSphere interface. These could run when there is access to a server,
 or using the [`vcrpy`](https://pypi.python.org/pypi/vcrpy) module.
* Unit tests for cloud interfaces (vcrpy, Mock, etc.)
* Functional tests for vsphere helper scripts
* Coverage testing
* doctests where appropriate

## Documentation
* Auto-generation of Man page
* Put READMEs in sub-directories with code, e.g for Vsphere, include in doc build?
* How to extend specification and implement the extension to the specification
 (e.g. adding a new section to the syntax of one of the core specifications
 that implements a in-house custom or add-on tool)
* Package specification example
* Add a "Packages" section outlining packages
* Add subsections for creating packages, syntax, examples, full API and spec


# Version 4
**Focus**: Expanding the feature set
* Adding Host platform support
* Adding new features

## Features
* Vagrant support: VirtualBox, Hyper-V, VMware Workstation, Host Docker containers, KVM
* Two-way transformation. Scan an existing environment and generate the specification for it.
* Ability to pause/freeze an in-progress exercise, ideally as a simple commandline argument.
* Simplify system setup for educators beyond what a Python package provides
    * Vagrantfile that builds a lightweight VM running the system
    * Dockerfile that builds a lightweight Docker image running the system


# Version 5
**Focus**: Transforming the user experience

## Features
* Addition of a standalone server module
    * Separate GitHub project that depends on ADLES
    * Web-based GUI
        * Create and manage exercises
        * Monitor running exercises
        * Manage infrastructure
        * Visualization of an exercise in progress (e.g. competition)
        * Provide exercise metadata over API (e.g. for a competition)
    * Dockerfile/Vagrantfile to setup the server
    * Visualization of what the network and service structure of a given exercise or package
       specification will look like without actually building the environment, including any
       cyber-physical testbeds, connected labs, and monitoring components if their corresponding
       extensions are implemented.
* Setup a cloud-hosted public repository of packages
    * Source code for this repository in a separate GitHub project


# Version 6
**Focus**: Extending the specifications

## Features
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
* Collaboration and communications for an exercise, e.g video conferencing, TeamSpeak,
   IRC channel, Discord server.
