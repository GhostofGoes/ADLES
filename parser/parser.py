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


def main():
    """ For testing of the parser """
    from pprint import pprint
    # testfile = 'test_example.yaml'
    # doc = parse_file(testfile)
    # print(doc["name"])

    # specfile = '../specification.yaml'
    specfile = '../examples/competition_example.yaml'
    # specfile = '../examples/tutorial_example.yaml'
    # specfile = '../examples/edurange_example.yaml'
    spec = parse_file(specfile)
    pprint(spec)  # Note that pprint will cause descriptions to go across multiple lines, don't be alarmed

if __name__ == '__main__':
    main()
