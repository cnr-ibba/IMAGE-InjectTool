#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Creating cryoweb roles for a dump import
    CREATE ROLE apiis_admin WITH SUPERUSER CREATEDB CREATEROLE ;

    -- Creating a insert only user
    CREATE USER cryoweb_insert_only PASSWORD '$CRYOWEB_INSERT_ONLY_PW';

    -- Creating image user
    CREATE USER $IMAGE_USER PASSWORD '$IMAGE_PASSWORD';
EOSQL
