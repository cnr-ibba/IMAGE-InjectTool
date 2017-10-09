
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



**Download the Postgres database**

Postgres data are not tracked in git. Simply download the postgres-data directory from the PTP FTP site. The instruction are on the Trello Image Board.

Once downloaded the tar-gz archive, open it and save the postgres-data directory in your working directory. Please do not change file's ownerships: many directories, for example, need to be owned by the docker group.

> NOTE:
the entire system (three contained managed by Compose) has got two shared volumes [https://docs.docker.com/engine/admin/volumes/volumes/](https://docs.docker.com/engine/admin/volumes/volumes/), for persistent data (you can disrupt and recreate the containers and the database will survive them): postgres-data and django-data. Django-data, containing the entire django working directory, is tracked in git and so it does not need to be downloaded from the FTP site.



### InjectTool Use

---

**Start the Docker-compose suite**

```bash
$ docker-compose up -d
```



**Useful commands**

```bash
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
