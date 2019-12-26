import os
from setuptools import find_packages, setup

import popupcrud
version = popupcrud.__version__

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

with open(os.path.join(os.path.dirname(__file__), 'HISTORY.rst')) as history:
    HISTORY = history.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-popupcrud',
    version=version,
    description='A CRUD framework that uses HTML popups for CRUD operations.',
    long_description=README + '\n\n' + HISTORY,
    long_description_content_type="text/x-rst",
    license='BSD 3-Clause License',
    packages=[
        'popupcrud'
    ],
    include_package_data=True,
    install_requires=[
        'django-bootstrap3',
        'django-pure-pagination',
    ],
    url='https://github.com/harikvpy/django-popupcrud',
    author='Hari Mahadevan',
    author_email='hari@smallpearl.com',
    keywords='django-popupcrud',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
