#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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
            print("Error parsing config file %s" % filename)
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                print("Error position: (%s:%s)" % (mark.line + 1, mark.column + 1))
            else:
                print("Error: ", exc)
            return None  # If there was an error, then there ain't gonna be any markup, so we exit in a obvious way
    return doc


def verify_syntax(spec):
    """
    Verifies the syntax for the dictionary representation of an environment specificaiton
    :param spec: Dictionary of environment specificaiton
    :return: Boolean indicating success or failure
    """
    failed = False
    if spec["metadata"]:
        if not _verify_metadata_syntax(spec["metadata"]):
            print("(ERROR) Invalid metadata syntax")
            failed = True
    else:
        print("(ERROR) No metadata found!")
        failed = True

    if spec["groups"]:
        if not _verify_groups_syntax(spec["groups"]):
            print("(ERROR) Invalid groups syntax")
            failed = True
    else:
        print("(WARNING) No groups found")

    if spec["services"]:
        if not _verify_services_syntax(spec["services"]):
            print("(ERROR) Invalid services syntax")
            failed = True
    else:
        print("(WARNING) No services found")

    if spec["resources"]:
        if not _verify_resources_syntax(spec["resources"]):
            print("(ERROR) Invalid resources syntax")
            failed = True
    else:
        print("(WARNING) No services found")

    if spec["networks"]:
        if not _verify_networks_syntax(spec["networks"]):
            print("(ERROR) Invalid networks syntax")
            failed = True
    else:
        print("(WARNING) No networks found")

    if spec["folders"]:
        if not _verify_folders_syntax(spec["folders"]):
            print("(ERROR) Invalid folders syntax")
            failed = True
    else:
        print("(ERROR) No folders found")
        failed = True

    return failed


def _verify_metadata_syntax(metadata):
    """
    Verifies that the syntax for metadata matches the specification
    :param metadata:
    :return: Boolean indicating success or failure
    """
    failed = False
    if not metadata["name"]:
        print("(ERROR) Missing name in metadata")

    return failed

def _verify_groups_syntax(groups):
    """
    Verifies that the syntax for groups matches the specification
    :param groups:
    :return: Boolean indicating success or failure
    """


def _verify_services_syntax(services):
    """
    Verifies that the syntax for services matches the specification
    :param services:
    :return: Boolean indicating success or failure
    """


def _verify_resources_syntax(resources):
    """
    Verifies that the syntax for resources matches the specification
    :param resources:
    :return: Boolean indicating success or failure
    """


def _verify_networks_syntax(networks):
    """
    Verifies that the syntax for networks matches the specification
    :param networks:
    :return: Boolean indicating success or failure
    """


def _verify_folders_syntax(folders):
    """
    Verifies that the syntax for folders matches the specification
    :param folders:
    :return: Boolean indicating success or failure
    """


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
