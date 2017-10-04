# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
import os

from setuptools import find_packages, setup


def read(*parts):
    filename = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(filename, encoding='utf-8') as fp:
        return fp.read()


setup(
    name="django-oscar-opp",
    version="0.2.0",
    url='https://github.com/ashwoods/django-oscar-opp',
    license='MIT',
    description="Oscar payment backend for opp",
    long_description=read('README.rst'),
    author='Raphael Grill, Ashley Camba Garrido',
    author_email='r.grill@nousguide.com',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'django-appconf >= 0.4',
        'requests >= 2.12.1',
        'opp',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
    ],
)
