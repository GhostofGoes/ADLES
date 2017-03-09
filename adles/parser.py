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
from os.path import exists

from netaddr import IPNetwork

import adles.utils as utils


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


def _checker(value_list, source, data, flag):
    """
    Checks if values in the list are in data (Syntax warnings or errors)
    :param value_list: List of values to check
    :param source: Name of source that's being checked
    :param data: Data being checked
    :param flag: What to do if value not found ("warnings" | "errors")
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
    :param metadata: Dict of metadata
    :return: (Number of errors, Number of warnings)
    """
    warnings = ["description", "activity", "date-created", "folder-name", "root-path", "template-path"]
    errors = ["name", "prefix", "infrastructure-config-file"]

    num_warnings = _checker(warnings, "metadata", metadata, "warnings")
    num_errors = _checker(errors, "metadata", metadata, "errors")

    if "infrastructure-config-file" in metadata:
        infra_contents = parse_file(metadata["infrastructure-config-file"])
        e, w = _verify_infra_syntax(infra_contents)
        num_errors += e
        num_warnings += w

    return num_errors, num_warnings


def _verify_infra_syntax(infra):
    """
    Verifies syntax of infrastructure-config-file
    :param infra: Dict of infrastructure
    :return: (Number of errors, Number of warnings)
    """
    warnings = ["datacenter", "datastore", "server-root"]
    errors = ["platform", "server-hostname", "server-port", "login-file", "template-folder"]

    num_warnings = _checker(warnings, "infrastructure", infra, "warnings")
    num_errors = _checker(errors, "infrastructure", infra, "errors")
    return num_errors, num_warnings


def _verify_groups_syntax(groups):
    """
    Verifies that the syntax for groups matches the specification
    :param groups: Dict of groups
    :return: (Number of errors, Number of warnings)
    """
    num_errors = 0
    num_warnings = 0
    
    for key, value in groups.items():
        if "instances" in value:  # Templates
            if type(value["instances"]) != int:
                logging.error("Instances must be an Integer for group %s", key)
                num_errors += 1
            if "ad-group" in value:
                if type(value["ad-group"]) != str:
                    logging.error("AD group must be a string")
                    num_errors += 1
            elif "filename" in value:
                e, w = _check_group_file(value["filename"])
                num_errors += e
                num_warnings += w
            else:
                logging.error("Invalid user specification method for template group %s", key)
                num_errors += 1
        else:  # Non-templates
            if "ad-group" in value:
                if type(value["ad-group"]) != str:
                    logging.error("AD group must be a string")
                    num_errors += 1
            elif "filename" in value:
                e, w = _check_group_file(value["filename"])
                num_errors += e
                num_warnings += w
            elif "user-list" in value:
                if type(value["user-list"]) is not list:
                    logging.error("Username specification must be a list for group %s", key)
                    num_errors += 1
            else:
                logging.error("Invalid user specification method for group %s", key)
                num_errors += 1
    return num_errors, num_warnings


def _check_group_file(filename):
    """
    Verifies user info file for a group
    :param filename: Name of user info JSON file
    :return: (Number of errors, Number of warnings)
    """
    num_errors = 0
    num_warnings = 0

    if not exists(filename):
        logging.error("Group user file %s does not exist", filename)
        num_errors += 1
    return num_errors, num_warnings


def _verify_services_syntax(services):
    """
    Verifies that the syntax for services matches the specification
    :param services: Dict of services
    :return: (Number of errors, Number of warnings)
    """
    num_errors = 0
    num_warnings = 0
    
    for key, value in services.items():
        if "network-interfaces" in value and not isinstance(value["network-interfaces"], list):
            logging.error("Network interfaces must be a list for service %s", key)
            num_errors += 1
        if "template" in value:
            pass
        elif "image" in value:
            pass
        elif "compose-file" in value:
            pass
        else:
            logging.error("Invalid service definition: %s", key)
            num_errors += 1
    return num_errors, num_warnings


def _verify_resources_syntax(resources):
    """
    Verifies that the syntax for resources matches the specification
    :param resources: Dict of resources
    :return: (Number of errors, Number of warnings)
    """
    warnings = []
    errors = ["lab", "resource"]
    num_warnings = _checker(warnings, "resources", resources, "warnings")
    num_errors = _checker(errors, "resources", resources, "errors")
    return num_errors, num_warnings


def _verify_networks_syntax(networks):
    """
    Verifies that the syntax for networks matches the specification
    :param networks: Dict of networks
    :return: (Number of errors, Number of warnings)
    """
    num_errors = 0
    num_warnings = 0
    
    net_types = ["unique-networks", "generic-networks", "base-networks"]
    if not any(net in networks for net in net_types):
        logging.error("Network specification exists but is empty!")
        num_errors += 1
    else:
        for name, network in networks.items():
            e, w = _verify_network(name, network)
            num_errors += e
            num_warnings += w
    return num_errors, num_warnings


