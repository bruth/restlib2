from setuptools import setup, find_packages

version = __import__('restlib2').get_version()

kwargs = {
    'name': 'restlib2',
    'version': version,
    'packages': find_packages(),
    'author': 'Byron Ruth',
    'author_email': 'b@devel.io',
    'description': 'Django REST API',
    'license': 'BSD',
    'keywords': 'REST Django HTTP HATEOAS',
    'url': 'https://github.com/bruth/restlib2',

    'install_requires': [
        'django>=1.4',
        'django-preserialize',
    ],

    'test_suite': 'test_suite',

    'classifiers': [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
}

setup(**kwargs)
