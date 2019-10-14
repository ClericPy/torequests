# python
#! coding:utf-8
import codecs
import os
import sys

from setuptools import find_packages, setup
"""
linux:
rm -rf "dist/*";rm -rf "build/*";python3 setup.py bdist_wheel;python2 setup.py bdist_wheel;twine upload "dist/*;rm -rf "dist/*";rm -rf "build/*""
win32:
rm -rf dist;rm -rf build;python3 setup.py bdist_wheel;python2 setup.py bdist_wheel;twine upload "dist/*";rm -rf dist;rm -rf build;rm -rf torequests.egg-info
"""

# optional_requires:
#    lxml jsonpath_rw_ext cssselect objectpath: for SimpleParser
#    uvloop: fastest loop for python3.5+ on non-win32 system

py_version = sys.version_info
install_requires = ["requests"]

if py_version.major == 2:
    install_requires.append("futures")

if py_version.major == 3 and py_version.minor >= 6:
    install_requires.append("aiohttp==3.6.2")
    if sys.platform not in ('win32', 'cygwin', 'cli'):
        install_requires.append("uvloop")

with codecs.open("README.md", encoding="u8") as f:
    long_description = f.read()

here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(
        os.path.join(here, 'torequests', '__version__'), encoding="u8") as f:
    version = f.read().strip()

setup(
    name="torequests",
    version=version,
    keywords=(
        "requests async multi-thread aiohttp asyncio uvloop asynchronous"),
    description=
    "Async wrapper for requests / aiohttp, and some python crawler toolkits. Let synchronization code enjoy the performance of asynchronous programming. Read more: https://github.com/ClericPy/torequests.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT License",
    install_requires=install_requires,
    py_modules=["torequests"],
    author="ClericPy",
    author_email="clericpy@gmail.com",
    url="https://github.com/ClericPy/torequests",
    packages=find_packages(),
    platforms="any",
)
