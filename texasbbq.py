#!/usr/bin/env python

""" texasbbq - smoke out the bugs that break dependent packages. """

import argparse
import inspect
import os
import shlex
import subprocess
import sys
import json

from packaging.version import parse


MINICONDA_BASE_URL = "https://repo.continuum.io/miniconda/"
MINCONDA_FILE_TEMPLATE = "Miniconda3-latest-{}.sh"
MINCONDA_INSTALLER = "miniconda.sh"
MINCONDA_PATH = "miniconda3"
MINCONDA_FULL_PATH = os.path.join(os.getcwd(), MINCONDA_PATH)
MINCONDA_BIN_PATH = os.path.join(MINCONDA_FULL_PATH, "bin")
MINCONDA_CONDABIN_PATH = os.path.join(MINCONDA_FULL_PATH, "condabin")

LINUX_X86 = "Linux-x86"
LINUX_X86_64 = "Linux-x86_64"
MACOSX_X86_64 = "MacOSX-x86_64"

STAGE_MINICONDA = "miniconda"
STAGE_ENVIRONMENT = "environment"
STAGE_INSTALL_SOURCE = "install_source"
STAGE_INSTALL_TARGET = "install_target"
STAGE_TESTS = "tests"
ALL_STAGES = [
    STAGE_MINICONDA,
    STAGE_ENVIRONMENT,
    STAGE_INSTALL_SOURCE,
    STAGE_INSTALL_TARGET,
    STAGE_TESTS,
]


PREFIX = "::>>"


def echo(value):
    """Print to stdout with prefix."""
    print("{} {}".format(PREFIX, value))


def execute(command, capture=False):
    """Execute a command and potentially capture and return its output."""
    echo("running: '{}'".format(command))
    if capture:
        return subprocess.check_output(shlex.split(command))
    else:
        subprocess.check_call(shlex.split(command))


UNAME = execute("uname", capture=True).strip().decode("utf-8")


def miniconda_url():
    """Get the correct miniconda download url."""
    if UNAME == "Linux":
        filename = MINCONDA_FILE_TEMPLATE.format(LINUX_X86_64)
    elif UNAME == "Darwin":
        filename = MINCONDA_FILE_TEMPLATE.format(MACOSX_X86_64)
    else:
        raise ValueError("Unsupported OS")
    return MINICONDA_BASE_URL + filename


def wget_conda(url, output):
    """Download miniconda.sh with wget."""
    execute("wget {} -O {}".format(url, output))


def install_miniconda(install_path):
    """Bootstrap miniconda to a given path."""
    execute("bash miniconda.sh -b -p {}".format(install_path))


def inject_conda_path():
    """Prefix the $PATH with the miniconda binary paths."""
    os.environ["PATH"] = ":".join(
        [MINCONDA_BIN_PATH, MINCONDA_CONDABIN_PATH]
        + os.environ["PATH"].split(":")
    )


# untested, because pending removal
def git_clone(url):
    """Run 'git clone' with a given url."""
    execute("git clone {}".format(url))


def git_clone_ref(url, ref, directory):
    """Run 'git clone' with a given ref, url and directory."""
    execute("git clone -b {} {} --depth=1 {}".format(ref, url, directory))


# untested, because pending removal
def git_tag():
    """Run git tag locally to get all tags."""
    return execute("git tag", capture=True).split('\n')


def git_ls_remote_tags(url):
    """Run git ls-remote to obtain all tags available at remote url."""
    return [os.path.basename(line.split("\t")[1])
            for line in execute("git ls-remote --tags --refs {}".format(url),
            capture=True).decode("utf-8").split("\n") if line]


def git_latest_tag(url, vprefix=True, exclude_filter=lambda x: False):
    """ Get the latest tag from a git repository.

    This uses packaging.version.parse to sort the tags at the given url and
    returns the largest one.

    Parameters
    ----------
    url: str
        The url of the git reproitory to use
    vprefix: bool
        Prefix the return value with the letter 'v'
    exclude_filter: single argument callable
        A filter to exclude certain tags from the git repo

    Returns
    -------
    str: the latest tag from the git repo
    """

    latest = str(sorted([parse(t) for t in git_ls_remote_tags(url)
                         if not exclude_filter(t)])[-1])
    return "v" + latest if vprefix else latest


# untested, because pending removal
def git_checkout(tag):
    """Run 'git checkout' on a given tag."""
    execute("git checkout {}".format(tag))


def conda_update_conda():
    """Get miniconda to update itself."""
    execute("conda update -y -n base -c defaults conda")


def conda_environments():
    """Return a dict of conda environments mapping name to path."""
    return dict(
        (
            (os.path.basename(i), i)
            for i in json.loads(
                execute("conda env list --json", capture=True)
            )["envs"]
        )
    )


def conda_create_env(name):
    """Create a conda environment with a given name."""
    execute("conda create -y -n {}".format(name))


def conda_install(env, name):
    """Use conda to install a package into an environment."""
    execute("conda install -y -n {} {}".format(env, name))

def pip_install(env, name):
    """Use pip to install a package into an environment."""
    execute("conda run --no-capture-output -n {} pip install {}".format(env, name))
    

