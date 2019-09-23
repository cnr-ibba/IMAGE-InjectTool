Send messages in real-time
==========================

Introduction to real time messaging
-----------------------------------

Channels is a project that takes Django and extends its abilities beyond HTTP - to handle WebSockets, chat protocols, IoT protocols, and more. It’s built on a Python specification called ASGI.
It does this by taking the core of Django and layering a fully asynchronous layer underneath, running Django itself in a synchronous mode but handling connections and sockets asynchronously, and giving you the choice to write in either style.


Sending messages in real-time using websocket protocol
------------------------------------------------------

Currently we use django-channels to send "Status" messages in real-time during data import, validation and submission.
Also we send messages to show notifications at the top of the "submission details" page during import, validation and submission phases.
Two functions are mainly used to send messages in real time and get info on
submission status: :py:meth:`send_message <submissions.helpers.send_message>` and
:py:meth:`construct_validation_message <validation.helpers.construct_validation_message>`:
the second function will returns a dictionary reporting how many samples we
have and hom many with problems; The first one will be responsible to send an
asynchronous message and update submisison detail page accordingly::

  from common.constants import WAITING
  from submissions.helpers import send_message
  from validation.helpers import construct_validation_message
  from image_app.models import Submission

  # Get a submission and update its status
  submission = Submission.objects.get(pk=1)
  submission.status = WAITING
  submission.save()

  # construct the validation message to show in submission detail:
  message = construct_validation_message(submission)

  # send message to submission (submission detail will change aaconrdingly):
  send_message(submission, message)

Asgi image
__________

We run django channels in separate docker container (created from asgi image). All required code is stored in `submissions_ws`_ folder.
It has "routing" module to decide which consumer to use and "consumer" module that does all the required job.

.. _`submissions_ws`: https://github.com/cnr-ibba/IMAGE-InjectTool/tree/master/django-data/image/submissions_ws
