

from setuptools import setup, find_packages
# python setup.py bdist_wheel upload
setup(
    name='torequests',
    version='3.0.1',
    keywords=('requests tomorrow async multi-thread concurrent.futures asynchronous'),
    description='Asynchronous requests. Using concurrent.futures to make requests async(like Tomorrow), and some functions to make async-coding easy. read more :https://github.com/ClericPy/torequests ',
    license='MIT License',
    install_requires=['requests','futures'],
    py_modules=['torequests'],
    author='ClericPy',
    author_email='clericpy@gmail.com',
    url='https://github.com/ClericPy/torequests',
    packages=find_packages(),
    platforms='any',
)
