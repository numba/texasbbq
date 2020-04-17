#!/usr/bin/env python

""" This is the system test for texasbbq.

It tests that the latest released version of Numba with the latest released
version of umap. If anything is red, it's probably due to a bug with texasbbq.

"""

from texasbbq import (main,
                      git_ls_remote_tags,
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
        return([t for t in git_ls_remote_tags(self.clone_url) if not
                t.startswith("v")][-1])

    @property
    def conda_dependencies(self):
        return ["numpy scikit-learn scipy nose pandas datashader holoviews"]

    @property
    def install_command(self):
        return "pip install -e ."

    @property
    def test_command(self):
        return "nosetests -s umap"


if __name__ == "__main__":
    main(NumbaSource())
