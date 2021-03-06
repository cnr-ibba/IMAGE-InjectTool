
Django apps and modules
=======================

Django apps
-----------

- :ref:`accounts <accounts-app>`: Implement the site registration with the update/create user stuff.
  it relies on ``django-registration-redux`` 3rd party app and the default :py:mod:`django.contrib.auth`
  module.
- :ref:`animals <animals-app>`: Implement all stuff to visualize and manage Animals (organim objects)
- :ref:`biosample <biosample-app>`: implement stuff regarding `EBI AAP`_ registration
  (2nd step InjectTool registration) and biosample submission and retrieval. The
  biosample submission process in described in :ref:`biosample.tasks`
- :ref:`common <common-app>`: modules and functions that could be imported from
  other django applications
- :ref:`crbanim <crbanim-app>`: implement stuff regarding CRBanim data import into :ref:`The Unified Internal Database`
- :ref:`cryoweb <cryoweb-app>`: implement stuff regarding Cryoweb data import into :ref:`The Unified Internal Database`
- :ref:`excel <excel-app>`: implement stuff regarding Template data import into :ref:`The Unified Internal Database`
- **image**: django configuration files
- :ref:`language <language-app>`: implement stuff related to language module implementation and to
  resolve common names (ie Cow) into more scientific names (ie Bos taurus)
- :ref:`samples <samples-app>`: Implement all stuff to visualize and manage Samples (specimens from organim)
- :ref:`submissions <submissions-app>`: Implement all stuff regarding submission (uploading
  user data, starting task as validation and submission, call Sample and Animal views)
- **submission_ws**: stuff required to deal with real time messages
- :ref:`uid <uid-app>`: implement stuff related to :ref:`The Unified Internal Database` and
  views like index, dashboard, about, ...
- :ref:`validation <validation-app>`: Perform validation stuff by calling `IMAGE-ValidationTool`_
- :ref:`zooma <zooma-app>`: Annotate dictionary tables in order to provide ontology informations
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
- **mixins**: contain mixins useful and imported by other modules
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
.. _`EBI AAP`: https://explore.aai.ebi.ac.uk/home
