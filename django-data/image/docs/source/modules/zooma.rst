
Zooma App
=========

.. _zooma-app:

Zooma app deals with ontology annotations of missing terms. It relies on
:ref:`zooma.helpers` functions, which tries to annotate missing terms relying on
`zooma tools <https://www.ebi.ac.uk/spot/zooma/>`_. Only ontologies with an
high confidence are used to annotate terms, lower confidences are discarded. Zooma
annotations are performed by :ref:`zooma.tasks` after each data import and by
weekley :ref:`Routine Tasks`. Annotations can be also started by the user by clicking
on *Annotate* buttons inside :py:class:`zooma.views.OntologiesReportView`

zooma.helpers
-------------

zooma.helpers module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: zooma.helpers
   :members:
   :show-inheritance:
   :undoc-members:


zooma.tasks
-----------

zooma.tasks module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: zooma.tasks
   :members:
   :show-inheritance:
   :undoc-members:


zooma.views
-----------

zooma.views module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: zooma.views
  :members:
  :show-inheritance:
  :undoc-members:
