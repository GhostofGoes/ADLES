mkdir pip-packages
pip3 download -r requirements.txt -d ./pip-packages
7z a -tzip package.zip -r ./ -xr!*.git* -xr!*.idea -xr!*pycache* -xr!*.zip -xr!diagrams -bb1