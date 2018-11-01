# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [1.4.0] - TODO-XX-XX
### Added
- The CLI can now be ran a module (e.g. `python -m adles`, `python -m adles.vsphere`)
- New argument: `--syslog-server`. Configures saving of log output to the specified Syslog server.
- Added progress bars to: `clone-vms`, `vm-power`, `vm-snapshots`
- Added compatibility warnings for unsupported Python versions
- New dependency: [tqdm](https://github.com/tqdm/tqdm)
- New dependency: [humanfriendly](https://pypi.org/project/humanfriendly/)

### Changed
- Failing to import an optional dependency will now log an error instead
of raising an exception and terminating execution.
- Moved the remaining examples in the project root into `examples/`
- Logs will not longer emit to a syslog server by default.
Syslog server will now only be used if the parameter is set.
- Behind the scenes changes to commandline argument parsing.
Parsing now generates argparse.Namespace objects using argopt library.
This makes argparse features available to use, and enables us to use
libraries such as argcomplete and Gooey that rely on argparse.
- Bumped `pyvmomi` version to 6.5
- Bumped `colorlog` version to 3.1.4

### Removed
- Dropped support for Python 2.7, 3.4, and 3.5
- Removed dependency: `netaddr`
- Removed `Libvirt` and `HyperV` interfaces


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

