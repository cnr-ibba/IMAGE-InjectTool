Common App
==========

.. _common-app:

common.constants
----------------

Here are defined values used in other modules. Those values are
used in enum database fields, in particular with django menus in forms. A lot of
class defined here are derived from the :py:class:`enum.Enum` class and :py:class:`common.constants.EnumMixin`,
which let to get a enum number value from an Enum object, as described in chapter
``6.4.8`` of `Two scoops of django`_::

  from common.constants import STATUSES

  WAITING = STATUSES.get_value("waiting")

``WAITING`` in this example is the numerical representation of ``waiting`` status
in the :ref:`The Unified Internal Database`

Common statuses
^^^^^^^^^^^^^^^

Statuses are applied for a :py:class:`image_app.models.Submission` and :py:class:`image_app.models.Name`
objects, and reflects the entiere submission status and the Object (Animal/Sample) statuses
rispectively. Here are the main statuses:

- **waiting**: means a processing phase where no user access is intended to data. While
  in this status data are checked, submitted or loaded and no update/deletion should
  occur in this stage. Model and views should have their methods to prevent user access
  during this phase.
- **loaded**: means that data were correctly loaded insided :ref:`The Unified Internal Database`.
  data could be modified but need to be validated before submission
- **error**: error is a status that should never be seen. It mean an issue in InjectTool
  itself or an error in data import. Entries in such status need to be verified
- **ready**: this status means that the validation is successful, and data could be
  submitted to biosample.
- **need_revision**: this status mean an issue in validation, or an error in biosample
  submission. Data need changes in order to be correctly subitted to biosample.
- **submitted**: this status mean that data were submitted to biosample and the system
  is waiting for ``USI`` response in order to collect ``biosample_ids`` and complete
  the submission.
- **completed**: this status means that data were correctly submitted to biosample and
  that they received a ``biosample_id``. After such status, you need to refer to
  ``biosample_id`` to update or change such data.

Status could change as described by this figure:

.. image:: ../_static/submission_statuses.png

Common confidences
^^^^^^^^^^^^^^^^^^

This :py:class:`enum.Enum` class models annotation confidence in dictionary tables
after annotation with ``zooma``. Even if all annotation statuses are possible, there
are three mainly chosen statuses:

- **curated**: means that this ontology term is annotated manually
- **good** and **high**: those are annotation accuracies as provided by ``zooma``


common.constants module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: common.constants
   :members:
   :show-inheritance:
   :undoc-members:


common.views
------------

.. automodule:: common.views
   :members:
   :show-inheritance:
   :undoc-members:

.. _`Two scoops of django`: https://www.twoscoopspress.com/products/two-scoops-of-django-1-11
