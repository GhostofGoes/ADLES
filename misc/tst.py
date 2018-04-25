
import os
import related
from related import (
    to_yaml, from_yaml, to_model,
    StringField, SequenceField, MappingField, IntegerField,
    URLField
)


# TODO: open a GitHub issue?
# How do a have a list of mixed model types/classes

@related.mutable
class Platform(object):
    pass


@related.immutable
class VsphereSpec(object):
    hostname = StringField(required=True)
    template_folder = StringField(key='template-folder', required=True)
    port = IntegerField(required=False)  # validate range?
    # TODO: validate the path exists?
    login_file = StringField(key='login-file', required=False)
    datacenter = StringField(required=False)
    datastore = StringField(required=False)
    server_root = StringField(key='server-root', required=False)
    vswitch = StringField(required=False)


@related.immutable
class DockerSpec(object):
    url = URLField(required=False)


@related.immutable
class Infra(object):
    vmware_vsphere = related.ChildField(VsphereSpec, required=False)
    docker = related.ChildField(VsphereSpec, required=False)


F = os.path.join('examples', 'related-test-infra.yaml')
yml = open(F).read().strip()
yml_dct = from_yaml(yml)
print(yml_dct)

infra = to_model(Infra, yml_dct)

print(infra)
print(type(infra))
print(dir(infra))
print(repr(infra.vmware_vsphere))

