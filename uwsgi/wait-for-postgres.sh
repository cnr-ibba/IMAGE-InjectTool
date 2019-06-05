#!/bin/sh
# wait-for-mysql.sh
# https://docs.docker.com/compose/startup-order/
# https://stackoverflow.com/q/12321469/4385116

set -e

cmd="$@"

NEXT_WAIT_TIME=0
MAX_STEPS=6

until PGPASSWORD=$PGPASSWORD psql -h db -U "postgres" -c '\q' || [ ${NEXT_WAIT_TIME} -eq ${MAX_STEPS} ]; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 5
  NEXT_WAIT_TIME=$((NEXT_WAIT_TIME+1))
done

if [ ${NEXT_WAIT_TIME} -eq ${MAX_STEPS} ]; then
  >&2 echo "Problem in waiting postgres"
  exit 1;
fi

>&2 echo "Postgres is up - executing command"
exec $cmd
