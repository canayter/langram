# The API only. The frontend is a static build served from ayter.com
# directly, not from this container; see docs/deploy.md.
FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg[binary] wheels and a healthcheck curl.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic
COPY content ./content
COPY schemas ./schemas
COPY docs ./docs

RUN pip install --no-cache-dir -e ".[db,api,content,postgres]"

# Runs once per deploy: bring the schema up to date, then load content/ into
# the content tables. Learner state is never touched by either step; see
# db/seed.py's own docstring for why that split is safe to run unattended.
COPY docker/release.sh /app/release.sh
RUN chmod +x /app/release.sh

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "langram.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
