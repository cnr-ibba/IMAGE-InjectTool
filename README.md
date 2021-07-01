
InjectTool installation
=======================

[![docker-compose-workflow](https://github.com/cnr-ibba/IMAGE-InjectTool/actions/workflows/docker-compose-workflow.yml/badge.svg)](https://github.com/cnr-ibba/IMAGE-InjectTool/actions/workflows/docker-compose-workflow.yml)
[![Coverage Status](https://coveralls.io/repos/github/cnr-ibba/IMAGE-InjectTool/badge.svg?branch=master)](https://coveralls.io/github/cnr-ibba/IMAGE-InjectTool?branch=master)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/cnr-ibba/IMAGE-InjectTool/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/cnr-ibba/IMAGE-InjectTool/?branch=master)
[![Documentation Status](https://readthedocs.org/projects/image-injecttool/badge/?version=latest)](https://image-injecttool.readthedocs.io/en/latest/?badge=latest)

Install Docker CE
-----------------

Please follow your platform documentation:
[https://docs.docker.com/engine/installation/](https://docs.docker.com/engine/installation/)

>NOTE: if you want to interact with docker using your user and not root, you need to
do the following (only applies to Linux machines):

```
$ sudo groupadd docker
$ sudo usermod -aG docker <your user>
# login again
```

Install Docker-compose
----------------------

Compose is a tool for defining and running multi-container Docker applications.
Please follow your platform documentation:
[https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)


Install the Inject-Tool code from GitHub
-----------------------------------------

The GitHub Inject-Tool repository is available at
[https://github.com/cnr-ibba/IMAGE-InjectTool.git](https://github.com/cnr-ibba/IMAGE-InjectTool.git)
Clone it with:

```
$ git clone --recursive https://github.com/cnr-ibba/IMAGE-InjectTool.git
```

The directory created by the cloning contains the following content (can be slightly different):

```
IMAGE-InjectTool/
├── django-data
├── docker-compose.yml
├── nginx
├── postgres
├── README.md
├── TODO.md
└── uwsgi
```

The `IMAGE-InjectTool` directory will be referred as the "working directory" in this document.

### Install git LFS

In order to contribute to this repository, you have to install `git-lfs`. Download
the [package required for your OS](https://git-lfs.github.com/) and install it.
Then inside `IMAGE-InjectTool` working directory install the github hooks with:

```
$ git lfs install
```

This is required once for repository. Please refer to [git lfs](https://git-lfs.github.com/) documentation
for more info.

Setting the `.env` file
-----------------------

`docker-compose` can read variables from a `.env` placed in the working directory.
Here we will define all variables useful for our containers, like database password.
Edit a new `.env` file in working directory and set passwords for such environment
variables:

```
POSTGRES_PASSWORD=<postgres password>
IMAGE_USER=<image_user>
IMAGE_PASSWORD=<user password>
CRYOWEB_INSERT_ONLY_PW=<user_password>
```

> *TODO*: manage sensitive data using secret in docker-compose, as described
[here](https://docs.docker.com/engine/swarm/secrets/#use-secrets-in-compose) and
[here](https://docs.docker.com/compose/compose-file/#secrets)

Preparing the database
----------------------

All information needed to instantiate database (like roles, password, user) are
defined in `postgres` directory. Database will be generated and then all the scripts
placed in `postgres` directory are executed. Ensure that `postgres-data` is not present,
if not this part of the configuration will not be executed.

> NOTE:
the entire system (three containers managed by Docker Compose) uses two shared
[volumes](https://docs.docker.com/engine/admin/volumes/volumes/) for ensuring
the existance of persistent data: on the host the two directories are named
`postgres-data/` and `django-data/`. The django-data directory, containing the
entire django environment and codes, is tracked in git while `postgres-data` not.
When instantiated for the first time, `postgres-data` is generated and the database
is initialized. After that, every instance of postgres will use the `postgres-data`
directory, mantaing already generate data. If you plan to move `IMAGE-InjectTool`,
you have to move all `IMAGE-InjectTool` directory with all its content

Build the docker-compose suite
------------------------------

There are seven containers defined in `docker-compose.yml`

 - uwsgi: the code base
 - nginx: web interface
 - db: the postgres database
 - redis: the redis database
 - asgi: the webesocket server based on uwsgi image
 - celery-worker: a celery worker image based on uwsgi image
 - celery-beat: a celery beat image based on uwsgi image

There's also `docker-compose-devel.yml` which contains the previously described
container plus the following

 - celery-flower: a celery monitoring imaged based on uwsgi image

This file could be used in development to understand tasks execution. To enable such
container, simply specify the `docker-compose-devel.yml` with the `-f` option, immediately
after `docker-compose`, for example:

```bash
$ docker-compose -f docker-compose-devel.yml up -d
```

And specify the same option everytime you need to call `docker-compose`


```bash
# build the images according to the docker-compose.yml specificatios. Docker will
# download and install all required dependences; it will need several minutes to complete.
# launch this command from the working directory
$ docker-compose build
```

InjectTool Use
--------------

### Django configuration

Django configuration relies on a `settings.py` module, which loads sensitive data
like password and `SECRET_KEY` from the same `.env` file in the project directory
through the [python decouple](https://simpleisbetterthancomplex.com/2015/11/26/package-of-the-week-python-decouple.html)
module. You need to define new environment variables for `uwsgi` container:

You need to define a new django `SECRET_KEY`. Start a python terminal with docker:

```
$ docker-compose run --rm --no-deps uwsgi python
```

then execute this python code, as described [here](https://stackoverflow.com/a/16630719):

```python
>>> from django.utils.crypto import get_random_string
>>> chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
>>> get_random_string(50, chars)
```

Copy the resulting key and the add into the previous  `.env` file like this:

```
SECRET_KEY=<your SECRET_KEY>
DEBUG=False
USI_MANAGER=imagemanager
USI_MANAGER_PASSWORD=<usi_manager_password>
```

You can set email activation backend parameters in the same file:

```
EMAIL_BACKEND=djcelery_email.backends.CeleryEmailBackend
CELERY_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL = <from email>
EMAIL_HOST = <your smtp host>
EMAIL_HOST_USER = <your email host user>
EMAIL_HOST_PASSWORD = <your email host password>
EMAIL_USE_TLS = <True if TLS if required. False otherwise>
EMAIL_PORT = <your smtp port>
```

> NOTE: Your email provider (ie Gmail) could untrust email sent from an unkwnown
address, you need to log in and authorize email sent from a new address

You can also set the EBI endpoints for submitting data to BioSamples. Please
refer to the correct API endpoints to submit data into BioSamples production
servers:

```
BIOSAMPLE_URL=https://wwwdev.ebi.ac.uk/biosamples/samples
EBI_AAP_API_AUTH=https://explore.api.aai.ebi.ac.uk
BIOSAMPLE_API_ROOT=https://submission-test.ebi.ac.uk
```

The Inject Tool interface is available for a local access through Internet browser at the URL:
`http://localhost:26080/`.

### Fixing django permissions

You will also to check file permissions in django data, expecially for `media`
folder:

```
$ docker-compose run --rm uwsgi sh -c 'mkdir -p /var/uwsgi/image/media'
$ docker-compose run --rm uwsgi sh -c 'mkdir -p /var/uwsgi/image/protected/data_source/'
$ docker-compose run --rm uwsgi sh -c 'chmod -R g+rwx media && chmod -R g+rwx protected'
$ docker-compose run --rm uwsgi sh -c 'chgrp -R www-data .'
```

### check that everything works as expected

Test  your fresh InjectTool installation with:

```
$ docker-compose run --rm uwsgi pytest
```

### Initialize Django tables

After inizialization, a new django user with administrative privilges is needed. This is
not the default postgres user, but a user valid only in django environment. Moreover
the django tables need to be defined:

```
$ docker-compose run --rm uwsgi python manage.py check
$ docker-compose run --rm uwsgi python manage.py migrate
$ docker-compose run --rm uwsgi python manage.py makemigrations
$ docker-compose run --rm uwsgi python manage.py migrate
$ docker-compose run --rm uwsgi python manage.py createsuperuser
```

The last commands will prompt for a user creation. This will be a new django
admin user, not the database users described in `env` files. Track user credentials
since those will be not stored in `.env` file of `IMAGE-InjectTool` directory.

Next, you need to initialize the InjectTool database by filling up default accessory
tables. You can do it by launching the following command:

```
$ docker-compose run --rm uwsgi python manage.py initializedb
```

### Start composed image

Pages are served by an nginx docker container controlled by Docker Compose
(see the docker-compose.yml file content). In order to start the service:

```bash
# cd <project directory>
$ docker-compose up -d
```

### Other useful commands

```bash
# start the containers according to the docker-compose.yml specifications
$ docker-compose up -d

# start the containers according to the docker-compose-devel.yml specifications
# (with celery-flower container enabled)
$ docker-compose -f docker-compose-devel.yml up -d

# see running processes, like unix ps command
$ docker-compose ps

# restart containers, e.g., useful for web service after having
# updated the web interface
$ docker-compose restart

# stop all
$ docker-compose stop

# stop containers and cleanup
$ docker-compose down

# run a command (e.g., python manage.py check) in the python container from the host
$ docker-compose run --rm uwsgi python manage.py check

# makemigrations to all application or to specific application
$ docker-compose run --rm uwsgi python manage.py makemigrations
$ docker-compose run --rm uwsgi python manage.py makemigrations image_app

# inspect a particoular migrations
$ docker-compose run --rm uwsgi python manage.py sqlmigrate image_app 0005

# apply migrations to database (all migrations made with makemigrations)
$ docker-compose run --rm uwsgi python manage.py migrate

# remove old contenttypes (tables which were deleted)
$ docker-compose run --rm uwsgi python manage.py remove_stale_contenttypes

# connect to the postgres database as administrator
$ docker-compose run --rm db psql -h db -U postgres

# make a dump of image database
$ docker-compose run --rm db pg_dump -h db -U postgres image | gzip --best > image_dump.sql.gz

# restore an image database
$ docker-compose run --volume $PWD/:/tmp/ --rm db bash -c 'exec zcat /tmp/image_dump.sql.gz | psql -h db -U postgres image'

# executing Unittest. Pytest ensure is the recommended way (since has mock objects)
$ docker-compose run --rm uwsgi pytest
$ docker-compose run --rm uwsgi pytest image_app/tests/
$ docker-compose run --rm uwsgi pytest image_app/tests/test_views.py
$ docker-compose run --rm uwsgi pytest --verbosity=2 image_app/tests/test_views.py::DashBoardViewTest::test_redirection

# calculating coverage
$ docker-compose run --rm uwsgi coverage run --source='.' -m py.test

# generate coverage report
$ docker-compose run --rm uwsgi coverage report
$ docker-compose run --rm uwsgi coverage html

# scaling up celery worker to two instances:
$ docker-compose scale celery-worker=2

# restart celery workers and reload tasks:
$ docker-compose restart celery-worker

# check sphinx documentation
$ docker-compose run --rm uwsgi bash -c "cd docs; make linkcheck"

# create sphinx html documentation
$ docker-compose run --rm uwsgi bash -c "cd docs; make html"

# cleanup sphinx html documentation
$ docker-compose run --rm uwsgi bash -c "cd docs; make clean"
```

Exporting data from cryoweb
---------------------------

At this point cryoweb tables are already defined for import, so we need to export
only data from an existing cryoweb instance. Execute a dump from a cryoweb like this:

```
$ pg_dump -U <user> -h <host> --column-inserts --data-only --schema apiis_admin <cryoweb_database> > cryoweb_data_only.sql
```

Biosamples submission
---------------------

Generate a biosamples `json` file:

```
$ docker-compose run --rm uwsgi python manage.py get_json_for_biosample --submission 1 --outfile italian_submission_example.json
```
