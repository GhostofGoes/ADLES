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

from netaddr import IPNetwork, AddrFormatError

import adles.utils as utils


# PyYAML Reference: http://pyyaml.org/wiki/PyYAMLDocumentation
def parse_file(filename):
    """
    Parses the YAML file and returns a nested dictionary containing it's contents.

    >>> parse_file("test.yaml")
    { "test": "value" }

    :param filename: Name of YAML file to parse
    :return: dictionary of parsed file contents
    """
    from yaml import load, YAMLError
    try:  # Attempt to use C-based YAML parser if it's available
        # noinspection PyUnresolvedReferences
        from yaml import CLoader as Loader
        logging.debug("Using C-based YAML parser")
    except ImportError:  # Fallback to using pure python YAML parser
        from yaml import Loader

    with open(filename) as f:
        try:
            doc = load(f, Loader=Loader)  # Parses the YAML file into a dict
        except YAMLError as exc:
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
    # TODO: add type checking, perhaps use a tuple of (value, type)
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
    warnings = ["description", "version", "folder-name"]
    errors = ["name", "prefix", "infrastructure-config-file"]

    num_warnings = _checker(warnings, "metadata", metadata, "warnings")
    num_errors = _checker(errors, "metadata", metadata, "errors")

    if "infrastructure-config-file" in metadata:
        infra_file = metadata["infrastructure-config-file"]
        if not exists(infra_file):
            logging.error("Could not open infrastructure-config-file '%s'", infra_file)
            num_errors += 1
        else:
            e, w = _verify_infra_syntax(parse_file(infra_file))
            num_errors += e
            num_warnings += w
    return num_errors, num_warnings


def _verify_infra_syntax(infra):
    """
    Verifies syntax of infrastructure-config-file
    :param infra: Dict of infrastructure
    :return: (Number of errors, Number of warnings)
    """
    num_warnings = 0
    num_errors = 0

    for platform, config in infra.items():
        if platform == "vmware-vsphere":  # VMware vSphere configurations
            warnings = ["port", "login-file", "datacenter", "datastore", "server-root", "vswitch"]
            errors = ["hostname", "template-folder"]
            if "login-file" in config and utils.read_json(config["login-file"]) is None:
                logging.error("Invalid infrastructure login-file: %s", config["login-file"])
                num_errors += 1
        elif platform == "docker":  # Docker configurations
            warnings = ["url"]
            errors = []
        else:
            logging.error("Unknown infrastructure platform: %s", str(platform))
            continue  # Skip the syntax verification of unknown platforms
        num_warnings += _checker(warnings, "infrastructure", config, "warnings")
        num_errors += _checker(errors, "infrastructure", config, "errors")
    return num_errors, num_warnings


def _verify_groups_syntax(groups):
    """
    Verifies that the syntax for groups matches the specification
    :param groups: Dict of groups
    :return: (Number of errors, Number of warnings)
    """
    num_warnings = 0
    num_errors = 0
    
    for key, value in groups.items():
        if "instances" in value:  # Template groups
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
        else:  # Regular groups (not templates)
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
    num_warnings = 0
    num_errors = 0

    if utils.read_json(filename) is None:
        logging.error("Invalid user info file %s", filename)
        num_errors += 1
    return num_errors, num_warnings


def _verify_services_syntax(services):
    """
    Verifies that the syntax for services matches the specification
    :param services: Dict of services
    :return: (Number of errors, Number of warnings)
    """
    num_warnings = 0
    num_errors = 0
    
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
    num_warnings = 0
    num_errors = 0

    net_types = ["unique-networks", "generic-networks"]
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
    num_warnings = 0
    num_errors = 0
    
    for key, value in network.items():
        # Subnet verification
        if "subnet" not in value:
            logging.warning("No subnet specified for %s %s", name, key)
            num_warnings += 1
        else:
            try:
                subnet = IPNetwork(value["subnet"])
            except AddrFormatError:
                logging.error("Invalid format for subnet '%s'", str(value["subnet"]))
                num_errors += 1
            else:
                if subnet.is_reserved() or subnet.is_multicast() or subnet.is_loopback():
                    logging.error("%s %s is in a invalid IP address space", name, key)
                    num_errors += 1
                elif not subnet.is_private():
                    logging.warning("Non-private subnet used for %s %s", name, key)
                    num_warnings += 1

        # VLAN verification
        if "vlan" in value:
            if name == "unique-networks" and int(value["vlan"]) >= 2000:
                logging.error("VLAN must be less than 2000 for network %s", key)
                num_errors += 1
            elif name == "generic-networks":
                logging.error("VLAN specification is not allowed for network %s", key)
                num_errors += 1

        # Increment verification
        if "increment" in value:
            if name == "unique-networks":
                logging.error("Increment cannot be used for network %s", key)
                num_errors += 1
            elif type(value["increment"]) != bool:
                logging.error("Increment must be a boolean for network %s", key)
                num_errors += 1
    return num_errors, num_warnings


