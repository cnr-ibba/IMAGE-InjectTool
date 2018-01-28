#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  -- Assign privileges on schema
  \connect imported_from_cryoweb
  GRANT USAGE ON SCHEMA apiis_admin TO cryoweb_insert_only;
  GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA apiis_admin TO cryoweb_insert_only;
  GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA apiis_admin TO cryoweb_insert_only
EOSQL
