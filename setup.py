# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup, find_packages
from setuptools.command import test

class TestCommand(test.test):
    def run_twisted(self):
        from twisted.trial import runner
        from twisted.trial import reporter

        from pyamf.tests import suite

        r = runner.TrialRunner(reporter.VerboseTextReporter)
        r.run(suite())

    def run_tests(self):
        try:
            import twisted

            self.run_twisted()
        except ImportError:
            test.test.run_tests(self)

import sys

install_requires = ["fpconst>=0.7.2", "Importing>=1.9.2"]
if sys.version_info < (2, 5):
    install_requires.extend(["elementtree >= 1.2.6", "uuid>=1.30"])

keyw = """\
amf amf0 amf3 flex flash remoting rpc http flashplayer air bytearray
objectproxy arraycollection recordset actionscript decoder encoder
gateway"""

setup(name = "PyAMF",
    version = "0.3",
    description = "AMF support for Python",
    long_description = open('README.txt', 'rt').read(),
    url = "http://pyamf.org",
    author = "The PyAMF Project",
    author_email = "dev@pyamf.org",
    keywords = keyw,
    packages = find_packages(exclude=["*.tests"]),
    install_requires = install_requires,
    test_suite = "pyamf.tests.suite",
    zip_safe=True,
    license = "MIT License",
    cmdclass = {'test': TestCommand},
    extras_require={
        'wsgi': ['wsgiref'],
        'twisted': ['Twisted>=2.5.0'],
        'django': ['Django>=0.96']
    },
    classifiers = [
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
