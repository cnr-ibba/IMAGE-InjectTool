#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Creating image database
    CREATE DATABASE image;

    -- Assigning privileges to database (public schema)
    GRANT ALL PRIVILEGES ON DATABASE image TO $IMAGE_USER;
EOSQL
