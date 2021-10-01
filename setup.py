""" texasbbq """

from setuptools import setup
from os import path
# io.open is needed for projects that support Python 2.7
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='texasbbq',
    version='0.2.1',
    description='Smoke out the bugs that break dependent projects.',
    url='https://github.com/numba/texasbbq',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='testing development',
    py_modules=["texasbbq"],
    python_requires='>=3.4, <4',
)
