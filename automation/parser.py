#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from netaddr import IPNetwork


# Reference: http://pyyaml.org/wiki/PyYAMLDocumentation
def parse_file(filename):
    """
    Parses the YAML file and returns a nested dictionary containing it's contents
    :param filename: Name of YAML file to parse
    :return: dictionary of parsed file contents
    """
    import yaml
    with open(filename, 'r') as f:
        try:
            doc = yaml.safe_load(f)  # Parses the YAML file and creates a python object with it's structure and contents
        except yaml.YAMLError as exc:
            logging.error("Could not parse file %s" % filename)
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                logging.error("Error position: (%s:%s)" % (mark.line + 1, mark.column + 1))
            else:
                logging.error("Error: ", exc)
            return None  # If there was an error, then there ain't gonna be any markup, so we exit in a obvious way
    return doc


def verify_syntax(spec):
    """
    Verifies the syntax for the dictionary representation of an environment specificaiton
    :param spec: Dictionary of environment specificaiton
    :return: Boolean indicating success or failure
    """
    status = True
    if "metadata" in spec:
        # TODO: verify infrastructure-spec
        if not _verify_metadata_syntax(spec["metadata"]):
            status = False
    else:
        logging.error("No metadata found!")
        status = False
    if "groups" in spec:
        if not _verify_groups_syntax(spec["groups"]):
            status = False
    else:
        logging.warning("No groups found")
    if "services" in spec:
        if not _verify_services_syntax(spec["services"]):
            status = False
    else:
        logging.warning("No services found")
    if "resources" in spec:
        if not _verify_resources_syntax(spec["resources"]):
            status = False
    else:
        logging.warning("No resources found")
    if "networks" in spec:
        if not _verify_networks_syntax(spec["networks"]):
            status = False
    else:
        logging.warning("No networks found")
    if "folders" in spec:
        if not _verify_folders_syntax(spec["folders"]):
            status = False
    else:
        logging.error("No folders found")
        status = False
    return status


def _verify_metadata_syntax(metadata):
    """
    Verifies that the syntax for metadata matches the specification
    :param metadata:
    :return: Boolean indicating success or failure
    """
    status = True
    if "name" not in metadata:
        logging.error("Missing name in metadata")
        status = False
    if "description" not in metadata:
        logging.warning("Missing description in metadata")
    if "date-created" not in metadata:
        logging.warning("Missing date-created in metadata")
    if "infrastructure-config-file" not in metadata:
        logging.error("Missing infrastructure-config-file in metadata")
        status = False
    return status


def _verify_groups_syntax(groups):
    """
    Verifies that the syntax for groups matches the specification
    :param groups:
    :return: Boolean indicating success or failure
    """
    status = True
    for key, value in groups.items():
        if " X" in key:  # Templates
            if "instances" not in value:
                logging.error("No instances specified for template group %s", key)
                status = False
            if "ad-group" in value:
                pass
            elif "filename" in value:
                pass
            else:
                logging.error("Invalid user specification method for template group %s", key)
                status = False
        else:  # Non-templates
            if "ad-group" in value:
                pass
            elif "filename" in value:
                pass
            elif "usernames" in value:
                if type(value["usernames"]) is not list:
                    logging.error("Username specification must be a list for group %s", key)
                    status = False
            else:
                logging.error("Invalid user specification method for group %s", key)
                status = False
    return status


def _verify_services_syntax(services):
    """
    Verifies that the syntax for services matches the specification
    :param services:
    :return: Boolean indicating success or failure
    """
    status = True
    for key, value in services.items():
        if "template" in value:
            pass
        elif "image" in value:
            pass
        elif "compose-file" in value:
            pass
        else:
            logging.error("Invalid service definition: %s", key)
            status = False
    return status


def _verify_resources_syntax(resources):
    """
    Verifies that the syntax for resources matches the specification
    :param resources:
    :return: Boolean indicating success or failure
    """
    status = True
    # TODO: implement
    return status


def _verify_networks_syntax(networks):
    """
    Verifies that the syntax for networks matches the specification
    :param networks:
    :return: Boolean indicating success or failure
    """
    status = True
    if "unique-networks" not in networks and "generic-networks" not in networks and "base-networks" not in networks:
        logging.error("Network specification exists but is empty!")
        status = False
    else:
        # TODO: generalize so not duplicating 3 times here and elsewhere (like in model.py)
        if "unique-networks" in networks:
            for key, value in networks["unique-networks"].items():
                if "subnet" not in value:
                    logging.warning("No subnet specified for network %s", key)
                else:
                    subnet = IPNetwork(value["subnet"])
                    if subnet.is_reserved() or subnet.is_multicast() or subnet.is_loopback():
                        logging.error("Network %s is in a invalid IP address space", key)
                        status = False
                    elif not subnet.is_private():
                        logging.warning("Non-private subnet used for network %s", key)
        if "generic-networks" in networks:
            for key, value in networks["generic-networks"].items():
                if "subnet" not in value:
                    logging.warning("No subnet specified for network %s", key)
                else:
                    subnet = IPNetwork(value["subnet"])
                    if subnet.is_reserved() or subnet.is_multicast() or subnet.is_loopback():
                        logging.error("Network %s is in a invalid IP address space", key)
                        status = False
                    elif not subnet.is_private():
                        logging.warning("Non-private subnet used for network %s", key)
        if "base-networks" in networks:
            for key, value in networks["base-networks"].items():
                if "subnet" not in value:
                    logging.warning("No subnet specified for network %s", key)
                else:
                    subnet = IPNetwork(value["subnet"])
                    if subnet.is_reserved() or subnet.is_multicast() or subnet.is_loopback():
                        logging.error("Network %s is in a invalid IP address space", key)
                        status = False
                    elif not subnet.is_private():
                        logging.warning("Non-private subnet used for network %s", key)
    return status


def _verify_folders_syntax(folders):
    """
    Verifies that the syntax for folders matches the specification
    :param folders:
    :return: Boolean indicating success or failure
    """
    status = True
    for key, value in folders.items():
        if "services" in value:
            for skey, svalue in value["services"].items():
                if "service" not in svalue:
                    logging.error("Service %s is unnamed in folder %s", skey, key)
                    status = False
                if "networks" in svalue and type(svalue["networks"]) is not list:
                    logging.error("Network specifications must be a list for service %s in folder %s", skey, key)
                    status = False
        else:
            logging.error("No services specified for folder %s", key)
            status = False
        if "group" not in value:
            logging.error("No group specified for folder %s", key)
            status = False
    return status


if __name__ == '__main__':
    """ For testing of the parser """
    from pprint import pprint
    files = ['../examples/edurange.yaml', '../specifications/environment-specification.yaml',
             '../examples/competition.yaml', '../examples/tutorial.yaml', '../examples/experiment.yaml']
    for specfile in files:
        s = parse_file(specfile)
        pprint(s)  # Note that pprint will cause descriptions to go across multiple lines, don't be alarmed
