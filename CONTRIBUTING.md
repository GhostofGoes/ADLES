# Contributing to ADLES

Thanks for taking an interest in this awesome little project. We love
to bring new members into the community, and can always use the help.

## Important resources
* Bug reports and issues: create an issue on [GitHub](https://github.com/GhostofGoes/ADLES/issues)
* Discussion: the [Python Discord server](https://discord.gg/python)
* [Documentation](https://adles.readthedocs.io/en/latest/)
* [PyPI](https://pypi.org/project/ADLES/)

# Where to contribute

## Good for beginners
* Documentation. This is especially important since this project is
focused on education. We need extensive documentation that *teaches*
the user (example: how to edit a file) in addition to the normal items.
* Adding unit tests
* Adding functional tests
* Development tooling: `pylint`, `tox`, `pipenv`, etc.
* Running the tests on your system and reporting if anything breaks...
* ...bug reports!

## Major areas
* Adding new deployment providers: Vagrant, Cloud providers (Apache Libcloud), etc.
* Adding to the existing specifications
* Getting the Package specification off the ground
* User interface: finishing the CLI overhaul, adding web GUI, visualizations, etc.

# Getting started
1. Create your own fork of the code through GitHub web interface ([Here's a Guide](https://gist.github.com/Chaser324/ce0505fbed06b947d962))
2. Clone the fork to your computer. This can be done using the
[GitHub desktop](https://desktop.github.com/) GUI , `git clone <fork-url>`,
or the Git tools in your favorite editor or IDE.
3. Create and checkout a new branch in the fork with either your username (e.g. "ghostofgoes"),
or the name of the feature or issue you're working on (e.g. "web-gui").
Again, this can be done using the GUI, your favorite editor, or `git checkout -b <branch> origin/<branch>`.
4. Create a virtual environment:
    * Linux/OSX (Bash)
        ```bash
        python -m pip install --user -U virtualenv
        mkdir -p ~/.virtualenvs/
        python -m virtualenv ~/.virtualenvs/ADLES
        source ~/.virtualenvs/ADLES/bin/activate
        ```
    * Windows (PowerShell)
        ```powershell
        python -m pip install --user -U virtualenv
        New-Item -ItemType directory -Path "$Env:USERPROFILE\.virtualenvs"
        python -m virtualenv "$Env:USERPROFILE\.virtualenvs\ADLES"
        $Env:USERPROFILE\.virtualenvs\ADLES\Scripts\Activate.ps1
        ```
5. Install the package: `python -m pip install -e .`
6. Setup and run the tests (wait, what tests? ...yeah, hey, what a great area to contribute!)
7. Write some code! Git commit messages should information about what changed,
and if it's relevant, the rationale (thinking) for the change.
8. Follow the checklist
9. Submit a pull request!

## Code requirements
* All methods must have type annotations
* Must work on Python 3.5+
* Must work on Windows 10+, Ubuntu 16.04+, and Kali Rolling 2017+
* Try to match the general code style (loosely PEP8)
* Be respectful.
Memes, references, and jokes are ok.
Explicit language (cursing/swearing), NSFW text/content, or racism are NOT ok.

## Checklist before submitting a pull request
* [ ] Update the [CHANGELOG](CHANGELOG.md) (For non-trivial changes, e.g. changing functionality or adding tests)
* [ ] Add your name to the contributors list in the [README](README.md)
* [ ] All tests pass locally
* [ ] Pylint is happy

# Bug reports
Filing a bug report:

1. Answer these questions:
    * [ ] What version of `ADLES` are you using? (`adles --version`)
    * [ ] What operating system and processor architecture are you using?
    * [ ] What version of Python are you using?
    * [ ] What did you do?
    * [ ] What did you expect to see?
    * [ ] What did you see instead?
2. Put any excessive output into a [GitHub Gist](https://gist.github.com/) and include a link in the issue.
3. Tag the issue with "Bug"

**NOTE**: If the issue is a potential security vulnerability, do *NOT* open an issue!
Instead, email: ghostofgoes(at)gmail(dot)com

# Features and ideas
Ideas for features or other things are welcomed. Open an issue on GitHub
detailing the idea, and tag it appropriately (e.g. "Feature" for a new feature).
