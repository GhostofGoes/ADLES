#!/bin/bash
pip3 install -r requirements.txt --no-index -f ./pip-packages
find . -name *.py -exec chmod +x {} +