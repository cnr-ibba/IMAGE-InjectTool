
InjectTool Databases
====================

Cryoweb helper database
-----------------------

The cryoweb database is modeled started from an empty cryoweb instance. It models
the minimal permission and table definitions in order to make possible to upload
cryoweb data from a postrges *data only* dump file. This database is filled by
:ref:`cryoweb <cryoweb-app>` module, using :py:meth:`cryoweb.tasks.import_from_cryoweb`.
After import is done (with success or not), database is cleaned and restored to
the original state.

The Unified Internal Database
-----------------------------

.. image:: ../_static/relationships.real.compact.png

The Redis Database
------------------

This database acts as a temporary space required to :py:class:`celery.app.task.Task`.
and its derived classes defined in InjectTool modules *tasks.py* packages. It
stores also the user generated token after a user start a submission using
:py:class:`biosample.views.SubmitView`
