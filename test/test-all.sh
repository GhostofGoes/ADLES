#!/usr/bin/env bash

adles
adles -h
adles --version
adles validate examples/spoofing-tutorial.yaml
adles --verbose validate examples/spoofing-tutorial.yaml
adles --no-color -v validate examples/spoofing-tutorial.yaml
adles -v validate examples/competition.yaml
adles -v validate examples/competition-with-docker.yaml
adles -v validate examples/experiment.yaml
adles -v validate examples/edurange_total-recon.yaml
adles -v validate examples/pentest-tutorial.yaml
adles -v validate examples/firewall-tutorial.yaml
adles -v -t infra validate infra.yaml
adles -v -t exercise validate examples/experiment.yaml
adles --list-examples
adles --print-example competition
adles --print-spec exercise
vsphere clone -h
vsphere clone --version
vsphere cleanup --help
vsphere cleanup --version
vsphere power -h
vsphere power --version
vsphere info -h
vsphere info --version
vsphere snapshot -h
vsphere snapshot --version
