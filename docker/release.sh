#!/bin/sh
# Runs once per deploy, before traffic is switched to the new version
# (Fly's release_command, Railway's pre-deploy). Migrates the schema, then
# seeds the content tables from content/. Never touches learner state: see
# db/seed.py's docstring for why an upsert-and-prune seed is safe to run
# unattended on every single deploy, including ones that only changed code.
set -eu

echo "release: validating content"
python -m langram.validate

echo "release: running migrations"
alembic upgrade head

echo "release: seeding content"
python -m langram.db.seed --database-url "$LANGRAM_DATABASE_URL"

echo "release: done"
