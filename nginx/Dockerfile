
#
# VERSION 0.3
# DOCKER-VERSION  17.05.0-ce
# AUTHOR:         Paolo Cozzi <cozzi@ibba.cnr.it>
# DESCRIPTION:    A nginx container to work with django
#

# Get the last stable nginx image
FROM nginx:1.15

LABEL maintainer="Paolo Cozzi <cozzi@ibba.cnr.it>"

# synchronize timezone for container
# https://forums.docker.com/t/synchronize-timezone-from-host-to-container/39116
RUN echo "Europe/Rome" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

# Copy nginx configuration file in conf.d directory
COPY nginx.conf /etc/nginx/nginx.conf

# define NGINX volume
VOLUME /etc/nginx/conf.d/
