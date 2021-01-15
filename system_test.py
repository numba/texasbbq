#!/usr/bin/env python

""" This is the system test for texasbbq.

It tests that the latest released version of Numba with the latest released
version of umap. If anything fails, it's probably due to a bug in texasbbq.

"""

from texasbbq import (main,
                      git_latest_tag,
                      CondaSource,
                      GitTarget,
                      )


class NumbaSource(CondaSource):

    module = __name__

    @property
    def name(self):
        return "numba"

    @property
    def conda_package(self):
        return "numba"


class UmapTests(GitTarget):
    @property
    def name(self):
        return "umap"

    @property
    def clone_url(self):
        return "https://github.com/lmcinnes/umap"

    @property
    def git_ref(self):
        return git_latest_tag(self.clone_url,
                              vprefix=False,
                              exclude_filter=lambda x: x.startswith("v"))

    @property
    def conda_dependencies(self):
        return ["numpy pytest nose scikit-learn pynndescent scipy pandas bokeh "
                "matplotlib datashader holoviews tensorflow scikit-image"]

    @property
    def install_command(self):
        return "pip install -e ."

    @property
    def test_command(self):
        return "pytest"


if __name__ == "__main__":
    main(NumbaSource())
