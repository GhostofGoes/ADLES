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

from automation.utils import time_execution


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
            doc = yaml.safe_load(f)  # Parses the YAML file into a dict
        except yaml.YAMLError as exc:
            logging.error("Could not parse file %s", filename)
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                logging.error("Error position: (%s:%s)", mark.line + 1, mark.column + 1)
            else:
                logging.error("Error: %s", exc)
            return None
    return doc


@time_execution
def verify_syntax(spec):
    """
    Verifies the syntax for the dictionary representation of an environment specification
    :param spec: Dictionary of environment specification
    :return: Boolean indicating success or failure
    """
    status = True
    if "metadata" in spec:
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


# TODO: I could totally generalize this in the future...basically swagger but domain-specific
def _checker(value_list, source, data, flag):
    """
    Checks if values in the list are in data (Syntax warnings or errors)
    :param value_list:
    :param source:
    :param data:
    :param flag: "warnings" or "errors"
    :return: Number of hits (warnings/errors)
    """
    num_hits = 0
    for value in value_list:
        if value not in data:
            if flag == "warnings":
                logging.warning("Missing %s in %s", value, source)
            elif flag == "errors":
                logging.error("Missing %s in %s", value, source)
            else:
                logging.error("Invalid flag for _checker: %s", flag)
            num_hits += 1
    if num_hits > 0:
        logging.info("Total number of %s in %s: %d", flag, source, num_hits)
    return num_hits


def _verify_metadata_syntax(metadata):
    """
    Verifies that the syntax for metadata matches the specification
    :param metadata:
    :return: Boolean indicating success or failure
    """
    warnings = ["description", "date-created", "root-path"]
    errors = ["name", "infrastructure-config-file"]

    num_warnings = _checker(warnings, "metadata", metadata, "warnings")
    num_errors = _checker(errors, "metadata", metadata, "errors")

    if "infrastructure-config-file" in metadata:
        infra_contents = parse_file(metadata["infrastructure-config-file"])
        num_errors += _verify_infra_syntax(infra_contents)

    return False if num_errors > 0 else True


def _verify_infra_syntax(infra):
    """
    Verifies syntax of infrastructure-config-file
    :param infra:
    :return: Number of errors
    """
    # TODO: interface-specific syntax and checking
    warnings = ["datacenter", "datastore"]
    errors = ["platform", "server-hostname", "server-port", "login-file", "template-folder"]

    num_warnings = _checker(warnings, "infrastructure", infra, "warnings")
    num_errors = _checker(errors, "infrastructure", infra, "errors")
    return num_errors


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
            elif "user-list" in value:
                if type(value["user-list"]) is not list:
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
    warnings = []
    errors = []
    num_warnings = _checker(warnings, "resources", resources, "warnings")
    num_errors = _checker(errors, "resources", resources, "errors")
    return num_errors


def _verify_networks_syntax(networks):
    """
    Verifies that the syntax for networks matches the specification
    :param networks:
    :return: Boolean indicating success or failure
    """
    status = True
    net_types = ["unique-networks", "generic-networks", "base-networks"]
    if not any(net in networks for net in net_types):
        logging.error("Network specification exists but is empty!")
        status = False
    else:
        for net in net_types:
            if net in networks and not _verify_network(net, networks[net]):
                status = False
    return status


def _verify_network(name, network):
    """
    Verifies syntax of a specific network
    :param name:
    :param network:
    :return:
    """
    status = True
    for key, value in network.items():
        if "subnet" not in value:
            logging.warning("No subnet specified for %s %s", name, key)
        else:
            subnet = IPNetwork(value["subnet"])
            if subnet.is_reserved() or subnet.is_multicast() or subnet.is_loopback():
                logging.error("%s %s is in a invalid IP address space", name, key)
                status = False
            elif not subnet.is_private():
                logging.warning("Non-private subnet used for %s %s", name, key)
    return status


def _verify_folders_syntax(folders):
    """
    Verifies that the syntax for folders matches the specification
    :param folders:
    :return: Boolean indicating success or failure
    """
    status = True

    for key, value in folders.items():
        if "instances" in value:
            if "number" in value["instances"]:
                pass  # TODO: VERIFY INT
            elif "size-of" in value["instances"]:
                pass  # TODO: verify group exists
            else:
                logging.error("Must specify number of instances for folder %s", key)
                status = False
        if "services" in value:
            if "group" not in value:
                logging.error("No group specified for folder %s", key)
                status = False
            for skey, svalue in value["services"].items():
                if "service" not in svalue:
                    logging.error("Service %s is unnamed in folder %s", skey, key)
                    status = False
                if "networks" in svalue and type(svalue["networks"]) is not list:
                    logging.error("Network specifications must be a list for service %s in folder %s", skey, key)
                    status = False
        else:  # It's a parent folder
            status = _verify_folders_syntax(value)

    return status


# TODO: basic unit tests
"""
if __name__ == '__main__':
    from pprint import pprint
    test_files = ['specifications/environment-specification.yaml', 'examples/competition.yaml',
                  'examples/tutorial.yaml', 'examples/experiment.yaml']
    for specfile in test_files:
        s = parse_file(specfile)
        pprint(s)  # Note that pprint will cause descriptions to go across multiple lines, don't be alarmed
"""
