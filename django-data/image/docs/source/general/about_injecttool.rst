
About InjectTool
================

Introduction
------------

Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

InjectTool composed image
-------------------------

InjectTool is a docker-compose application running Django, NGINX, PostgreSQL, redis
and Celery. The application is mainly developed in python, and structured in a
django project. Each docker container is structured in order to do specific stuff,
and they are linked through docker-composed `configuration file`_.

The container componing InjectTool are the followings:

- **nginx**: is the frontend layer to InjectTool. It runs a NGINX instance and it exposes ``26080`` port. It serves
  InjectTool application through
  the ``image`` location. It provide the static content of the site and forwards
  all the dynamic request to the ``uwsgi`` container. The configuration files are
  inside the `nginx`_ folder of InjectTool project.

- **db**: is a PostgreSQL instance in which all InjectTool data are stored. The UID
  is inside this image. All the configuration files are inside the `postgres`_
  folder, while data will be stored persistently inside the InjectTool working
  directory inside *postgres_data* folder

- **redis**: is a redis instance of InjectTool backend. It is required by Celery
  to store and retrive information for its tasks. It stores temporary data useful
  for the InjectTool application. It doesn't store anything outside its container
  environment, so all its data need to be considered as temporary

- **uwsgi**: is part of the backend layer. It manages django codes, it receives request
  from NGINX and replies with dynamic content. The configuration files are inside
  `uwsgi`_ folder of InjectTool project, while django code is stored inside and
  specifi InjectTool configuration files are stored in `django_data`_ folder

In addtion, we have three container based on *uwsgi* container which run different
celery operations:

- **celery-worker**: The first of the three containers running Celery. It relies on
  *uwsgi* container, since it share the same django code of *uwsgi*. It performs
  InjectTool time consuming task asynchronously. It consumes task stored in *redis*
  database and has access to *postgres* database in order to store data persistently.

- **celery-beat**: The second of the three containers running celery. It send
  routine tasks or tasks on regolar timning to celery-worker. This operates without
  user intervention

- **celery-flower**: is a monitoring instance of celery workers. It displays information
  regarding tasks. Its contents are rendered in HTML and reached through ``5555`` port


.. _`configuration file`: https://github.com/cnr-ibba/IMAGE-InjectTool/blob/master/docker-compose.yml
.. _`nginx`: https://github.com/cnr-ibba/IMAGE-InjectTool/tree/master/nginx
.. _`postgres`: https://github.com/cnr-ibba/IMAGE-InjectTool/tree/master/postgres
.. _`uwsgi`: https://github.com/cnr-ibba/IMAGE-InjectTool/tree/master/uwsgi
.. _`django_data`: https://github.com/cnr-ibba/IMAGE-InjectTool/tree/master/django-data
