#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Creating image database
    CREATE DATABASE image;

    -- Creating cryoweb database
    CREATE DATABASE cryoweb TEMPLATE template_cryoweb;

    -- templating cryoweb database for cryoweb testing
    UPDATE pg_database SET datistemplate=true WHERE datname='cryoweb';
EOSQL
