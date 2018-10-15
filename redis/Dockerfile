#
# VERSION 0.1
# DOCKER-VERSION  17.05.0-ce
# AUTHOR:         Paolo Cozzi <cozzi@ibba.cnr.it>
# DESCRIPTION:    A redis container
#

# get the latest redis image
FROM redis:alpine

MAINTAINER Paolo Cozzi <cozzi@ibba.cnr.it>

# synchronize timezone for container
# https://serverfault.com/a/683651
RUN apk add --no-cache tzdata
ENV TZ Europe/Rome

# commands and ports are the same of the base redis image
