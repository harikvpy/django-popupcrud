========
Settings
========

django-popupcrud global settings are specified as the dict variable 
``POPUPCRUD`` in your settings.py.

``POPUPCRUD`` currently supports the following settings with their
default values.

.. code:: django

    # Default settings
    POPUPCRUD = {

        # The base template from which popupcrud's templates will be extended.
        # This template should have a template block named 'content' where 
        # popupcrud views will place their rendered content.
        'base_template': 'base.html',
    }

