#!/bin/sh
set -eu

# Les volumes nommés sont créés root:root par Docker.
# On prépare les répertoires puis on abandonne les privilèges.
mkdir -p /app/data/warehouse /app/site
chown -R app:app /app/data /app/site

exec setpriv --reuid=1000 --regid=1000 --init-groups "$@"
