#!/usr/bin/env python
import os
import subprocess
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

try:
    from distutils.config import ConfigParser
except ImportError:
    from configparser import ConfigParser

conf = ConfigParser()
conf.read(['setup.cfg'])

# Get some config values
metadata = dict(conf.items('metadata'))
PACKAGENAME = metadata.get('package_name', 'wiimatch')
DESCRIPTION = metadata.get('description', 'A package for optimal "matching" '
                           'N-dimentional image background using '
                           '(multivariate) polynomials')
AUTHOR = metadata.get('author', 'Mihai Cara')
AUTHOR_EMAIL = metadata.get('author_email', 'help@stsci.edu')
URL = metadata.get('url', 'https://www.stsci.edu/')
LICENSE = metadata.get('license', 'BSD-3-Clause')

if os.path.exists('relic'):
    sys.path.insert(1, 'relic')
    import relic.release
else:
    try:
        import relic.release
    except ImportError:
        try:
            subprocess.check_call(['git', 'clone',
                                   'https://github.com/jhunkeler/relic.git'])
            sys.path.insert(1, 'relic')
            import relic.release
        except subprocess.CalledProcessError as e:
            print(e)
            exit(1)

version = relic.release.get_info()
if not version.date:
    default_version = metadata.get('version', '')
    default_version_date = metadata.get('version-date', '')
    version = relic.git.GitVersion(
        pep386=default_version,
        short=default_version,
        long=default_version,
        date=default_version_date,
        dirty=True,
        commit='',
        post='-1'
    )
relic.release.write_template(version, PACKAGENAME)


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['wiimatch/tests']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name=PACKAGENAME,
    version=version.pep386,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    license=LICENSE,
    url=URL,
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'numpy',
    ],
    tests_require=['pytest'],
    packages=find_packages(),
    cmdclass = {'test': PyTest}
)
