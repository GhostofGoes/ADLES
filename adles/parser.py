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
from os.path import exists, basename
import sys
import ipaddress

from yaml import load, YAMLError
try:  # Attempt to use C-based YAML parser if it's available
    from yaml import CLoader as Loader
except ImportError:  # Fallback to using pure Python YAML parser
    from yaml import Loader

import adles.utils as utils


# PyYAML Reference: http://pyyaml.org/wiki/PyYAMLDocumentation
def parse_yaml(filename):
    """
    Parses a YAML file and returns a nested dictionary containing its contents.

    :param str filename: Name of YAML file to parse
    :return: Parsed file contents
    :rtype: dict or None
    """
    try:
        # Enables use of stdin if '-' is specified
        with sys.stdin if filename == '-' else open(filename) as f:
            try:
                # Parses the YAML file into a dict
                return load(f, Loader=Loader)
            except YAMLError as exc:
                logging.critical("Could not parse YAML file %s", filename)
                if hasattr(exc, 'problem_mark'):
                    # Tell user exactly where the syntax error is
                    mark = exc.problem_mark
                    logging.error("Error position: (%s:%s)",
                                  mark.line + 1, mark.column + 1)
                else:
                    logging.error("Error: %s", exc)
                    return None
    except FileNotFoundError:
        logging.critical("Could not find YAML file for parsing: %s", filename)
        return None


def _checker(value_list, source, data, flag):
    """
    Checks if values in the list are in data (Syntax warnings or errors).

    :param list value_list: List of values to check
    :param str source: Name of source that's being checked
    :param dict data: Data being checked
    :param str flag: What to do if value not found ("warnings" | "errors")
    :return: Number of hits (warnings/errors)
    :rtype: int
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


def _verify_exercise_metadata_syntax(metadata):
    """
    Verifies that the syntax for exercise metadata matches the specification.

    :param dict metadata: metadata
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    warnings = ["description", "version", "folder-name"]
    errors = ["name", "prefix", "infra-file"]
    num_warnings = _checker(warnings, "metadata", metadata, "warnings")
    num_errors = _checker(errors, "metadata", metadata, "errors")

    if "infra-file" in metadata:
        infra_file = metadata["infra-file"]
        if not exists(infra_file):
            logging.error("Could not open infra-file '%s'", infra_file)
            num_errors += 1
        else:
            err, warn = verify_infra_syntax(parse_yaml(infra_file))
            num_errors += err
            num_warnings += warn
    return num_errors, num_warnings


def _verify_groups_syntax(groups):
    """
    Verifies that the syntax for groups matches the specification.

    :param dict groups: groups
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    num_warnings = 0
    num_errors = 0

    for key, value in groups.items():
        if "instances" in value:  # Template groups
            if not isinstance(value["instances"], int):
                logging.error("Instances must be an Integer for group %s", key)
                num_errors += 1
            if "ad-group" in value:
                if not isinstance(value["ad-group"], str):
                    logging.error("AD group must be a string")
                    num_errors += 1
            elif "filename" in value:
                e, w = _check_group_file(value["filename"])
                num_errors += e
                num_warnings += w
            else:
                logging.error("Invalid user specification method for "
                              "template group %s", key)
                num_errors += 1
        else:  # Regular groups (not templates)
            if "ad-group" in value:
                if not isinstance(value["ad-group"], str):
                    logging.error("AD group must be a string")
                    num_errors += 1
            elif "filename" in value:
                e, w = _check_group_file(value["filename"])
                num_errors += e
                num_warnings += w
            elif "user-list" in value:
                if not isinstance(value["user-list"], list):
                    logging.error("Username specification must be a "
                                  "list for group %s", key)
                    num_errors += 1
            else:
                logging.error("Invalid user specification method "
                              "for group %s", key)
                num_errors += 1
    return num_errors, num_warnings


def _check_group_file(filename):
    """
    Verifies user info file for a group.

    :param str filename: Name of user info JSON file
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    num_warnings = 0
    num_errors = 0

    if utils.read_json(filename) is None:
        logging.error("Invalid user info file %s", filename)
        num_errors += 1
    return num_errors, num_warnings


def _verify_services_syntax(services):
    """
    Verifies that the syntax for services matches the specification.

    :param dict services: services
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    num_warnings = 0
    num_errors = 0

    for key, value in services.items():
        if "network-interfaces" in value and \
                not isinstance(value["network-interfaces"], list):
            logging.error("Network interfaces must be a list for "
                          "service %s", key)
            num_errors += 1
        if "provisioner" in value:
            num_errors += _checker(["name", "file"],
                                   "provisioner for service %s" % key,
                                   value["provisioner"], "errors")
        if "note" in value and not isinstance(value["note"], str):
            logging.error("Note must be a string for service %s", key)
            num_errors += 1
        if "template" in value:
            pass
        elif "image" in value or "dockerfile" in value:
            pass
        elif "compose-file" in value:
            pass
        else:
            logging.error("Invalid service definition: %s", key)
            num_errors += 1
    return num_errors, num_warnings


def _verify_resources_syntax(resources):
    """
    Verifies that the syntax for resources matches the specification.

    :param dict resources: resources
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    warnings = []
    errors = ["lab", "resource"]
    num_warnings = _checker(warnings, "resources", resources, "warnings")
    num_errors = _checker(errors, "resources", resources, "errors")
    return num_errors, num_warnings


