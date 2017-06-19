#!/usr/bin/env python
from setuptools import setup


setup(
    name='requests-wsgi-adapter',
    version='0.2.3',
    description='WSGI Transport Adapter for Requests',
    long_description=open('README.rst').read(),
    author='Sean Brant',
    author_email='brant.sean@gmail.com',
    url='https://github.com/seanbrant/requests-wsgi-adapter',
    license='BSD',
    py_modules=['wsgiadapter'],
    test_suite='runtests.runtests',
    install_requires=[
        'requests>=1.0',
    ],
    extras_require={
        'tests': [
            'flake8',
            'pytest',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
