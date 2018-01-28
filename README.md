
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
IMAGE_USER=***REMOVED***
IMAGE_PASSWORD=<user password>
CRYOWEB_INSERT_ONLY_PW=<user_password>
```

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

Create the settings.py file
---------------------------

Django configuration file (settings.py) must be created by copying the
settings.py_SAMPLE file in its own directory. After having created it,
open it and write the password for the django-postgres connection. With this procedure, no password is stored into git history:

```bash
$ cd django-data/image/image
$ cp settings.py_SAMPLE settings.py

# open settings.py and replace **REMOVED** with the password
# at the line
# 'PASSWORD': '**REMOVED**',
# you should find the password in the Trello Board.

```

> TODO:
settings.py will be defined using [python decouple](https://simpleisbetterthancomplex.com/2015/11/26/package-of-the-week-python-decouple.html)
reading values from `.env` file.

Start the Docker-compose suite
------------------------------

There are three containers defined in docker-compose.yml

 - uwsgi: the code base
 - nginx: web interface
 - db: the postgres database

```bash

# start the containers according to the docker-compose.yml specifications
# docker will download and install all required dependences; it will need several minutes to complete.
# launch this command from the working directory
$ docker-compose up -d

```

InjectTool Use
--------------

The Inject Tool interface is available for a local access through Internet browser at the URL: `http://localhost:28080/image/`.

Pages are served by an nginx docker container controlled by Docker Compose (see the docker-compose.yml file content). In order to start the service:

```bash
# cd <working directory>
$ docker-compose up -d
```

After inizialization, a new django user with administrative privilges is needed. This is
not the default postgres user, but a user valid only in django environment. Moreover
the django tables need to be defined:

```
$ docker-compose run --rm uwsgi python manage.py check
$ docker-compose run --rm uwsgi python manage.py makemigrations
$ docker-compose run --rm uwsgi python manage.py migrate
$ docker-compose run --rm uwsgi python manage.py createsuperuser
```

The last commands will prompt for a user creation. Track user credentials since
those will be not stored in `.env` file of `IMAGE-InjectTool` directory.

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

### Useful commands

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

# connect to the postgres database as administrator
$ docker-compose run --rm db psql -h db -U postgres
```

### Exporting cryoweb data

At this point cryoweb tables are already defined for import, so we need to export
only data from an existing cryoweb instance. Execute a dump from a cryoweb like this:

```
$ pg_dump -U <user> -h <host> --column-inserts --data-only --schema apiis_admin --column-inserts <cryoweb_database> > cryoweb_data_only.sql
```