def _verify_folders_syntax(folders):
    """
    Verifies that the syntax for folders matches the specification
    :param folders: Dict of folders
    :return: (Number of errors, Number of warnings)
    """
    num_warnings = 0
    num_errors = 0

    for key, value in folders.items():
        if "instances" in value:  # Check instances syntax, regardless of parent or base
            if "number" in value["instances"]:
                if type(value["instances"]["number"]) != int:
                    logging.error("Number of instances for folder '%s' must be an Integer", key)
                    num_errors += 1
            elif "size-of" in value["instances"]:
                pass  # TODO: verify group existence
            else:
                logging.error("Must specify number of instances for folder '%s'", key)
                num_errors += 1

        # Check if parent or base
        if "services" in value:  # It's a base folder
            if "group" not in value:
                logging.error("No group specified for folder '%s'", key)
                num_errors += 1
            for skey, svalue in value["services"].items():
                if "service" not in svalue:
                    logging.error("Service %s is unnamed in folder '%s'", skey, key)
                    num_errors += 1
                if "networks" in svalue and type(svalue["networks"]) is not list:
                    logging.error("Network specifications must be a list for service '%s' "
                                  "in folder '%s'", skey, key)
                    num_errors += 1
                if "scoring" in svalue:
                    e, w = _verify_scoring_syntax(skey, svalue["scoring"])
                    num_errors += e
                    num_warnings += w
        else:  # It's a parent folder
            if key == "group" or key == "instances" or key == "description":
                pass
            elif not isinstance(value, dict):
                logging.error("Could not verify syntax of folder '%s': '%s' is not a folder!",
                              str(key), str(value))
                num_errors += 1
            else:
                e, w = _verify_folders_syntax(value)
                num_errors += e
                num_warnings += w
    return num_errors, num_warnings


def _verify_scoring_syntax(service_name, scoring):
    """
    Verifies syntax for the scoring definition of a service.
    :param service_name: Name of the service for which the scoring specification applies
    :param scoring: Dict of scoring parameters
    :return: (Number of errors, Number of warnings)
    """
    num_warnings = 0
    num_errors = 0

    if "ports" not in scoring:
        logging.warning("No scoring ports specified for service %s", service_name)
        num_warnings += 1
    elif not isinstance(scoring["ports"], list):
        logging.error("Scoring ports must be a list for service %s", service_name)
        num_errors += 1
    if "protocols" not in scoring:
        logging.warning("No protocols specified for service %s", service_name)
        num_warnings += 1
    elif not isinstance(scoring["protocols"], list):
        logging.error("Protocols must be a list for service %s", service_name)
        num_errors += 1
    if "criteria" not in scoring:
        logging.error("No criteria file specified for service %s", service_name)
        num_errors += 1
    return num_errors, num_warnings


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


def check_syntax(specfile_path):
    """
    Checks the syntax of a specification file
    :param specfile_path: Path to the specification file
    :return: The specification
    """
    from os.path import exists, basename

    if not exists(specfile_path):
        logging.error("Could not find specification file in path %s", str(specfile_path))
        return None
    spec = parse_file(specfile_path)
    if spec is None:
        logging.error("Failed to ingest specification file %s", basename(specfile_path))
        return None
    logging.info("Successfully ingested specification file %s", basename(specfile_path))
    logging.info("Checking syntax...")
    errors, warnings = verify_syntax(spec)
    if errors == 0 and warnings == 0:
        logging.info("Syntax check successful!")
        return spec
    elif errors == 0:
        logging.info("Syntax check successful, but there were %d warnings", warnings)
        return spec
    else:
        logging.error("Syntax check failed! Errors: %d\tWarnings: %d", errors, warnings)
        return None
