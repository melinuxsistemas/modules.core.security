=====
Otma Core
=====

Module for base security in company projects django.
Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "otma_authentication" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'otma.apps.core.security',
    ]

2. Include the polls URLconf in your project urls.py like this::

    path('core/', include('otma.apps.core.security.urls')),

3. Run `python manage.py migrate` to create the authentications models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to verify core models (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/ to participate in the poll.