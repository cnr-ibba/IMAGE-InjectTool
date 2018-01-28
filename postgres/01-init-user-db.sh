#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Creating cryoweb roles for a dump import
    CREATE DATABASE imported_from_cryoweb WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.utf8' LC_CTYPE = 'en_US.utf8';
    CREATE ROLE apiis_admin WITH SUPERUSER CREATEDB CREATEROLE ;
    CREATE USER cryoweb_insert_only PASSWORD '$CRYOWEB_INSERT_ONLY_PW';

    -- Creating image database and user
    CREATE USER $IMAGE_USER PASSWORD '$IMAGE_PASSWORD';
    CREATE DATABASE image;

    -- Assigning privileges to database
    GRANT ALL PRIVILEGES ON DATABASE image TO $IMAGE_USER;
    GRANT ALL PRIVILEGES ON DATABASE imported_from_cryoweb TO cryoweb_insert_only;
EOSQL
