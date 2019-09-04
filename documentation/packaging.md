# Building Debian apt package

```bash
# Apt dependencies
sudo apt update
sudo apt install debhelper python3-all

# If you're on WSL, you may need this if build fails
# https://github.com/microsoft/WSL/issues/2465
sudo update-alternatives --set fakeroot /usr/bin/fakeroot-tcp

# Install stdeb
pip install stdeb

# Build the package
python setup.py --command-packages=stdeb.command bdist_deb

# See the results
ls -lhAt ./deb_dist
```

# Windows
TBD
