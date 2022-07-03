# python
# -*- coding: utf-8 -*-
import codecs
import os
import re

from setuptools import find_packages, setup
"""
linux:
rm -rf "dist/*";rm -rf "build/*";python3 setup.py bdist_wheel;twine upload "dist/*;rm -rf "dist/*";rm -rf "build/*""
win32:
rm -rf dist;rm -rf build;python3 setup.py bdist_wheel;twine upload "dist/*"
rm -rf dist;rm -rf build;rm -rf torequests.egg-info
"""

install_requires = [
    "requests",
    "aiohttp>=3.6.2,<4.0.0;python_version>'3.5'",
]

with codecs.open("README.md", encoding="u8") as f:
    long_description = f.read()

here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, 'torequests', '__init__.py'),
                 encoding="u8") as f:
    version = re.search(r'''__version__ = ['"](.*?)['"]''', f.read()).group(1)
desc = "Async wrapper for requests / aiohttp, and some python crawler toolkits. Let synchronization code enjoy the performance of asynchronous programming. Read more: https://github.com/ClericPy/torequests."
keywords = "requests async multi-thread aiohttp asyncio asynchronous".split()
setup(
    name="torequests",
    version=version,
    keywords=keywords,
    description=desc,
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT License",
    install_requires=install_requires,
    py_modules=["torequests"],
    extras_require={
        'security': ['pyOpenSSL >= 0.14', 'cryptography>=1.3.4', 'idna>=2.0.0'],
        'socks': ['PySocks>=1.5.6, !=1.5.7'],
        'all': [
            'pyOpenSSL >= 0.14', 'cryptography>=1.3.4', 'idna>=2.0.0',
            'PySocks>=1.5.6, !=1.5.7', 'psutil', 'pyperclip'
        ],
        'speedups': [
            'aiodns>=1.1',
            'Brotli',
            'cchardet',
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        'Programming Language :: Python',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    author="ClericPy",
    author_email="clericpy@gmail.com",
    url="https://github.com/ClericPy/torequests",
    packages=find_packages(),
    platforms="any",
)
