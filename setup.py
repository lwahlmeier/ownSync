#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup

VERSION = '0.6.0'

setup(name='ownSync',
      version=VERSION,
      description='Python ownCloud file sync utility',
      author='Luke Wahlmeier',
      author_email='lwahlmeier@gmail.com',
      url='https://github.com/lwahlmeier/ownSync',
      install_requires=['requests', 'argparse'],
      license='BSD',
      py_modules=['ownSyncUtils'],
      scripts=['ownSync.py'],
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'Topic :: Internet',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
      ],
      keywords='owncloud files sync sychronize',
      download_url = 'https://github.com/lwahlmeier/ownSync/tarball/'+VERSION,
     )
