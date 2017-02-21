# Overview
Simple tools to make life in RADICL a little less frustrating and a little more automated.

if(sysadmin): 
    automation = happiness

Oh, if you're wondering why the scripts are in the top level directory...
it's because python is retarded with the way it imports.
Wasted an hour on this, if you want to fix it feel free to open an issue or pull request.

# Requirements
* Python 3.2+ (Tested using 3.6)
* Network connection to a vSphere 6.0+ server

## Python Packages
* pyvmomi 6.0+
* docopt 0.6.2+

# Setup

```bash
git clone https://github.com/GhostofGoes/cybersecurity-environment-automation.git
pip3 install -r script-requirements.txt
python3 ./<tool>.py --help
```

# Usage

```bash
python3 ./<tool>.py
```


