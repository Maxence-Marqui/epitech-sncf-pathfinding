#!/bin/bash

# Wait until Postgres is ready.


while ! pg_isready  -q --host=$DB_HOST --port=$DB_PORT -U $DB_USER; do
  echo "$(date) - waiting for database to start"
  sleep 2
done

python3 main.py -d
#flask