#!/usr/bin/env bash

adles
adles -h
adles --version
adles -c examples/spoofing-tutorial.yaml
adles --verbose --validate examples/spoofing-tutorial.yaml
adles --no-color -v -c examples/spoofing-tutorial.yaml
adles -v -c examples/competition.yaml
adles -v -c examples/competition-with-docker.yaml
adles -v -c examples/experiment.yaml
adles -v -c examples/edurange_total-recon.yaml
adles -v -c examples/pentest-tutorial.yaml
adles -v -c examples/firewall-tutorial.yaml
adles -v -t infra -c infra.yaml
adles -v -t exercise -c examples/experiment.yaml
adles --list-examples
adles --print-example competition
adles --print-spec exercise
clone-vms
clone-vms -h
clone-vms --version
cleanup-vms
cleanup-vms --help
cleanup-vms --version
vm-power
vm-power -h
vm-power --version
vsphere-info
vsphere-info -h
vsphere-info --version
vm-snapshots
vm-snapshots -h
vm-snapshots --version
