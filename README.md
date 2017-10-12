
### InjectTool installation

---

**Install Docker CE**

Please follow your platform documentation:
[https://docs.docker.com/engine/installation/](https://docs.docker.com/engine/installation/)

>NOTE: if you want to interact with docker using your user and not root, you need to do the following:
```bash
$ sudo groupadd docker
$ sudo usermod -aG docker <your user>
# login again
```


**Install Docker-compose**

Compose is a tool for defining and running multi-container Docker applications.

Please follow your platform documentation:
[https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)


**Download the Inject-Tool code from GitHub**

The GitHub Inject-Tool repository is available at
[https://github.com/bioinformatics-ptp/IMAGE-InjectTool](https://github.com/bioinformatics-ptp/IMAGE-InjectTool)
The directory created by the cloning contains the following content (can be slightly different):
```bash
image/
├── django-data
├── docker-compose.yml
├── nginx
├── postgres-data
├── README.md
└── uwsgi
```
It will be referred to as the "working directory" in this file.

**Download the Postgres database**

Postgres data are not tracked in git. Simply download the postgres-data directory from the PTP FTP site. The instruction are on the Trello Image Board.

Once downloaded the tar-gz archive, open it and save the postgres-data directory in your working directory as administrator user; please do not change file's ownerships: many directories, for example, need to be owned by the docker group.

> NOTE:
the entire system (three containers managed by Docker Compose) uses two shared volumes [https://docs.docker.com/engine/admin/volumes/volumes/](https://docs.docker.com/engine/admin/volumes/volumes/) for ensuring the existance of persistent data: on the host the two directories are named postgres-data/ and django-data/. The django-data directory, containing the entire django environment and codes, is tracked in git and so it does not need to be downloaded from the FTP site.


**Start the Docker-compose suite**

```bash

# start the containers according to the docker-compose.yml specifications
# docker will download and install all required dependences; it will need several minutes to complete.
# launch this command from the working directory
$ docker-compose up -d

```

**Create the settings.py file**

Django configuration file (named settings.py) must be created copying the
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


### InjectTool Use

The Inject Tool interface is available for a local access through Internet browser at the URL: `http://localhost:28080/image/`.

Pages are served by an nginx docker container controlled by Docker Compose (see the docker-compose.yml file content). In order to start the service:

```bash
# cd <working directory>
$ docker-compose up -d

```

**Useful commands**

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

```
