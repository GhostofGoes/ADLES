# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## NEXT - XXXX-XX-XX

### Added
- 

### Changed
- Moved install dependencies to a requirements file

### Dev
- Standardized formatting on [Black](https://github.com/psf/black)
- Linting: added several `flake8` plugins, added check using `vulture`
- Moved requirements out of tox and into files

## [1.4.0] - 2019-09-04

**Notable changes**
- New CLI command syntax, run `adles --help` for details or checkout the Usage section in the README 
- Consolidated the vSphere helper scripts (e.g. `vm-power`) into a single command, `vsphere` . For usage, run `vsphere --help`.
- **ADLES now requires Python 3.6+**. It is included or easily installable on any modern Linux distribution, Windows, and OSX.

### Added
- The CLI can now be invoked a Python module (e.g. `python -m adles`, `python -m adles.vsphere`)
- Added two new specification fields to all spec types: `spec-type` and `spec-version`
- New argument: `--syslog`. Configures saving of log output to the specified Syslog server.
- Added progress bars to the cloning, power, and snapshot vSphere helper commands
- Support the `NO_COLOR` environment variable (per [no-color.org](https://no-color.org/))
- New dependencies: [tqdm](https://github.com/tqdm/tqdm) and [humanfriendly](https://pypi.org/project/humanfriendly/)
- Debian package (See the [GitHub releases page](https://github.com/GhostofGoes/ADLES/releases))

### Changed
- Failing to import an optional dependency will now log an error instead
of raising an exception and terminating execution.
- Logs will not longer emit to a syslog server by default.
Syslog server will now only be used if the parameter is set.
- Behind the scenes changes to commandline argument parsing that will
make adding future functionality easier and enable usage of other
third-party libraries that use `argparse`.
- Lots of code cleanup and formatting
- Bumped dependency versions
- Various other minor changes, see the Git pull request diff for all the changes

### Removed
- Dropped support for Python < 3.6
- Removed `Libvirt` and `HyperV` interfaces
- Removed dependency: `netaddr`

### Dev
- Added Tox for test running and linting
- Added `.editorconfig`
- Added `.gitattributes`
- Reorganized some documentation
- Removed CodeClimate
- Moved the remaining examples in the project root into `examples/`
- Added unit tests to Travis CI

## [1.3.6] - 2017-12-19
### Fixed
- Fixed issue with any of the commandline scripts where just entering
 the script name (e.g "adles") on the commandline would error,
 instead of printing help as a user would expect.
- Fixed vm_snapshots script outputting to the wrong log file.

### Changed
- Under-the-hood improvements to how arguments are parsed
and keyboard interrupts are handled.


## [1.3.5] - 2017-12-13
### Changed
- Move package dependencies into setup.py from requirements.txt.


## [1.3.4] - 2017-12-13
### Added
- Man page on Linux systems!


## [1.3.3] - 2017-11-25
### Added
- The ability to relocate a VM to a new host and/or datastore to the VM class.
- The ability to change the mode of a VM HDD to the VM class.

### Changed
- Cleaned up docstrings in vm.py.


## [1.3.2] - 2017-11-25
### Added
- The ability to resize a HDD to the VM class.


## [1.3.1] - 2017-11-24
### Fixed
- Fixed bug where interfaces (and their dependencies) would be imported,
even if they were not being used. This caused the "pip install docker" error.

### Changed
- Minor improvements to logging.


## [1.3.0] - 2017-07-02
### Added
- An interface for libvirt (LibvirtInterface).
- LibcloudInterface that is inherited by LibvirtInterface and CloudInterface.
- Libvirt to infrastructure-specification.
- libvirt to optional-requirements.

### Changed
- Significant changes to class heirarachy. All interfaces now inherit from Interface and class its init method.
There is a separate PlatformInterface that has most of the functionality Interface did, and this is what is now called from main().
- Tweaked some boilerplate code in the interfaces.
- Updated parser.
- Formatting tweaks.
- Moved apache-libcloud to requirements.


## [1.2.0] - 2017-07-02
Initial stab at cloud interface using Apache libcloud
(quickly superseded by 1.3.0, so ignore this version).

