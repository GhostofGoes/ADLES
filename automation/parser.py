#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging


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
        if not _verify_metadata_syntax(spec["metadata"]):
            logging.error("Invalid metadata syntax")
            status = False
    else:
        logging.error("No metadata found!")
        status = False

    if "groups" in spec:
        if not _verify_groups_syntax(spec["groups"]):
            logging.error("Invalid groups syntax")
            status = False
    else:
        logging.warning("No groups found")

    if "services" in spec:
        if not _verify_services_syntax(spec["services"]):
            logging.error("Invalid services syntax")
            status = False
    else:
        logging.warning("No services found")

    if "resources" in spec:
        if not _verify_resources_syntax(spec["resources"]):
            logging.error("Invalid resources syntax")
            status = False
    else:
        logging.warning("No services found")

    if "networks" in spec:
        if not _verify_networks_syntax(spec["networks"]):
            logging.error("Invalid networks syntax")
            status = False
    else:
        logging.warning("No networks found")

    if "folders" in spec:
        if not _verify_folders_syntax(spec["folders"]):
            logging.error("Invalid folders syntax")
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
    if not metadata["name"]:
        logging.error("Missing name in metadata")
        status = False

    return status


def _verify_groups_syntax(groups):
    """
    Verifies that the syntax for groups matches the specification
    :param groups:
    :return: Boolean indicating success or failure
    """
    status = True
    return status


def _verify_services_syntax(services):
    """
    Verifies that the syntax for services matches the specification
    :param services:
    :return: Boolean indicating success or failure
    """
    status = True
    return status


def _verify_resources_syntax(resources):
    """
    Verifies that the syntax for resources matches the specification
    :param resources:
    :return: Boolean indicating success or failure
    """
    status = True
    return status


def _verify_networks_syntax(networks):
    """
    Verifies that the syntax for networks matches the specification
    :param networks:
    :return: Boolean indicating success or failure
    """
    status = True
    return status


def _verify_folders_syntax(folders):
    """
    Verifies that the syntax for folders matches the specification
    :param folders:
    :return: Boolean indicating success or failure
    """
    status = True
    return status


def main():
    """ For testing of the parser """
    from pprint import pprint
    # testfile = 'test_example.yaml'
    # doc = parse_file(testfile)
    # print(doc["name"])

    # specfile = '../examples/edurange_example.yaml'
    # specfile = '../specification.yaml'
    # specfile = '../examples/competition_example.yaml'
    specfile = '../examples/tutorial_example.yaml'
    spec = parse_file(specfile)
    pprint(spec)  # Note that pprint will cause descriptions to go across multiple lines, don't be alarmed

if __name__ == '__main__':
    main()
