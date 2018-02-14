#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  -- Assigning privileges to $IMAGE_USER
  ALTER USER $IMAGE_USER CREATEDB;

  -- Assigning privileges to database (public schema)
  GRANT ALL PRIVILEGES ON DATABASE image TO $IMAGE_USER;
  GRANT ALL PRIVILEGES ON DATABASE imported_from_cryoweb TO $IMAGE_USER;
  GRANT ALL PRIVILEGES ON DATABASE imported_from_cryoweb TO cryoweb_insert_only;

  -- Assign privileges on schema apiis_admin
  \connect imported_from_cryoweb
  GRANT ALL PRIVILEGES ON SCHEMA apiis_admin TO $IMAGE_USER;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA apiis_admin TO $IMAGE_USER;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA apiis_admin TO $IMAGE_USER;

  GRANT USAGE ON SCHEMA apiis_admin TO cryoweb_insert_only;
  GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA apiis_admin TO cryoweb_insert_only;
  GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA apiis_admin TO cryoweb_insert_only
EOSQL
