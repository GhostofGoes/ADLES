import logging

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
except ImportError:
    logging.error("Could not import apache-libcloud. "
                  "Install it using 'pip install apache-libcloud'")

from adles.interfaces import Interface


class LibcloudInterface(Interface):
    """Base class for all interfaces that use Apache libcloud."""

    # noinspection PyMissingConstructor
    def __init__(self, infra, spec, provider_name=None):
        """
        :param dict infra: Dict of infrastructure information
        :param dict spec: Dict of a parsed specification
        :param str provider_name: Name of provider, if not in "provider" key
        """
        super(LibcloudInterface, self).__init__(infra=infra, spec=spec)
        self._log = logging.getLogger(str(self.__class__))
        self._log.debug("Initializing %s", self.__class__)

        # Used for interfaces such as libvirt
        if provider_name is None:
            self.provider_name = self.infra["provider"]
        else:
            self.provider_name = provider_name
        self.driver = get_driver(getattr(Provider, self.provider_name))

        # TODO: temporary for testing
        self.username = "test"
        self.api_key = "key"
        self.provider = self.driver(user_id=self.username, key=self.api_key)
