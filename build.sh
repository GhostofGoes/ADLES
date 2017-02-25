#!/bin/bash
mkdir pip-packages
pip3 download -r requirements.txt -d ./pip-packages
find . -path '*/.*' -prune -o -type f -print | zip ~/package.zip -@