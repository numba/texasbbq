texasbbq
========

Smoke out the bugs that break dependent projects.

About
-----

A project that allows you to test a source project against potentially multiple target
projects, i.e. downstream projects that depend on it. This allows an early
warning when developing the source, because a daily master of the source
project can be checked against all significant downstream targets in an
automated fashion. Such testing is especially useful for core libraries, such as
the ones that power the rest of the SciPy ecosystem, and helps to reduce the
risk of breaking an ecosystem with a faulty release.

Name
----

The ``texasbbq`` name was coined during a lightning talk at SciPy 2019 in
Austin, Texas where one of the pun panelists suggested "if you are all about
smoking out bugs, you better call it barbecue!" Puns about "marination" and
"roasting" followed.

Principles
----------

It is just an ancillary script, so let's keep it minimal.

* Minimalism
* Single script
* Simple installation
* Single page README
* Minimal dependencies
* Modular design
* Idempotent behaviour
* Simple license
* Trivial to release

Usage
-----

Configuration happens (for now) in a Python script by subclassing one
``Source`` configuration class as well as several ``Target`` subclasses and
placing these in a configuration script, for example ``switchboard.py``. The
module ``texasbbq`` will then provides a command-line interface for running the
tests (see blow).

The main entry point is a single script, ``texasbbq.py``, which is used to
drive integration testing. This script will run on at least Python 2.7 and 3.7
and has only a single third-party python dependency: `packaging`. Hence it will
probably run on a large variety of different CI systems and platforms. It
provides a pure Python interface to ``conda`` without using a shell language.
A self-contained miniconda distribution containing at least ``conda`` 4.9 will
be downloaded to ensure a clean build.

It has multiple *stages*, which are actions to perform and multiple *targets*,
which are projects to be tested.

Dependencies
------------

* Executable

  * `git`
  * `conda` (4.9) (Will be downloaded during operation, see above.)

* Python packages

  * `packaging`

Sources
-------

Every integration-testing setup configuration must have at least one of
``CondaSource`` or ``GitSource`` to define the source project to be tested. The
difference between the two is that for a ``CondaSource`` you are configuring
that the source be installed via a ``conda`` package. For example the build
artifact result of a nightly or development build. For a ``GitSource`` project
you are installing the project by cloning a copy of the project repository and
building it prior to testing.

Here is an example ``CondaSource`` configuration from the `Numba
<https://numba.pydata.org/>`_ project:

.. code-block:: python

    from texasbbq import CondaSource

    class NumbaSource(CondaSource):

        module = __name__

        @property
        def name(self):
            return "numba"

        @property
        def conda_package(self):
            return "-c numba/label/dev numba"

And here is an example ``GitSource`` configuration from the `Dask
<https://dask.org/>`_ project:

.. code-block:: python

    from texasbbq import GitSource

    class DaskSource(GitSource):

        module = __name__

        @property
        def name(self):
            return "dask"

        @property
        def clone_url(self):
            return "https://github.com/dask/dask"

        @property
        def git_ref(self):
            return "master"

        @property
        def conda_dependencies(self):
            return ["-c conda-forge toolz numpy fsspec"]

        @property
        def install_command(self):
            return "pip install -e ."

Targets
-------

Targets are projects that should be tested as part of the integration tests.
They are specified as either a ``CondaTarget`` or a ``GitTarget``.

In an ideal case, the project ships the tests and running the tests is simply a
matter of installing the (potentially pre-compiled) conda package and running
the tests. In such cases a ``CondaTarget`` will suffice.  In case this isn't
possible, doing a ``git clone``, building the package from source and running
the tests from the clone is also supported. In that case, you will need to use
a ``GitTarget``.

Here is the example ``GitTarget`` configuration for the
`UMAP <https://umap-learn.readthedocs.io/en/latest/>`_ project, when
testing with Numba as a source:

.. code-block:: python

    class UmapTests(GitTarget):
        @property
        def name(self):
            return "umap"

        @property
        def clone_url(self):
            return "https://github.com/lmcinnes/umap"

        @property
        def git_ref(self):
            return([t for t in git_ls_remote_tags(self.clone_url) if not
                    t.startswith("v")][-1])

        @property
        def conda_dependencies(self):
            return ["numpy scikit-learn scipy nose"]

        @property
        def install_command(self):
            return "pip install -e ."

        @property
        def test_command(self):
            return "nosetests -s umap"

Lastly, ``texasbbq.py`` will automatically detect any target subclasses and
make them available.

Command-Line Interface
----------------------

In order to access the command-line interface, import the ``main`` function from ``texasbbq`` and place the following snippet at
the end of your configuration script:

.. code-block:: python

    if __name__ == "__main__":
        main(NumbaSource())

And replace ``NumbaSource`` with the appropriate ``Source`` for your project.

Now, assuming your initial configuration script was called ``switchboard.py``,
this will now be equipped to run one of multiple *stages* for one of multiple
*targets*.

The stages are as follows:

miniconda
  Download and setup miniconda distribution.

environment
  Setup conda environments for each of the targets.

install_source
  Install the source to the given environments.

install_target
  Install each target to the given environments.

tests
  Run tests for each target.


The two stages: ``miniconda`` and ``environment`` are more or less
idempotent.  I.e. if miniconda has been downloaded and installed that step will
not be done again.

By default, all stages and all targets will be run. If you want to limit the
stages use the ``-s`` or ``--stages`` option. If you want to limit the targets
use the ``-t`` or ``--targets`` option.

Examples (assuming your initial configuration script was called ``switchboard.py``)::

    # Only download and install miniconda
    $ ./switchboard.py -s miniconda

    # Only run tests for umap
    $ ./switchboard.py -s tests -t umap

    # Only download miniconda and setup environment for umap
    $ ./switchboard.py -s miniconda environment -t umap

Please see the output of ``./switchboard.py -h`` for more information.

Installation
------------

``texasbbq`` can be installed with ``pip`` from PyPI::

    pip install texasbbq

or directly from GitHub::

    pip install git+https://github.com/numba/texasbbq.git

The ``texasbbq.py`` module can also be downloaded locally using commands
like ``curl`` or ``wget``.


Continuous Integration Testing Examples
---------------------------------------

* https://github.com/numba/numba-integration-testing
* https://github.com/jrbourbeau/dask-integration-testing

Caveats
-------

* The script is reasonably robust but won't respond well to malformed user
  input. For example, if you try to run only the ``test`` stage without the
  others it is likely to fail.

* If you are running this locally and you already have an anaconda or miniconda
  distribution activated you may run into problems. In such cases it is best to
  run this script from a vanilla (non-customized) shell.


Change Log
----------

0.2.1
.....

* Metadata update

0.2.0
.....

* First "real" release after two years of development and usage
* Package has been running in production for quite some time and appears stable
* Special thanks to `Kevin Cawly <https://github.com/KevinCawley>`_ for
  providing `pip support <https://github.com/numba/texasbbq/pull/25>`_.
* Thank you also to `James Bourbeau https://github.com/jrbourbeau>`_, `Stuart
  Archibald <https://github.com/stuartarchibald>`_ and
  `Stan Seibert <https://github.com/seibert>`_ for reviews and feedback

0.1.0
.....

* Initial tag and typosquat PyPi

License
-------

texasbbq is Copyright (c) 2019, Anaconda, Inc. and provided under the terms of
a 2-Clause BSD license.
