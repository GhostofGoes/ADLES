If `twine` isn't installed, get it: `python -m pip install --user -U twine`

1. Increment version number in `adles/__about__.py`
2. Update CHANGELOG header from UNRELEASED to the version and add the date
3. Run static analysis checks (`tox -e check`)
4. Run the test suite on the main supported platforms (`tox`)
    a) Windows
    b) Ubuntu
    c) CentOS
    d) OSX
5. Ensure a pip install from source works on the main platforms:
```bash
pip install https://github.com/ghostofgoes/adles/archive/master.tar.gz
```
6. Clean the environment: `bash ./scripts/clean.sh`
7. Build the wheels
```bash
python setup.py sdist bdist_wheel --universal
```
8. Upload the wheels
```bash
twine upload dist/*
```
9. Build the Debian package
```bash
python setup.py --command-packages=stdeb.command bdist_deb
```
10. Create a tagged release on GitHub including:
    a) The relevant section of the CHANGELOG in the body
    b) The source and binary wheels
    c) The .deb package
11. Announce the release in the normal places
