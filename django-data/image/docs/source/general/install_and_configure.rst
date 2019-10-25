
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

Switch to BioSamples production environment
-------------------------------------------

By default InjectTool works by submitting data to BioSamples test servers. In order
to switch to the BioSamples production environment, you have to define the production
URLs in the ``.env`` file, like this::

  BIOSAMPLE_URL=https://www.ebi.ac.uk/biosamples/samples
  EBI_AAP_API_AUTH=https://api.aai.ebi.ac.uk/auth
  BIOSAMPLE_API_ROOT=https://submission.ebi.ac.uk/api/

.. note:: remember to re-create countainers since those variables are esported
   as environment variables.

.. warning:: The EBI Auth server is different from the test server. You will need
   to register your users through the new environment. The resulting group names
   will be incompatible from test to production, you have to clean up each
   biosample account data in database
