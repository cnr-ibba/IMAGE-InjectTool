#
# VERSION 0.1
# DOCKER-VERSION  17.05.0-ce
# AUTHOR:         Paolo Cozzi <cozzi@ibba.cnr.it>
# DESCRIPTION:    A postgres container
#

# get the latest postgres server
FROM postgres:9.6

MAINTAINER Paolo Cozzi <cozzi@ibba.cnr.it>

# synchronize timezone for container
# https://forums.docker.com/t/synchronize-timezone-from-host-to-container/39116
RUN echo "Europe/Rome" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

# commands and ports are the same of the base postgres image
