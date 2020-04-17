import unittest
import unittest.mock as mock
import io
import os
import subprocess
import textwrap

import texasbbq


class TestEcho(unittest.TestCase):

    def test_echo(self):
        with mock.patch('sys.stdout', new=io.StringIO()) as fake_out:
            texasbbq.echo("test")
            self.assertEqual("::>> test\n", fake_out.getvalue())


class TestExecute(unittest.TestCase):

    def test_execute_true(self):
        # shoud be a no-op
        texasbbq.execute("true")

    def test_execute_false(self):
        with self.assertRaises(subprocess.CalledProcessError) as e:
            texasbbq.execute("false")
            self.assertIn(
                "Command '['false']' returned non-zero exit status 1.",
                str(e)
            )

    def test_execute_capture(self):
        result = texasbbq.execute("echo -n 'test'", capture=True)
        self.assertEqual(b"test", result)


class TestMinicondaURL(unittest.TestCase):

    @mock.patch("texasbbq.UNAME", "Linux")
    def test_linux(self):
        result = texasbbq.miniconda_url()
        self.assertEqual(
            "https://repo.continuum.io/miniconda/"
            "Miniconda3-latest-Linux-x86_64.sh",
            result
        )

    @mock.patch("texasbbq.UNAME", "Darwin")
    def test_osx(self):
        result = texasbbq.miniconda_url()
        self.assertEqual(
            "https://repo.continuum.io/miniconda/"
            "Miniconda3-latest-MacOSX-x86_64.sh",
            result
        )

    @mock.patch("texasbbq.UNAME", "GARBAGE")
    def test_unsupported(self):
        with self.assertRaises(ValueError) as e:
            texasbbq.miniconda_url()
            self.assertIn(
                "Unsupported OS",
                str(e)
            )


class TestWGETConda(unittest.TestCase):

    @mock.patch("texasbbq.execute")
    def test_wget_conda(self, mock_execute):
        texasbbq.wget_conda("test_url", "test_output")
        mock_execute.assert_called_once_with("wget test_url -O test_output")


class TestInjectCondaPath(unittest.TestCase):

    @mock.patch("os.environ", {"PATH": ""})
    def test_inject_conda_path(self):
        texasbbq.inject_conda_path()
        self.assertEqual(
            "/Users/vhaenel/git/texasbbq/miniconda3/bin:"
            "/Users/vhaenel/git/texasbbq/miniconda3/condabin:",
            os.environ["PATH"]
        )


class TestGit(unittest.TestCase):

    @mock.patch("texasbbq.execute")
    def test_git_clone_ref(self, mock_execute):
        texasbbq.git_clone_ref("test_url", "test_ref", "test_dir")
        mock_execute.assert_called_once_with(
            "git clone -b test_ref test_url --depth=1 test_dir")

    @mock.patch("texasbbq.execute")
    def test_git_ls_remote_tags(self, mock_execute):
        mock_execute.return_value = (
            b"ffffffffffffffffffffffffffffffffffffffff	refs/tags/0.1.0\n"
            b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa	refs/tags/0.2.0\n"
        )
        result = texasbbq.git_ls_remote_tags("test_url")
        self.assertEqual(["0.1.0", "0.2.0"], result)
        mock_execute.assert_called_once_with(
            "git ls-remote --tags --refs test_url", capture=True)


class TestConda(unittest.TestCase):

    @mock.patch("texasbbq.execute")
    def test_conda_update_conda(self, mock_execute):
        texasbbq.conda_update_conda()
        mock_execute.assert_has_calls(
            [mock.call("conda update -y -n base -c defaults conda"),
             mock.call("conda install -y conda=4.7")])

    @mock.patch("texasbbq.execute")
    def test_conda_environments(self, mock_execute):
        mock_execute.return_value = textwrap.dedent("""
            {
            "envs": [
                "/test/miniconda3",
                "/test/miniconda3/envs/numba",
                "/test/miniconda3/envs/texasbbq"
            ]
            }""")
        result = texasbbq.conda_environments()
        expected = {
            "miniconda3": "/test/miniconda3",
            "numba":      "/test/miniconda3/envs/numba",
            "texasbbq":   "/test/miniconda3/envs/texasbbq",
        }
        self.assertEqual(expected, result)

    @mock.patch("texasbbq.execute")
    def test_conda_create_env(self, mock_execute):
        texasbbq.conda_create_env("test_env")
        mock_execute.assert_called_once_with(
            "conda create -y -n test_env")

    @mock.patch("texasbbq.execute")
    def test_conda_install(self, mock_execute):
        texasbbq.conda_install("test_env", "test_package")
        mock_execute.assert_called_once_with(
            "conda install -y -n test_env test_package")
