#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name='requests-wsgi-adapter',
    version='0.1',
    description='WSGI Transport Adapter for Requests',
    long_description=open('README.rst').read(),
    author='Sean Brant',
    author_email='brant.sean@gmail.com',
    url='https://github.com/seanbrant/requests-wsgi-adapter',
    license='BSD',
    packages=find_packages(exclude=['tests.py']),
    include_package_data=True,
    zip_safe=False,
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
