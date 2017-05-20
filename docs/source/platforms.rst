*********
Platforms
*********

Wrappers for the various platforms ADLES supports.



vSphere
=======


The vSphere platform serves as a wrapper around the pyVmomi library.


Vsphere
-------



Holds the state and provides methods to interact with the vCenter server
or ESXi host.

.. autoclass:: adles.vsphere.vsphere_class.Vsphere
   :members:


VM
--
Represents a Virtual Machine.

.. automodule:: adles.vsphere.vm
   :members:

Host
----
Represents an ESXi host.

.. automodule:: adles.vsphere.host
   :members:

Utility functions
-----------------
.. automodule:: adles.vsphere.vsphere_utils
   :members:

.. automodule:: adles.vsphere.folder_utils
   :members:

.. automodule:: adles.vsphere.network_utils
   :members:
