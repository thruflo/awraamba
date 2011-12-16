#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'awraamba',
    version = '0.1',
    author = 'James Arthur',
    author_email = 'username: thruflo, domain: gmail.com',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'License :: Public Domain',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet :: WWW/HTTP'
    ],
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'bolt',
        'babel',
        'assetgen',
        'weblayer==0.4.3',
        'FormEncode==1.2.4',
        'psycopg2==2.4.3',
        'SQLAlchemy==0.7.4',
        'PasteScript==1.7.5',
        #'Imaging', <!-- deal with this manually ;)
        'WSGIUtils',
        'pyDNS',
        'pytz',
        'passlib'
    ],
    entry_points = {
        'setuptools.file_finders': [
            'foo = setuptools_git:gitlsfiles'
        ],
        'paste.app_factory': [
            'main=awraamba.app:factory'
        ]
    }
)