class GitSource(object):
    """Subclass this to configure a source project from Git. """

    @property
    def name(self):
        """Name of the source.

        This will be used as the directory to clone into.

        Returns
        -------
        name : str
            The name of the project.

        """
        raise NotImplementedError

    @property
    def clone_url(self):
        """Canonical clone url for the source.

        This will be used to clone the source.

        Returns
        -------
        url : str
            A 'git clone' compatible url.

        """
        raise NotImplementedError

    @property
    def git_ref(self):
        """The target git ref to checkout.

        This function must work out which ref (branch or tag should be checked
        out and return that. Since this is for a source, a branch such
        as `master` is probably appropriate.

        Returns
        -------
        ref : str
            The git ref to checkout.

        """
        raise NotImplementedError

    @property
    def conda_dependencies(self):
        """Conda dependencies for this source.

        The conda dependencies for this source. If you need to install things
        in a specific order with multiple, subsequent, `conda` calls, use
        multiple strings. You can include any channel information such as `-c
        numba` in the string.

        Returns
        -------
        dependencies : list of str
            All conda dependencies.

        """
        raise NotImplementedError

    @property
    def install_command(self):
        """Execute command to install the source.

        Use this to execute the command or commands you need to install the
        source. You may assume that the commands will be executed inside the
        root directory of your clone.

        Returns
        -------
        command : str
            The command to execute to install the source

        """
        raise NotImplementedError

    def install(self, env):
        """Install source into conda environment.

        Parameters
        ----------
        env: str
            The conda environment to install into

        """
        if not os.path.exists(self.name):
            execute("git clone -b {} {} {}".format(
                self.git_ref, self.clone_url, self.name))
            for dep in self.conda_dependencies:
                conda_install(env, dep)
            os.chdir(self.name)
            execute("conda run --no-capture-output -n {} {}".format(env, self.install_command))
            os.chdir('../')


class CondaSource(object):

    @property
    def name(self):
        """Name of the source.

        Returns
        -------
        name : str
            The name of the source.

        """
        raise NotImplementedError

    @property
    def conda_package(self):
        """Name of the source conda package.

        Returns
        -------
        conda_package : str
            The name of the source conda package

        """
        raise NotImplementedError

    def install(self, env):
        """Install source into conda environment.

        Parameters
        ----------
        env: str
            The conda environment to install into

        """
        conda_install(env, self.conda_package)


class GitTarget(object):
    """Subclass this to configure a target which is installed from git."""
    @property
    def name(self):
        """Name of the target.

        This will be used as the directory to clone into as well as selecting
        the target from the command line.

        Returns
        -------
        name : str
            The name of the target.

        """
        raise NotImplementedError

    @property
    def clone_url(self):
        """Canonical clone url for the target.

        This will be used to clone the target.

        Returns
        -------
        url : str
            A 'git clone' compatible url.

        """
        raise NotImplementedError

    @property
    def git_ref(self):
        """The target git ref to checkout.

        This function must work out which ref (branch or tag should be checked
        out and return that. A good start is to use
        `git_ls_remote_tags(self.clone_url)` to obtain a list of tags from the
        remote. If you want to use `master` just return that.

        Returns
        -------
        ref : str
            The git ref to checkout.

        """
        raise NotImplementedError

    @property
    def conda_dependencies(self):
        """Conda dependencies for this target.

        The conda dependencies for this target. If you need to install things
        in a specific order with multiple, subsequent, `conda` calls, use
        multiple strings. You can include any channel information such as `-c
        numba` in the string.

        Returns
        -------
        dependencies : list of str
            All conda dependencies.
        """
        raise NotImplementedError
        
    @property
    def pip_dependencies(self):
        """Pip dependencies for this target.
        
        The pip dependencies for this target. If you need to install things
        in a specific order with multiple, subsequent, 'pip' calls, use
        multiple strings. You can include any channel information such as '-c
        numba' in the string. If there are no pip dependencies, return an empty 
        list.
        
        Returns
        -------
        dependencies : list of str
            All pip dependencies
        """
        return []

    def install_command(self):
        """Execute command to install the target.

        Use this to execute the command or commands you need to install the
        target.

        """
        raise NotImplementedError

    def test_command(self):
        """Execute command to run tests.

        Use this to execute the command or commands you need to run the
        test-suite.

        """
        raise NotImplementedError

    def clone(self):
        git_clone_ref(self.clone_url, self.git_ref, self.name)

    def install(self):
        """Install target into conda environment."""
        if not os.path.exists(self.name):
            self.clone()
        os.chdir(self.name)
        execute("conda run --no-capture-output -n {} {}".format(self.name, self.install_command))
        os.chdir('../')

    def test(self):
        """Run targets test command inside conda environment."""
        os.chdir(self.name)
        execute("conda run --no-capture-output -n {} {}".format(self.name, self.test_command))
        os.chdir('../')


