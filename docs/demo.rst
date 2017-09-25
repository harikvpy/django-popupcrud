Demo Project
------------

The demo project in folder ``demo`` shows four usage scenarios of 
``PopupCrudViewSet``. To run the demo, issue the following commands from 
``demo`` folder::

    ./manage migrate
    ./manage runserver

Homepage has links to the various views in the project that demonstrates 
different use cases. Each link has a brief description on the type of use case
it demonstrates.

One of the forms in the demo ``MultipleRelatedObjectForm``, shows how the 
advanced ``Select2`` can be used instead of the django's native `'Select`` 
widget. For this to work, you need to install ``django-select2`` in the virtual 
environment where ``demo`` is run.

