#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup

setup(name='ownSync',
      version='0.2.0',
      description='Python ownCloud file sync utility',
      author='Luke Wahlmeier',
      author_email='lwahlmeier@gmail.com',
      url='https://github.com/lwahlmeier/ownSync',
      install_requires=['httplib2', 'argparse'],
      license='BSD',
      py_modules=['ownSyncUtils'],
      scripts=['ownSync.py'],
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
      ],
      keywords='owncloud files sync sychronize',
     )
