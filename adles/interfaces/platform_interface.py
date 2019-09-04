import logging

from adles.interfaces import Interface


class PlatformInterface(Interface):
    """Generic interface used to uniformly interact with
    platform-specific interfaces."""

    def __init__(self, infra, spec):
        """
        :param dict infra: Full infrastructure configuration
        :param dict spec: Full exercise specification
        """
        super(PlatformInterface, self).__init__(infra=infra, spec=spec)
        self._log = logging.getLogger(str(self.__class__))
        self._log.debug("Initializing %s", self.__class__)
        self.interfaces = []  # List of instantiated platform interfaces

        # Select the Interface to use based on
        # the specified infrastructure platform
        for platform, config in infra.items():
            if platform == "vmware-vsphere":
                from adles.interfaces.vsphere_interface import VsphereInterface
                self.interfaces.append(VsphereInterface(config, spec))
            elif platform == "docker":
                from adles.interfaces.docker_interface import DockerInterface
                self.interfaces.append(DockerInterface(config, spec))
            elif platform == "cloud":
                from adles.interfaces.cloud_interface import CloudInterface
                self.interfaces.append(CloudInterface(config, spec))
            else:
                self._log.error("Invalid platform: %s", str(platform))
                raise ValueError

    # @time_execution
    def create_masters(self):
        """Master creation phase."""
        self._log.info("Creating Master instances for %s", self.metadata["name"])
        for i in self.interfaces:
            i.create_masters()

    # @time_execution
    def deploy_environment(self):
        """Environment deployment phase."""
        self._log.info("Deploying environment for %s", self.metadata["name"])
        for i in self.interfaces:
            i.deploy_environment()

    # @time_execution
    def cleanup_masters(self, network_cleanup=False):
        """
        Cleans up master instances.

        :param bool network_cleanup: If networks should be cleaned up
        """
        self._log.info("Cleaning up Master instances for %s", self.metadata["name"])
        for i in self.interfaces:
            i.cleanup_masters(network_cleanup=network_cleanup)

    # @time_execution
    def cleanup_environment(self, network_cleanup=False):
        """
        Cleans up a deployed environment.

        :param bool network_cleanup: If networks should be cleaned up
        """
        self._log.info("Cleaning up environment for %s", self.metadata["name"])
        for i in self.interfaces:
            i.cleanup_masters(network_cleanup=network_cleanup)
