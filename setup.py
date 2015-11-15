

from setuptools import setup, find_packages

setup(
    name='torequests',
    version='0.0.1',
    keywords=('requests', 'tomorrow', 'async', 'multi-thread',
              'multiprocessing.dummy', 'Pool'),
    description='Requests + Tomorrow. Using tomorrow to make requests async, also can use requests with multiprocessing.dummy for many urls. ',
    license='MIT License',
    install_requires=['requests'],
    py_modules=['torequests'],
    author='ClericPy',
    author_email='pythonld@163.com',
    url='http://clericpy.github.io/',
    packages=find_packages(),
    platforms='any',
)
