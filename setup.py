#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup

setup(name='ownSync',
      version='0.1.0',
      description='Python ownCloud file sync utility',
      author='Luke Wahlmeier',
      author_email='lwahlmeier@gmail.com',
      url='https://github.com/lwahlmeier/ownSync',
      install_requires=['httplib2', 'xml.etree.ElementTree'],
      license='BSD',
      py_modules=['ownSync'],
     )