def _verify_networks_syntax(networks):
    """
    Verifies that the syntax for networks matches the specification.

    :param dict networks: networks
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    num_warnings = 0
    num_errors = 0
    net_types = ["unique-networks", "generic-networks"]

    if not any(net in networks for net in net_types):
        logging.error("Network specification exists but is empty!")
        num_errors += 1
    else:
        for name, network in networks.items():
            err, warn = _verify_network(name, network)
            num_errors += err
            num_warnings += warn
    return num_errors, num_warnings


def _verify_network(name, network):
    """
    Verifies syntax of a specific network.

    :param str name: Name of network
    :param dict network: the network
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
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
                subnet = ipaddress.ip_network(value["subnet"])
            except ValueError as err:
                logging.error("Invalid format for subnet '%s': %s",
                              str(value["subnet"]), str(err))
                num_errors += 1
            else:
                if subnet.is_reserved \
                        or subnet.is_link_local \
                        or subnet.is_multicast \
                        or subnet.is_loopback:
                    logging.error("%s %s is in a invalid IP address space",
                                  name, key)
                    num_errors += 1
                elif not subnet.is_private:
                    logging.warning("Non-private subnet used for %s %s",
                                    name, key)
                    num_warnings += 1

        # VLAN verification
        if "vlan" in value:
            if name == "unique-networks" and int(value["vlan"]) >= 2000:
                logging.error("VLAN must be less than 2000 for network %s", key)
                num_errors += 1
            elif name == "generic-networks":
                logging.error("VLAN specification is not allowed "
                              "for network %s", key)
                num_errors += 1

        # Increment verification
        if "increment" in value:
            if name == "unique-networks":
                logging.error("Increment cannot be used for network %s", key)
                num_errors += 1
            elif not isinstance(value["increment"], bool):
                logging.error("Increment must be a boolean for network %s", key)
                num_errors += 1
    return num_errors, num_warnings


def _verify_folders_syntax(folders):
    """
    Verifies that the syntax for folders matches the specification.

    :param dict folders: folders
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    num_warnings = 0
    num_errors = 0
    keywords = ["group", "master-group", "instances", "description", "enabled"]

    for key, value in folders.items():
        if key in keywords:
            continue
        if not isinstance(value, dict):
            logging.error("Invalid configuration %s", str(key))
            num_errors += 1
            continue
        # Check instances syntax, regardless of parent or base
        if "instances" in value:
            if not isinstance(value["instances"], int):
                pass
            elif "number" in value["instances"]:
                if not isinstance(value["instances"]["number"], int):
                    logging.error("Number of instances for folder '%s' "
                                  "must be an Integer", key)
                    num_errors += 1
            elif "size-of" in value["instances"]:
                pass
            else:
                logging.error("Must specify number of instances "
                              "for folder '%s'", key)
                num_errors += 1

        # Check if parent or base
        if "services" in value:  # It's a base folder
            if "group" not in value:
                logging.error("No group specified for folder '%s'", key)
                num_errors += 1
            for skey, svalue in value["services"].items():
                if "service" not in svalue:
                    logging.error("Service %s is unnamed in folder '%s'",
                                  skey, key)
                    num_errors += 1
                if "networks" in svalue and \
                        not isinstance(svalue["networks"], list):
                    logging.error("Network specifications must be a list "
                                  "for service '%s' "
                                  "in folder '%s'", skey, key)
                    num_errors += 1
                if "scoring" in svalue:
                    err, warn = _verify_scoring_syntax(skey, svalue["scoring"])
                    num_errors += err
                    num_warnings += warn
        else:  # It's a parent folder
            if not isinstance(value, dict):
                logging.error("Could not verify syntax of folder '%s': "
                              "'%s' is not a folder!",
                              str(key), str(value))
                num_errors += 1
            else:
                err, warn = _verify_folders_syntax(value)
                num_errors += err
                num_warnings += warn
    return num_errors, num_warnings


def _verify_scoring_syntax(service_name, scoring):
    """
    Verifies syntax for the scoring definition of a service.

    :param str service_name: Name of the service for which the 
    scoring specification applies
    :param dict scoring: scoring parameters
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    warnings = ["ports", "protocols"]
    errors = ["criteria"]
    num_warnings = _checker(warnings, "service %s" %
                            service_name, scoring, "warnings")
    num_errors = _checker(errors, "service %s"
                          % service_name, scoring, "errors")
    return num_errors, num_warnings