class CondaTarget(object):
    """Subclass this to configure a target which is installed via conda."""

    @property
    def name(self):
        """Name of the target.

        This will be used for the name of the conda envoironment to test in
        and as target from the command line.

        Returns
        -------
        name : str
            The name of the target.

        """
        raise NotImplementedError

    @property
    def conda_package(self):
        """Name of the source conda package.

        Returns
        -------
        conda_package : str
            The name of the source conda package

        """
        raise NotImplementedError

    @property
    def conda_dependencies(self):
        """Conda dependencies for this target.

        The conda dependencies for this target. If you need to install things
        in a specific order with multiple, subsequent, `conda` calls, use
        multiple strings. You can include any channel information such as `-c
        numba` in the string.

        Returns
        -------
        dependencies : list of str
            All conda dependencies.
        """
        raise NotImplementedError
    
    @property
    def pip_dependencies(self):
        """Pip dependencies for this target.
        
        The pip dependencies for this target. If you need to install things
        in a specific order with multiple, subsequent, 'pip' calls, use
        multiple strings. You can include any channel information such as '-c
        numba' in the string. If there are no pip dependencies, return an empty 
        list.
        
        Returns
        -------
        dependencies : list of str
            All pip dependencies
        """
        return []
    
    def test_command(self):
        """Execute command to run tests.

        Use this to execute the command or commands you need to run the
        test-suite.

        Returns
        -------
        command : str
            The command to execute to run the test suite.

        """
        raise NotImplementedError

    def install(self):
        """Install target into conda environment.  """
        conda_install(self.name, self.conda_package)

    def test(self):
        """Run targets test command inside conda environment."""
        execute("conda run --no-capture-output -n {} {}".format(self.name, self.test_command))


def bootstrap_miniconda():
    """Download, install and update miniconda."""
    url = miniconda_url()
    if not os.path.exists(MINCONDA_INSTALLER):
        wget_conda(url, MINCONDA_INSTALLER)
    if not os.path.exists(MINCONDA_FULL_PATH):
        install_miniconda(MINCONDA_FULL_PATH)
    inject_conda_path()
    conda_update_conda()


def setup_environment(target):
    """Setup conda environment for target and install dependencies."""
    if target.name not in conda_environments():
        conda_create_env(target.name)
        for dep in target.conda_dependencies:
            conda_install(target.name, dep)
        for dep in target.pip_dependencies:
            pip_install(target.name, dep)


def switch_environment(target):
    """ TO BE REMOVED """
    switch_environment_path(target.name)


def print_environment_details(target):
    """Print details of the conda environment."""
    execute("conda env export -n {}".format(target.name))
    execute("conda list -n {}".format(target.name))


def print_package_details(source_name, target_name):
    lines = execute("conda list -n {}".format(target_name),
                    capture=True).decode("utf-8").split("\n")
    for l in lines[:3]:
        print(l)
    for l in lines[3:]:
        if source_name in l or target_name in l:
            print(l)


def find_all_targets(module):
    """Inspect a module and discover all subclasses of GitTarget and
    CondaTarget. """
    return [
        obj()
        for name, obj in inspect.getmembers(sys.modules[module])
        if inspect.isclass(obj)
        and (issubclass(obj, GitTarget) or issubclass(obj, CondaTarget))
        and (obj is not GitTarget and obj is not CondaTarget)
    ]


def parse_arguments(available_targets):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--stages",
        nargs="*",
        type=str,
        choices=ALL_STAGES,
        default=ALL_STAGES,
        metavar="STAGE",
    )
    parser.add_argument(
        "-t",
        "--targets",
        nargs="*",
        type=str,
        choices=list(available_targets.keys()),
        default=list(available_targets.keys()),
        metavar="TARGET",
    )
    return parser.parse_args()


def run(source, stages, available_targets, targets):
    """Run the integration testing dance.

    Parameters
    ----------
    source: GitSource or CondaSource
        The source for the integration testing dance.
    stages: list of str
        The stages of the dance to execute.
    available_targets: list or str
        The list of targets available in the module
    targets: list of str
        The targets to actually test on.

    """
    failed = []
    basedir = os.getcwd()
    if STAGE_MINICONDA in stages:
        bootstrap_miniconda()
    else:
        inject_conda_path()
    for name, target in available_targets.items():
        if name in targets:
            os.chdir(basedir)
            if STAGE_ENVIRONMENT in stages:
                setup_environment(target)
            if STAGE_INSTALL_SOURCE in stages:
                source.install(target.name)
            if STAGE_INSTALL_TARGET in stages:
                target.install()
            print_environment_details(target)
            if STAGE_TESTS in stages:
                try:
                    target.test()
                except subprocess.CalledProcessError:
                    failed.append(target.name)
            print_package_details(source.name, target.name)
    if STAGE_TESTS in stages:
        if failed:
            echo("The following tests failed: '{}'".format(failed))
            sys.exit(23)
        else:
            echo("All integration tests successful")


def main(source):
    """Main entry point.

    Parameters
    ----------
    source: GitSource or CondaSource
        The source for the integration testing dance.
    """
    available_targets = dict(
        (target.name, target) for target in find_all_targets(source.module)
    )
    args = parse_arguments(available_targets)
    echo("stages are: '{}'".format(args.stages))
    echo("targets are: '{}'".format(args.targets))
    run(source, args.stages, available_targets, args.targets)
