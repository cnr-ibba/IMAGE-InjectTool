.. IMAGE-InjectTool documentation master file, created by
   sphinx-quickstart on Wed May  8 15:16:19 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to IMAGE-InjectTool's documentation!
============================================

InjectTool is developed to help gene bank managers to enhance, standardize, tag and submit their gene bank data to EBI BioSamples, that integrates all gene bank records from across Europe. The interface guides users throughout submission and allows standardization of data following an agreed IMAGE rule set

InjectTool is a web application mainly written with `django <https://docs.djangoproject.com/en/2.2/intro/overview/>`_,
relying on a `postgres <https://www.postgresql.org/docs/>`_ and `redis <https://redis.io/documentation>`_
databases and a `nginx <https://nginx.org/en/docs/>`_ frontend to serve static
contents. InjectTool is able to perform time consuming task on the background, like
`validating <https://github.com/cnr-ibba/IMAGE-ValidationTool>`_ user data or submitting
user data to `BioSamples <https://www.ebi.ac.uk/biosamples/>`_, using
`Celery <https://docs.celeryproject.org/en/latest/>`_.

InjectTool is available at https://inject.image2020genebank.eu/, while the repository of
source code is maintained at `GitHub <https://github.com/cnr-ibba/IMAGE-InjectTool>`_

This guide is addressed to developers/contribuitor to InjectTool or people that
want to understand how InjectTool works behind the curtains.

General Documentation
---------------------

This section provides an overview of InjectTool, discussing the main features of the
web application:

.. toctree::
   :maxdepth: 3

   general/about_injecttool
   general/install_and_configure
   general/databases
   general/apps_and_modules
   general/language_and_ontologies
   general/asynchronous_tasks
   general/send_messages_in_real_time


Module Documentation
--------------------

This is the module dedicated section. InjectTool is composed by several **django-applications**,
each one perform a specific activity like user registration or BioSamples submission.
Follow the links to understand what these applications do:


.. toctree::
   :maxdepth: 3

   modules/biosample
   modules/common
   modules/cryoweb
   modules/language
   modules/submissions
   modules/uid
   modules/validation


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
