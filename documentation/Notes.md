

# Apache Libcloud notes
[Apache Libcloud](https://libcloud.readthedocs.io/en/latest/compute/examples.html).

While this has a VMware vSphere driver, it is limited (can't create nodes!) and is based on pysphere, which isn't as well supported as pyVmomi, stuck on python 2.7, not official, and only works for vsphere 5.5...


# Specification API
* Potential tools:[Swagger](http://swagger.io/) and it's
 [Python binding, `connexion`](https://pypi.python.org/pypi/connexion)
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

# Packages
* Compression utility for implementing packages (Use [`gzip`](https://docs.python.org/3.5/library/gzip.html) standard library module for this. Intro to it [here](https://pymotw.com/3/gzip/))

## Repository
Long-term, I’d like to see the creation of a public open-source repository of packages, similar to
Hashicorp’s Atlas and Docker’s Hub, where educators can share packages
and contribute to improving cyber education globally.


# Hypervisor support
* Vagrant: brings the platform to workstations and personal machines.
* Hyper-V server: free academic license, good for schools invested in the Microsoft ecosystem
* Xen: free and open-source, scalable, robust. Rich introspection possibilities for monitoring
   extensions using the Xen API
* KVM: free and open-source, good for schools with a strong Linux background.
   LibVMI provides rich introspection possibilities here as well.
* Various cloud platforms, such as Microsoft Azure, Amazon AWS, Google Cloud Platform,
   or DigitalOcean. Clouds are dynamic, scalable, and cost only for the time utilized,
   making them perfect for short-lived tutorials or competitions.

```yaml
# Microsoft Hyper-V Server
hyper-v:
  hostname: "hostname"    # REQUIRED    Hostname of the Hyper-V server
  port: 0                 # Suggested   Port used to connect to Hyper-V server
  login-file: "path"      # REQUIRED    Path to file containing login information for the Hyper-V server
  version: "v2"           # Suggested   Version of the Hyper-V API to use
  vswitch: "name"         # Suggested   Name of VirtualEthernetSwitch to use as default
```

