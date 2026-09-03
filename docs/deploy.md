# Deploying Langram

Two separate deployments, because ayter.com is static file hosting (Apache,
GoDaddy) and cannot run the Python API. The frontend goes to ayter.com like
every other project there. The API goes to Fly.io.

## What is already prepared

- `Dockerfile`, `.dockerignore`, `docker/release.sh` — the API image, and the
  migrate-then-seed step that runs once per deploy before traffic switches
  over. It never touches learner state; see `db/seed.py`'s own docstring.
- `fly.toml` — app config. `app = "langram-api"` is a placeholder name.
- `web/src/lib/api.ts` now reads `VITE_API_BASE` at build time and prefixes
  every request with it. Without this, a frontend built for one origin
  (ayter.com) calling a backend on another (a Fly.io URL) would have every
  request go to the wrong place, since the code previously called bare
  `/api/...` paths, which only resolves correctly when both are on the same
  origin. This was a real gap, not a hypothetical one, and it would have
  failed silently as "network error" with nothing pointing at the cause.
- `pyproject.toml` now has a `postgres` extra (`psycopg[binary]`). The code
  has assumed a `postgresql+psycopg://` URL since Phase 2 without the driver
  package ever actually being declared as a dependency.

## What needs your account

### 1. Fly.io

```
# install flyctl (one of, whichever fits this machine)
irm https://fly.io/install.ps1 | iex        # PowerShell
curl -L https://fly.io/install.sh | sh      # bash

fly auth signup    # or: fly auth login, if you already have an account
```

From the repo root:

```
fly launch --no-deploy --copy-config
```

This reads the existing `fly.toml`, asks you to confirm (or change) the app
name and region, and creates the app on your account without deploying yet.

### 2. A Postgres database

```
fly postgres create --name langram-db --region ord
fly postgres attach langram-db --app langram-api
```

`attach` sets `DATABASE_URL` as a secret automatically, but it will not be in
the `postgresql+psycopg://` form the code expects (it defaults to
`postgres://`, the psycopg2-style scheme). Set it explicitly instead:

```
fly secrets set --app langram-api \
  LANGRAM_DATABASE_URL="postgresql+psycopg://<user>:<password>@<host>:5432/<db>" \
  LANGRAM_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
```

(`fly postgres attach` prints the connection details; `fly secrets list`
confirms what is set, though not the values.) `LANGRAM_SECRET_KEY` matters:
without it a new signing key is generated per process, which logs every
learner out on every restart or deploy.

### 3. Deploy the API

```
fly deploy
```

This builds the Docker image on Fly's remote builder (nothing needs to build
locally), runs `docker/release.sh` as the release command, then starts the
app. Confirm it is alive:

```
curl https://langram-api.fly.dev/api/health
```

## Once the API has a real URL: the frontend

```
cd web
VITE_BASE=/langram/ VITE_API_BASE=https://langram-api.fly.dev npm run build
```

If this is run in Git Bash on Windows, prefix it with `MSYS_NO_PATHCONV=1`.
Confirmed the hard way: Git Bash silently rewrites a leading-slash argument
like `/langram/` into a Windows path (`/Program Files/Git/langram/`), which
builds without error and without any indication anything is wrong, and the
deployed site then 404s on every asset. `MSYS_NO_PATHCONV=1` stops the
rewrite. PowerShell and a real Linux shell do not have this problem.

`web/dist/` is the static site. Upload its contents via FTP to
`ayter_com/langram/`, the same way Rosetta or Timbre are deployed.

### The CSP gap this will hit

ayter.com's root `.htaccess` and `_headers` both send:

```
connect-src 'self' https://formspree.io
```

No Fly.io origin is in there, and a subdirectory without its own `.htaccess`
inherits the root policy. Every request from the deployed frontend to the API
would be silently blocked by the browser, the same class of bug that broke
the ambient audio feature and Forage's Anthropic calls on this same site,
both already documented in memory as recurring failure modes here. Add
`ayter_com/langram/.htaccess`, modelled on `ayter_com/semaphore/.htaccess`'s
per-directory override pattern:

```apache
<IfModule mod_headers.c>
  Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self' https://langram-api.fly.dev; frame-src 'none'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests"
</IfModule>
```

Replace `https://langram-api.fly.dev` with the real app URL if the Fly app
name ends up different. This file has not been created yet: it needs the
real API URL first, which only exists after `fly deploy` succeeds.

## After that

- Point the "Langram" entry in `ayter_com/index.html`'s projects panel at
  `/langram/` and drop the "In development" status.
- `sitemap.xml` on ayter.com could list it too, matching how other projects
  are listed there.
