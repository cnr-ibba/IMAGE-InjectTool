
InjectTool installation
=======================

Install Docker CE
-----------------

Please follow your platform documentation:
[https://docs.docker.com/engine/installation/](https://docs.docker.com/engine/installation/)

>NOTE: if you want to interact with docker using your user and not root, you need to do the following (only applies to Linux machines):
```bash
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
[https://github.com/bioinformatics-ptp/IMAGE-InjectTool](https://github.com/bioinformatics-ptp/IMAGE-InjectTool)
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

Setting the `.env` file
-----------------------

`docker-compose` can read variables from a `.env` placed in the working directory.
Here we will define all variables useful for our containers, like database password.
Edit a new `.env` file in working directory and set passwords for such environment
variables:

```
PGPASSWORD=<postgres password>
IMAGE_USER=image_user
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

There are three containers defined in docker-compose.yml

 - uwsgi: the code base
 - nginx: web interface
 - db: the postgres database

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
like password and `SECRET_KEY` from an another `.env` file through
the [python decouple](https://simpleisbetterthancomplex.com/2015/11/26/package-of-the-week-python-decouple.html)
module. You need to create a new `.env` file in `image` settings directory. start
from working directory, then:

```bash
$ cd django-data/image/image
$ touch .env
```

You need to define a new django `SECRET_KEY`. Start a python terminal with docker:


```bash
$ docker-compose run --rm uwsgi python
```
then execute this python code, as described [here](https://stackoverflow.com/a/16630719):

```python
>>> from django.utils.crypto import get_random_string
>>> chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
>>> get_random_string(50, chars)
```

Copy the resulting key and then paste into a new `.env` file like this:

```
SECRET_KEY=<your SECRET_KEY>
DEBUG=False
IMAGE_USER=image_user
IMAGE_PASSWORD=<user password>
CRYOWEB_INSERT_ONLY_PW=<user_password>
```

Database passwords have to be the same of the previous `.env` file.

### Start composed image

Pages are served by an nginx docker container controlled by Docker Compose
(see the docker-compose.yml file content). In order to start the service:

```bash
# cd <working directory>
$ docker-compose up -d
```

The Inject Tool interface is available for a local access through Internet browser at the URL:
`http://localhost:26080/image/`.

### Initialize Django tables

After inizialization, a new django user with administrative privilges is needed. This is
not the default postgres user, but a user valid only in django environment. Moreover
the django tables need to be defined:

```
$ docker-compose run --rm uwsgi python manage.py check
$ docker-compose run --rm uwsgi python manage.py makemigrations
$ docker-compose run --rm uwsgi python manage.py makemigrations language
$ docker-compose run --rm uwsgi python manage.py migrate
$ docker-compose run --rm uwsgi python manage.py createsuperuser
```

The last commands will prompt for a user creation. This will be a new django
admin user, not the database users described in `env` files. Track user credentials
since those will be not stored in
`.env` file of `IMAGE-InjectTool` directory.

### Fixing django permissions

You will also to check file permissions in django data, expecially for `media`
folder:

```
$ docker-compose run --rm uwsgi sh -c 'mkdir /var/uwsgi/image/media && chmod g+rwx media && chgrp -R www-data .'
```

Next, you need to initialize the InjectTool database by filling up default accessory
tables. You can do it by launching the following command:

```
$ docker-compose run --rm uwsgi python manage.py initializedb
```

### Other useful commands

```bash
# start the containers according to the docker-compose.yml specifications
$ docker-compose up -d

# see running processes, like unix ps command
$ docker-compose ps

# restart containers, e.g., useful for web service after having
# updated the web interface
$ docker-compose restart

# stop all
$ docker-compose stop

# run a command (e.g., python manage.py check) in the python container from the host
$ docker-compose run --rm uwsgi python manage.py check

# makemigrations to all application or to specific application
$ docker-compose run --rm uwsgi python manage.py makemigrations
$ docker-compose run --rm uwsgi python manage.py makemigrations image_app

# inspect a particoular migrations
$ docker-compose run --rm uwsgi python manage.py sqlmigrate image_app 0005

# apply migrations to database (all migrations made with makemigrations)
docker-compose run --rm uwsgi python manage.py migrate

# connect to the postgres database as administrator
$ docker-compose run --rm db psql -h db -U postgres

# executing Unittest
$ docker-compose run --rm uwsgi python manage.py test image_app.tests
$ docker-compose run --rm uwsgi python manage.py test image_app.tests.test_models

# executing test with pytest
$ docker-compose run --rm uwsgi pytest

# executing test on a certain module
$ docker-compose run --rm uwsgi pytest --verbosity=2 cryoweb/tests/test_cryoweb.py

# calculating coverage
$ docker-compose run --rm uwsgi coverage run --source='.' manage.py test

# generate coverage report
$ docker-compose run --rm uwsgi coverage report
$ docker-compose run --rm uwsgi coverage html
```

Exporting data from cryoweb
---------------------------

At this point cryoweb tables are already defined for import, so we need to export
only data from an existing cryoweb instance. Execute a dump from a cryoweb like this:

```
$ pg_dump -U <user> -h <host> --column-inserts --data-only --schema apiis_admin <cryoweb_database> > cryoweb_data_only.sql
```