def verify_infra_syntax(infra):
    """
    Verifies the syntax of an infrastructure specification.

    :param dict infra: infrastructure
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    num_warnings = 0
    num_errors = 0
    warnings = []
    errors = []

    for platform, config in infra.items():
        if platform == "vmware-vsphere":  # VMware vSphere configurations
            warnings = ["port", "login-file", "datacenter",
                        "datastore", "server-root", "vswitch"]
            errors = ["hostname", "template-folder"]
            if "login-file" in config and \
                    utils.read_json(config["login-file"]) is None:
                logging.error("Invalid vSphere infrastructure login-file: %s",
                              config["login-file"])
                num_errors += 1
            if "host-list" in config and \
                    not isinstance(config["host-list"], list):
                logging.error("Invalid type for vSphere host-list: %s",
                              type(config["host-list"]))
                num_errors += 1
            if "thresholds" in config:
                num_errors += _checker(["folder", "service"], "infrastructure",
                                       config["thresholds"], "errors")
        elif platform == "docker":  # Docker configurations
            warnings = ["url"]
            errors = []
            if "registry" in config:
                num_errors += _checker(["url", "login-file"], "infrastructure",
                                       config["registry"], "errors")
        elif platform in ["hyper-v", "cloud", "libvirt"]:
            logging.info("Platform %s is not yet implemented", platform)
        else:
            logging.error("Unknown infrastructure platform: %s", str(platform))
            num_warnings += 1
            continue  # Skip the syntax verification of unknown platforms
        num_warnings += _checker(warnings, "infrastructure", config, "warnings")
        num_errors += _checker(errors, "infrastructure", config, "errors")
    return num_errors, num_warnings


def verify_exercise_syntax(spec):
    """
    Verifies the syntax of an environment specification.

    :param dict spec: Dictionary of environment specification
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    num_warnings = 0
    num_errors = 0
    funcs = {"metadata": _verify_exercise_metadata_syntax,
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
                logging.info('Optional definition "%s" was not found', key)
            else:
                logging.warning("Unknown definition found: %s", key)
                num_warnings += 1
        else:
            err, warn = func(spec[key])
            num_errors += err
            num_warnings += warn
    return num_errors, num_warnings


def verify_package_syntax(package):
    """
    Verifies the syntax of an package specification.

    :param dict package: Dictionary representation of the package specification
    :return: Number of errors, Number of warnings
    :rtype: tuple(int, int)
    """
    num_warnings = 0
    num_errors = 0

    # Check syntax of metadata section
    if "metadata" not in package:
        logging.error("Metadata section not specified for package!")
        num_errors += 1
    else:
        metadata_warnings = ["name", "description", "version"]
        metadata_errors = ["timestamp", "tag"]
        num_warnings += _checker(metadata_warnings, "metadata",
                                 package["metadata"], "warnings")
        num_errors += _checker(metadata_errors, "metadata",
                               package["metadata"], "errors")

    # Check syntax of contents section
    if "contents" not in package:
        logging.error("Contents section not specified for package!")
        num_errors += 1
    else:
        content_warnings = ["infrastructure", "scoring", "results",
                            "templates", "materials"]
        content_errors = ["environment"]
        num_warnings += _checker(content_warnings, "contents",
                                 package["contents"], "warnings")
        num_errors += _checker(content_errors, "contents",
                               package["contents"], "errors")
    return num_errors, num_warnings


def check_syntax(specfile_path, spec_type="exercise"):
    """
    Checks the syntax of a specification file.

    :param str specfile_path: Path to the YAML specification file
    :param str spec_type: Type of specification file 
    (exercise | package | infra)
    :return: The specification
    :rtype: dict or None

    """
    spec = parse_yaml(specfile_path)
    if spec is None:
        logging.critical("Failed to ingest specification file %s",
                         basename(specfile_path))
        return None
    logging.info("Successfully ingested specification file '%s'",
                 basename(specfile_path))
    if spec_type == "exercise":
        logging.info("Checking exercise syntax...")
        errors, warnings = verify_exercise_syntax(spec)
    elif spec_type == "package":
        logging.info("Checking package syntax...")
        errors, warnings = verify_package_syntax(spec)
    elif spec_type == "infra":
        logging.info("Checking infrastructure syntax...")
        errors, warnings = verify_infra_syntax(spec)
    else:
        logging.error("Unknown specification type in for check_syntax: %s",
                      str(spec_type))
        return None

    if errors == 0 and warnings == 0:
        logging.info("Syntax check successful!")
        return spec
    elif errors == 0:
        logging.warning("Syntax check successful, but there were %d warnings",
                        warnings)
        return spec
    else:
        logging.error("Syntax check failed! Errors: %d\tWarnings: %d",
                      errors, warnings)
        return None
