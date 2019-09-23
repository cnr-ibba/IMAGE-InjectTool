
Biosample App
=============

.. _biosample-app:

biosample.helpers
-----------------

biosample.helpers module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: biosample.helpers
   :members:
   :show-inheritance:
   :undoc-members:

biosample.models
----------------

biosample.models module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: biosample.models
   :members:
   :show-inheritance:
   :undoc-members:


biosample.tasks
---------------

Biosample tasks are splitted in two main modules, ``retrieval`` and ``submission``
and classes are defined in modules accordingly if they are used for submission or
for retrieval of biosample data. Biosample submission is accomplished in parallel: after starting
a submission with :py:class:`SubmitView <biosample.views.SubmitView>` a
:py:class:`SplitSubmissionTask <biosample.tasks.submission.SplitSubmissionTask>`
is called in order to split submission data in batches as described in
:py:class:`biosample.models.Submission`. Then it will start a
:py:class:`SubmitTask <biosample.tasks.submission.SubmitTask>` in order to submit
a single batch of data in a new process, able to create a new
`USI submission <https://submission-test.ebi.ac.uk/api/docs/guide_getting_started.html#_creating_a_submission>`_. Finally a
:py:class:`SubmissionCompleteTask <biosample.tasks.submission.SubmissionCompleteTask>`
is called after each :py:class:`SubmitTask <biosample.tasks.submission.SubmitTask>`
using a :py:class:`celery.chord`, which is a special type of task that is executed
after only after other task. This task in particoular marks the submission process
as completed in order to be controlled by :py:class:`FetchStatusTask <biosample.tasks.retrieval.FetchStatusTask>`,
which if the task able to get statuses and retrieve biosample ids.
The retrieval process is performed regularly every 15 minutes by the
:py:class:`FetchStatusTask <biosample.tasks.retrieval.FetchStatusTask>` task.
If the biosample submission is successful, this task will retrieve the **biosample_id**
back to InjectTool database. Otherwise it will mark objects with **NEED_REVISION**
status. After each submission batches is retrieved with success, the whole submission
process is completed by the :py:class:`RetrievalCompleteTask <biosample.tasks.retrieval.RetrievalCompleteTask>`,
which is called after each batch object for a submission has been requested.

biosample.tasks module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: biosample.tasks.retrieval
   :members:
   :show-inheritance:
   :undoc-members:

.. automodule:: biosample.tasks.submission
  :members:
  :show-inheritance:
  :undoc-members:


biosample.views
---------------

biosample.views module contents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: biosample.views
   :members:
   :show-inheritance:
   :undoc-members:
