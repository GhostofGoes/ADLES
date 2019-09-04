If you're not in a virtual environment, make one and activate it: 
```bash
python -m venv ./venv
source ./venv/bin/activate
```

Release steps:
1. Increment version number in `adles/__about__.py`
2. Update CHANGELOG header from UNRELEASED to the version and add the date
3. Run static analysis and lint checks: `tox -e check`
4. Run the test suite: `tox`
5. Ensure a pip install from GitHub source works:
```bash
pip install https://github.com/ghostofgoes/adles/archive/master.tar.gz
```
6. Clean the environment: `bash scripts/clean.sh`
7. Build the wheels
If wheel isn't installed, get it: `pip install -U wheel setuptools`
```bash
python setup.py sdist bdist_wheel --universal
```
8. Upload the wheels
If `twine` isn't installed, get it: `pip install -U twine`
```bash
twine upload dist/*
```
9. Build the Debian package
See `packaging.md` for details on required tools and setup.
```bash
python setup.py --command-packages=stdeb.command bdist_deb
```
10. Create a tagged release on GitHub including:
    a) The relevant section of the CHANGELOG in the body
    b) The source and binary wheels
    c) The .deb package
    d) The documentation as a PDF and Man page (if it's working)
11. Announce the release in the normal places
