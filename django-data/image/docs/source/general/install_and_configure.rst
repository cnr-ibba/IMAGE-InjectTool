
Installing InjectTool
=====================

Installing docker and docker compose
------------------------------------

InjectTool is developed inside a docker-compose instance. You need to install
both docker and docker compose in order to run InjectTool.
Please follow your platform documentation to `install docker`_.

.. note:: if you want to interact with docker using your user and not root, you need
   to do the following (only applies to Linux machines)::

    $ sudo groupadd docker
    $ sudo usermod -aG docker <your user>
    # login again

Docker compose is a tool for defining and running multi-container Docker applications.
Please follow your platform documentation to install `docker-compose`_.

.. _`install docker`: https://docs.docker.com/engine/installation/
.. _`docker-compose`: https://docs.docker.com/compose/install/

Donwload and install InjectTool
-------------------------------

A detailed description on how to install InjectTool is described in
`github README <https://github.com/cnr-ibba/IMAGE-InjectTool/blob/master/README.md>`_
