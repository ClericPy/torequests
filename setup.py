

from setuptools import setup, find_packages

setup(
    name='torequests',
    version='1.0.3',
    keywords=('requests tomorrow async multi-thread multiprocessing.dummy Pool'),
    description='Requests + Tomorrow. Using tomorrow to make requests async, also can use requests with multiprocessing.dummy for many urls. read more :https://github.com/ClericPy/torequests ',
    license='MIT License',
    install_requires=['requests','futures'],
    py_modules=['torequests'],
    author='ClericPy',
    author_email='pythonld@163.com',
    url='https://github.com/ClericPy/torequests',
    packages=find_packages(),
    platforms='any',
)
