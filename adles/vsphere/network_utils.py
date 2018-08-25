import logging

from pyVmomi import vim


def create_portgroup(name, host, vswitch_name, vlan=0, promiscuous=False):
    """
    Creates a portgroup on a ESXi host.

    :param name: Name of portgroup to create
    :param host: vim.HostSystem on which to create the port group
    :param vswitch_name: Name of vSwitch on which to create the port group
    :param vlan: VLAN ID of the port group
    :param promiscuous: Put portgroup in promiscuous mode
    """
    logging.debug("Creating PortGroup %s on vSwitch %s on host %s; "
                  "VLAN: %d; Promiscuous: %s",
                  name, vswitch_name, host.name, vlan, promiscuous)
    policy = vim.host.NetworkPolicy()
    policy.security = vim.host.NetworkPolicy.SecurityPolicy()
    policy.security.allowPromiscuous = bool(promiscuous)
    policy.security.macChanges = False
    policy.security.forgedTransmits = False
    spec = vim.host.PortGroup.Specification(name=name, vlanId=int(vlan),
                                            vswitchName=vswitch_name,
                                            policy=policy)
    try:
        host.configManager.networkSystem.AddPortGroup(spec)
    except vim.fault.AlreadyExists:
        logging.error("PortGroup %s already exists on host %s",
                      name, host.name)
    except vim.fault.NotFound:
        logging.error("vSwitch %s does not exist on host %s",
                      vswitch_name, host.name)
