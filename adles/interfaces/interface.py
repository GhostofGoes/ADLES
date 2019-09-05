import logging
from abc import ABC, abstractmethod


class Interface(ABC):
    """Base class for all Interfaces."""

    # Names/prefixes
    master_prefix = "(MASTER) "
    master_root_name = "MASTER-FOLDERS"

    def __init__(self, infra, spec):
        """
        :param dict infra: Full infrastructure configuration
        :param dict spec: Full exercise specification
        """
        self._log = logging.getLogger(self.__class__.__name__)
        self.infra = infra      # Save the infrastructure configuration
        self.spec = spec        # Save the exercise specification
        self.metadata = spec["metadata"]    # Save the exercise spec metadata
        self.services = spec["services"]
        self.networks = spec["networks"]    # Networks for platforms
        self.folders = spec["folders"]
        self.thresholds = {}    # Thresholds for platforms
        self.groups = {}        # Groups for platforms

    @abstractmethod
    def create_masters(self):
        """Master creation phase."""
        pass

    @abstractmethod
    def deploy_environment(self):
        """Environment deployment phase."""
        pass

    @abstractmethod
    def cleanup_masters(self, network_cleanup=False):
        """
        Cleans up master instances.

        :param bool network_cleanup: If networks should be cleaned up
        """
        pass

    @abstractmethod
    def cleanup_environment(self, network_cleanup=False):
        """
        Cleans up a deployed environment.

        :param bool network_cleanup: If networks should be cleaned up
        """
        pass

    def _instances_handler(self, spec, obj_name, obj_type):
        """
        Determines number of instances and optional prefix using specification.

        :param dict spec: Dict of folder
        :param str obj_name: Name of the thing being handled
        :param str obj_type: Type of the thing being handled (folder | service)
        :return: Number of instances, Prefix
        :rtype: tuple(int, str)
        """
        num = 1
        prefix = ""
        if "instances" in spec:
            if isinstance(spec["instances"], int):
                num = int(spec["instances"])
            else:
                if "prefix" in spec["instances"]:
                    prefix = str(spec["instances"]["prefix"])
                if "number" in spec["instances"]:
                    num = int(spec["instances"]["number"])
                elif "size-of" in spec["instances"]:
                    # size_of = spec["instances"]["size-of"])
                    # num = int(self._get_group(size_of).size
                    # if num < 1:
                    num = 1  # WORKAROUND FOR AD-GROUPS
                else:
                    self._log.error("Unknown instances specification: %s",
                                    str(spec["instances"]))
                    num = 0

        # Check if the number of instances exceeds
        # the configured thresholds for the interface
        thr = self.thresholds[obj_type]
        if num > thr["error"]:
            self._log.error("%d instances of %s '%s' is beyond the "
                            "configured %s threshold of %d",
                            num, obj_type, obj_name,
                            self.__name__, thr["error"])
            raise Exception("Threshold exceeded")
        elif num > thr["warn"]:
            self._log.warning("%d instances of %s '%s' is beyond the "
                              "configured %s threshold of %d",
                              num, obj_type, obj_name,
                              self.__name__, thr["warn"])
        return num, prefix

    def _path(self, path, name):
        """
        Generates next step of the path for deployment of Masters.

        :param str path: Current path
        :param str name: Name to add to the path
        :return: The updated path
        :rtype: str
        """
        return str(path + '/' + self.master_prefix + name)

    @staticmethod
    def _is_enabled(spec):
        """
        Determines if a spec is enabled.

        :param dict spec: Specification to check
        :return: If the spec is enabled
        :rtype: bool
        """
        if "enabled" in spec:
            return bool(spec["enabled"])
        else:
            return True

    def _determine_net_type(self, network_label):
        """
        Determines the type of a network.

        :param str network_label: Name of network to determine type of
        :return: Type of the network ("generic-networks" | "unique-networks")
        :rtype: str
        """
        for net_name, net_value in self.networks.items():
            vals = {k for k in net_value}
            if network_label in vals:
                return net_name
        self._log.error("Could not find type for network '%s'", network_label)
        return ""

    def _get_group(self, group_name):
        """
        Provides a uniform way to get information about normal groups
        and template groups.

        :param str group_name: Name of the group
        :return: Group object
        :rtype: :class:`Group`
        """
        from adles.group import Group
        if group_name in self.groups:
            group = self.groups[group_name]
            if isinstance(group, Group):    # Normal groups
                return group
            elif isinstance(group, list):   # Template groups
                return group[0]
            else:
                self._log.error("Unknown type for group '%s': %s",
                                str(group_name), str(type(group)))
        else:
            self._log.error("Could not get group '%s' from groups", group_name)

    def __repr__(self):
        return "%s(%s, %s)" % (str(self.__class__),
                               str(self.spec),
                               str(self.infra))

    def __str__(self):
        return str([x for x in self.infra.keys()])

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.infra == other.infra and \
            self.spec == other.spec
