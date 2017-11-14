#! coding:utf-8
from setuptools import setup, find_packages
import sys
import platform
'''
linux:
python3 setup.py bdist_wheel;python2 setup.py bdist_wheel;twine upload dist/*
win32:
python3 setup.py bdist_wheel&python2 setup.py bdist_wheel&twine upload dist/*
'''


py_version = sys.version_info
install_requires = ['requests']
if py_version.major == 2:
    install_requires.append('futures')
if py_version.major == 3 and py_version.minor >= 5:
    install_requires.append('aiohttp')
    # if  'Windows' not in platform.system():
    #     install_requires.append('uvloop')

setup(
    name='torequests',
    version='4.4.11',
    keywords=('requests tomorrow async multi-thread aiohttp asyncio uvloop futures asynchronous'),
    description='Asynchronous requests. Using concurrent.futures to make requests asynchronous, and some functions to make async-coding easy. Besides, add aiohttp+uvloop to enjoy python3.5+ coroutine. Read more: https://github.com/ClericPy/torequests.',
    license='MIT License',
    install_requires=install_requires,
    py_modules=['torequests'],
    author='ClericPy',
    author_email='clericpy@gmail.com',
    url='https://github.com/ClericPy/torequests',
    packages=find_packages(),
    platforms='any',
)
