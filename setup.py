import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-popupcrud',
    version='0.1',
    description='A CRUD framework that uses HTML popups for CRUD operations.',
    long_description=README,
    license='MIT License',  # example license
    packages=[
        'popupcrud'
    ],
    include_package_data=True,
    install_requires=[
        'django-bootstrap3',
        'django-pure-pagination',
    ],
    url='https://www.smallpearl.com/',
    author='Hari Mahadevan',
    author_email='hari@smallpearl.com',
    keywords='django-popupcrud',
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
