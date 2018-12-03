#! coding:utf-8
from setuptools import setup, find_packages
import sys
import codecs
"""
linux:
rm -rf "dist/*";rm -rf "build/*";python3 setup.py bdist_wheel;python2 setup.py bdist_wheel;twine upload "dist/*;rm -rf "dist/*";rm -rf "build/*""
win32:
rm -rf dist&rm -rf build&python3 setup.py bdist_wheel&python2 setup.py bdist_wheel&twine upload "dist/*"&rm -rf dist&rm -rf build
"""

# optional_requires:
#    lxml jsonpath_rw_ext cssselect objectpath: for SimpleParser
#    uvloop: fastest loop for python3.5+ on non-win32 system

py_version = sys.version_info
install_requires = ['requests']

if py_version.major == 2:
    install_requires.append('futures')

if py_version.major == 3 and py_version.minor >= 5:
    install_requires.append('aiohttp>=3.0.5')
    # if  'Windows' not in .system():
    #     install_requires.append('uvloop')

with codecs.open('README.rst', encoding='u8') as f:
    README = f.read()

setup(
    name='torequests',
    version='4.8.1',
    keywords=(
        'requests async multi-thread aiohttp asyncio uvloop asynchronous'),
    description=
    'Async wrapper for requests / aiohttp, and some python crawler toolkits. Let synchronization code enjoy the performance of asynchronous programming. Read more: https://github.com/ClericPy/torequests.',
    long_description=README,
    license='MIT License',
    install_requires=install_requires,
    py_modules=['torequests'],
    author='ClericPy',
    author_email='clericpy@gmail.com',
    url='https://github.com/ClericPy/torequests',
    packages=find_packages(),
    platforms='any',
)