def _verify_network(name, network):
    """
    Verifies syntax of a specific network
    :param name: Name of network
    :param network: Dict of the network
    :return: (Number of errors, Number of warnings)
    """
    num_errors = 0
    num_warnings = 0
    
    for key, value in network.items():
        if "subnet" not in value:
            logging.warning("No subnet specified for %s %s", name, key)
            num_warnings += 1
        else:
            subnet = IPNetwork(value["subnet"])
            if subnet.is_reserved() or subnet.is_multicast() or subnet.is_loopback():
                logging.error("%s %s is in a invalid IP address space", name, key)
                num_errors += 1
            elif not subnet.is_private():
                logging.warning("Non-private subnet used for %s %s", name, key)
                num_warnings += 1
    return num_errors, num_warnings


def _verify_folders_syntax(folders):
    """
    Verifies that the syntax for folders matches the specification
    :param folders: Dict of folders
    :return: (Number of errors, Number of warnings)
    """
    num_errors = 0
    num_warnings = 0

    for key, value in folders.items():
        if "instances" in value:  # Check instances syntax, regardless of parent or base
            if "number" in value["instances"]:
                if type(value["instances"]["number"]) != int:
                    logging.error("Number of instances for folder %s must be an Integer", key)
                    num_errors += 1
            elif "size-of" in value["instances"]:
                pass
            else:
                logging.error("Must specify number of instances for folder %s", key)
                num_errors += 1

        # Check if parent or base
        if "services" in value:  # It's a base folder
            if "group" not in value:
                logging.error("No group specified for folder %s", key)
                num_errors += 1
            for skey, svalue in value["services"].items():
                if "service" not in svalue:
                    logging.error("Service %s is unnamed in folder %s", skey, key)
                    num_errors += 1
                if "networks" in svalue and type(svalue["networks"]) is not list:
                    logging.error("Network specifications must be a list for service %s in folder %s", skey, key)
                    num_errors += 1
                if "scoring" in svalue:
                    e, w = _verify_scoring_syntax(skey, svalue["scoring"])
                    num_errors += e
                    num_warnings += w
        else:
            if "master-group" not in value:
                logging.warning("No master group specified for parent folder %s", key)
                num_warnings += 1
            num_errors, num_warnings = _verify_folders_syntax(value)

    return num_errors, num_warnings


def _verify_scoring_syntax(service_name, scoring):
    """
    Verifies syntax for the scoring definition of a service.
    This is functionalized because it is likely to change in the future.
    :param service_name: Name of the service for which the scoring specification applies
    :param scoring: Dict of scoring parameters
    :return: (Number of errors, Number of warnings)
    """
    num_warnings = 0
    num_errors = 0

    if "ports" not in scoring:
        logging.error("No scoring ports specified for service %s", service_name)
        num_errors += 1
    elif not isinstance(scoring["ports"], list):
        logging.error("Scoring ports must be a list for service %s", service_name)
        num_errors += 1
    if "protocols" not in scoring:
        logging.error("No protocols specified for service %s", service_name)
        num_errors += 1
    elif not isinstance(scoring["protocols"], list):
        logging.error("Protocols must be a list for service %s", service_name)
        num_errors += 1
    if "criteria" not in scoring:
        logging.error("No criteria file specified for service %s", service_name)
        num_errors += 1
    # TODO: need to pass package dir or path to where the environment file is, so we can check files like these
    # elif not exists(scoring["criteria"]):
    #    logging.error("Could not find criteria file %s for service %s", scoring["criteria"], service_name)
    #    num_errors += 1

    return num_errors, num_warnings


@utils.time_execution
def verify_syntax(spec):
    """
    Verifies the syntax for the dictionary representation of an environment specification
    :param spec: Dictionary of environment specification
    :return: (Number of errors, Number of warnings)
    """
    num_warnings = 0
    num_errors = 0
    funcs = {"metadata": _verify_metadata_syntax,
             "groups": _verify_groups_syntax,
             "services": _verify_services_syntax,
             "resources": _verify_resources_syntax,
             "networks": _verify_networks_syntax,
             "folders": _verify_folders_syntax}

    required = ["metadata", "groups", "services", "networks", "folders"]
    optional = ["resources"]

    for key, func in funcs.items():
        if key not in spec:
            if key in required:
                logging.error("Required definition %s was not found", key)
                num_errors += 1
            elif key in optional:
                logging.debug('Optional definition "%s" was not found', key)
            else:
                logging.warning("Unknown definition found: %s", key)
                num_warnings += 1
        else:
            e, w = func(spec[key])
            num_errors += e
            num_warnings += w

    return num_errors, num_warnings
