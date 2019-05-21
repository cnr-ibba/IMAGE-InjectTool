
Django apps and modules
=======================

Django apps
-----------

- **accounts**: Implement the site registration with the update/create user stuff.
  it relies on ``django-registration-redux`` 3rd party app and the default :py:mod:`django.contrib.auth`
  module.
- **animals**: Implement all stuff to visualize and manage Animals (organims)
  object
- **biosample**: implement stuff regarding AAP registration (2nd step InjectTool registration)
  and biosample submission and retrieval
- :ref:`common <common-app>`: modules and functions that could be imported from
  other django applications
- **crbanim**: implement stuff regarding CRBanim data import into :ref:`The Unified Internal Database`
- **cryoweb**: implement stuff regarding Cryoweb data import into :ref:`The Unified Internal Database`
- **image**: django configuration files
- :ref:`image_app <image_app-app>`: implement stuff related to :ref:`The Unified Internal Database` and
  views like index, dashboard, about, ...
- **language**: implement stuff related to language module implementation and to
  resolve common names (ie Cow) into more scientific names (ie Bos taurus)
- **samples**: Implement all stuff to visualize and manage Samples (specimen from organim)
- :ref:`submissions <submissions-app>`
- **validation**: Perform validation stuff by calling `IMAGE-ValidationTool`_
- **zooma**: Annotate dictionary tables in order to provide ontology informations
  using `zooma`_ API.

Generic content of a django app
-------------------------------

- **admin.py**: admin module for :py:mod:`django.contrib.admin` application
- **apps.py**: configuration file for django application
- **common.py**: module with generic stuff, could be imported by other modules, used
  to lower complexity of **tests**.
- **constants**: define constants used by others modules
- **fixtures**: sample data (in JSON) for testing purposes. Structured inside folders
  with the same module name to avoid name collisions
- **forms.py**: helper module to define forms. It could ovverride fields defined in
  **models.py** by displaying certing columns or add new ones. The low level form validation
  is modeled here (field validation before writing into databases, like discarging
  uploaded file if it isn't in the expected format)
- **helpers.py**: module with generic stuff, could be imported by other modules, used
  to lower complexity of **views.py** and **models.py**.
- **__init__.py**: empty file required to the module to be imported
- **management**: collect management scripts which interact with the database, for
  example for database maintenance
- **migrations**: collects files created using ``manage.py makemigrations``
- **models.py**: define database tables and low level functions related to data, such
  as biosample conversion
- **templates**: django templates specific for the application
- **templatetags**: functions imported by django templates, could contains complex
  or repetitive task difficult to implement in django template language. Ideally
  the modify page layout
- **tasks.py**: time consuming function called in background
- **tests**: directory which tests stuff and try to cover each statement defined in
  other modules
- **urls.py**: define routes inside django application
- **views.py**: define views used to display data or forms. Can call **tasks.py**

.. _`IMAGE-ValidationTool`: https://github.com/cnr-ibba/IMAGE-ValidationTool
.. _`zooma`: https://www.ebi.ac.uk/spot/zooma/
