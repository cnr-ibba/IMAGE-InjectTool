Image_app App
=============

.. _image_app-app:

All stuff related with image :ref:`The Unified Internal Database` and site pages like index and about
are defined in this module.

image_app.models
----------------

Submission and user data
^^^^^^^^^^^^^^^^^^^^^^^^

Inside model library, you can manage :ref:`The Unified Internal Database` objects.
The main object is :py:class:`image_app.models.Submission` which is the object that
a registered user create when starts creating a new submission. Animals and Samples
data loaded by user are manged by the :py:class:`image_app.models.Animal` and
:py:class:`image_app.models.Sample` class. The original name of such objects (defined
as ``Data source id`` from the IMAGE-metadata rules) is managed by :py:class:`image_app.models.Name`
class, which track also the ``biosample_id`` of such objects and its :ref:`Common statuses`.
Here are presented the relations between ``Names`` objects:

.. image:: ../_static/image_app_name.1degree.png

Throgh name relationship, you could rerieve all animal belonging to a submission,
for example::

  from image_app.models import Submission, Animal

  submission = Submission.objects.get(pk=1)
  animals = Animal.objects.filter(name__submission=submission)

in this example ``animals`` is a :py:class:`django.db.models.query.QuerySet` instance
with all animals defined in selected submission.

image_app.models module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: image_app.models
   :members:
   :show-inheritance:
