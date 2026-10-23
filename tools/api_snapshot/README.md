# API snapshot: does the web app see the same API?

A before/after check for backend upgrades (e.g. Django 4.2 / Graphene 2 → Django 5.2 / Graphene 3).
It sends the **30 real queries the openIMIS React web app sends** to two versions of this backend and
shows, value by value, whether the responses are identical.

| File | What it is |
|---|---|
| [`queries/`](queries/) | 30 queries copied from the web app source (`openimis/openimis-fe-<module>_js`, branch `develop`), one per screen |
| `snapshot.py` | runs every query against one checkout and writes one JSON file per query |
| `compare.py` | compares two snapshot folders, prints a summary, writes an HTML report, exits `0` (identical) or `1` |
| [`baseline/`](baseline/) | responses recorded from `main` (Django 4.2.30 / Graphene 2.1.9, commit `035df915`) on the `test_imis` sample database. **For reference only, not needed to run the tool** (see below) |
| `tests/` | unit tests for `compare.py` |

## How it works

`snapshot.py --repo <checkout> --out <dir>` starts the Django app of `<checkout>` in-process and drives it with
Django's test `Client` (`POST /api/graphql`, `HTTP_HOST="localhost"`): real URL routing, middleware, JWT
authentication and GraphQL view, exactly like a request from the browser. It logs in like the web app, with the
`tokenAuth` mutation as `Admin` / `admin123` (`--user`, `--password`), then sends each query with the token in
the `Authorization` header. It is read-only: `tokenAuth` is the only mutation, and `snapshot.py` refuses any other.
It never imports graphene, so the same script runs unchanged on Graphene 2 and 3.

Output: one `<query name>.json` per query with `query`, `screen`, `http_status` and `response`, plus
`_manifest.json` with `versions` (Django, graphene, graphene-django), `git` (commit), `git_ref`, Python version and timings.

The database comes from the usual environment variables (`DB_NAME`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, ...).
Unset ones default to the CI values (`DB_NAME=test_imis`, `SITE_ROOT=api`, `MODE=DEV`, `OPENSEARCH_DSL_AUTOSYNC=False`, ...).
`--verbose` shows the backend's own log output.

`compare.py <before_dir> <after_dir> --report <file.html>` prints
`N queries, N identical, N different (M values compared)` and the JSON path, old value and new value of each
difference. The HTML report is a single self-contained file: a green or red verdict, the versions of both runs,
one row per screen, and the exact differences. Exit code `0` if every query is identical, `1` otherwise.

Comparison rules:
- Value by value and type-aware: `1`, `1.0`, `"1"` and `true` are all different; `null` vs `""` is a difference.
- Key order inside an object doesn't matter; list order does (a re-ordered result list is a difference).
- A query with GraphQL `errors` or a non-200 status is a failure, even if both sides return the same error.
- `_manifest.json` is shown in the report but never compared.

### Masked values

Before writing, `snapshot.py` replaces the values of these keys with `"<volatile>"` wherever they appear.
Nothing else is changed (no sorting, rounding or reformatting).

| Key | Why it changes between runs |
|---|---|
| `token`, `refreshToken`, `refresh_token`, `csrfToken` | login tokens, new on every login |
| `refreshExpiresIn`, `last_login`, `lastLogin` | timestamps computed from "now" |
| `age` | computed from today's date, so it changes on each insuree's birthday (`dob` is still compared) |

None of the token/timestamp keys appear in the current queries; the rule is a safety net for new queries.

## The queries

`queries/NN_<module>_<screen>.graphql` holds the query text as the web app builds it (same fields, filters, ordering
and page size of 10). Each file starts with a header: `# Screen:` (which screen), `# Source:` (frontend repo, file and
function) and `# Variables:` (JSON, or `none` when the values are written inline in the query, as the web app does).
`01_core_current_user.rest` is the one REST call: right after login the web app loads the user and their rights with
`GET /api/core/users/current_user/`. IDs are records of the `test_imis` sample data, so detail pages return real data
(insuree `070707070`, claim `CIA00001` with its services and items, etc.).

| Area | Queries |
|---|---|
| Login / permissions | current user + rights (REST), module permissions, roles |
| Insurees | search, detail, enquiry, insuree's policies, remaining benefits (eligibility) |
| Families | search, detail, members |
| Policies | search, detail, premiums of a policy |
| Claims | search (health facility view), detail with services and items |
| Contributions / payments | contribution search and detail, payment search (empty in the sample data) |
| Locations | regions, districts of a region, the user's districts |
| Health facilities | search, detail |
| Products | search, detail |
| Medical | items search, services search, service detail, item detail |

## Running a before/after check

Graphene 2 and 3 can't be installed side by side, and the openIMIS modules are editable installs bound to one
checkout, so each version needs **its own git worktree with its own virtualenv**. `snapshot.py` refuses to run if
the Python it is started with loads the modules from a different checkout than `--repo`.

The upgraded code also needs `manage.py migrate`: django-axes 7 adds `axes.0009_add_session_hash`, a required
column in its login log. After that migration the old code can't log in to that database any more, so use **two
copies of the same database**: `test_imis` for the old code, `test_imis_after` for the new one.

```bash
# 1. One worktree + venv per version (~2 min each, once). OLD/NEW are any git refs, e.g. main and the upgrade branch.
git worktree add --detach ~/oi-before OLD
git worktree add --detach ~/oi-after  NEW
for d in ~/oi-before ~/oi-after; do (
  cd "$d" && uv venv -p 3.11 .venv &&
  uv pip install --python .venv "setuptools<81" -r requirements.txt &&
  cd script && ../.venv/bin/python modules-requirements.py ../openimis.json > modules-requirements.txt &&
  uv pip install --python ../.venv -r modules-requirements.txt
) done

# 2. Old code on test_imis (~5 s; on a fresh database run `manage.py migrate` with the old code first, ~75 s).
#    Snapshot before copying: the first login creates Admin's user row with a random UUID, and both copies need the same one.
~/oi-before/.venv/bin/python tools/api_snapshot/snapshot.py --repo ~/oi-before --out /tmp/before

# 3. Copy the database for the new code and migrate the copy (~5 s + ~5 s).
docker exec oi-pg createdb -U postgres -T test_imis test_imis_after
(cd ~/oi-after/openIMIS && DB_NAME=test_imis_after ../.venv/bin/python manage.py migrate)

# 4. New code on the copy (~5 s), then compare (< 1 s).
DB_NAME=test_imis_after ~/oi-after/.venv/bin/python tools/api_snapshot/snapshot.py --repo ~/oi-after --out /tmp/after
python3 tools/api_snapshot/compare.py /tmp/before /tmp/after --report /tmp/api-report.html
```

Run the tool from a checkout that contains `tools/api_snapshot` (older refs don't have it); `--repo` picks the code
under test. `createdb -T` needs no other connections to `test_imis`, so stop any running server first.

Timings measured on the development VM: `snapshot.py` ~4 s (Django start-up ~1 s, `tokenAuth` login ~1.5 s for password
hashing, 30 queries ~1 s); `compare.py` < 0.2 s.

## About `baseline/`

`baseline/` is a snapshot of `main` before the upgrade, recorded on this repository's `test_imis` sample database.
It shows what the responses look like and lets you compare quickly against today's API. It is **not** required:
UUIDs (e.g. Admin's user id, created on first login) and some orderings (e.g. the product list) differ per database
instance, so a baseline from another machine can show false differences. For a real check, snapshot both versions on
copies of the same database as above. To refresh it, run `snapshot.py --out tools/api_snapshot/baseline` on `main`.

## Tests

```bash
python3 -m unittest discover -s tools/api_snapshot/tests
```

No dependencies beyond the Python standard library.
