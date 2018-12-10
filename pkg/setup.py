import json

from setuptools import setup, find_packages

versionData = json.loads(open('version.json', 'r').read())

setup(
    name=versionData['name'],

    version='{major}.{minor}.{bugfix}'.format(**versionData['version']['number']),

    description='JADN Schema/Message Translator & Validator',
    # long_description="The Server for NetVamp, that provides the REST API, controllers, and database.",

    # author='G2-Inc.',
    # author_email='screaming_bunny@g2-inc.com',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        "License :: Apache 2.0 License",
        'Intended Audience :: Information Technology',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Topic :: Security :: Translation :: Validation'
    ],

    packages=find_packages(),

    install_requires=[d.replace('\n', '') for d in open('requirements.txt', 'r').readlines()],

    # Python 2.7, 3.6+ but not 4
    python_requires='>=2.7, !=3.[1-5], <4',

    package_data={
        str(versionData['name']): [
            './{}/*'.format(versionData['pkg_name']),
            './{}/convert/theme.*'.format(versionData['pkg_name']),
        ]
    },

    include_package_data=True
)
