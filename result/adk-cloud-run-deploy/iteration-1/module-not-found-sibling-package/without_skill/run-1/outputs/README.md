# Fix: `ModuleNotFoundError: No module named 'shared_lib'` after `adk deploy cloud_run`

## Diagnosis

`adk deploy cloud_run ./my_agent` treats `./my_agent` as the **entire build
context**. Internally it:

1. Copies the contents of `my_agent/` into a temp staging folder (or the
   Cloud Run source-deploy tarball).
2. Generates a Dockerfile that does the equivalent of `COPY . /app` from
   that staging folder.
3. Builds and deploys the image via Cloud Build + Cloud Run.

Because `shared_lib/` lives **next to** `my_agent/`, not inside it, it is
outside the build context and is silently dropped. The build and `gcloud
run deploy` both succeed (there's nothing to statically check imports
against), but the first request that executes `agent.py`'s
`from shared_lib.policy import evaluate` fails at runtime with
`ModuleNotFoundError`, because `/app/shared_lib` doesn't exist in the
container.

This is a packaging problem, not a Python/ADK bug — fix it by changing
what gets shipped into the image.

## Option 1 (recommended for a single agent): nest `shared_lib` inside `my_agent`

Move the directory so it travels with the agent:

```bash
# from the parent directory that currently holds my_agent/ and shared_lib/
git mv shared_lib my_agent/shared_lib   # or plain `mv` if not in git
```

No code changes needed: `my_agent/`'s *contents* become the container's
`/app`, so `my_agent/shared_lib/` becomes `/app/shared_lib/`, and the
existing `from shared_lib.policy import evaluate` in `agent.py` still
resolves correctly.

Redeploy exactly as before:

```bash
adk deploy cloud_run ./my_agent \
  --project YOUR_PROJECT --region YOUR_REGION --service_name YOUR_SERVICE
```

Trade-off: if other agents also depend on `shared_lib`, you now have
multiple copies to keep in sync. Use Option 2 if that's the case.

## Option 2: make `shared_lib` an installable dependency

Better when `shared_lib` is shared across multiple agent projects. Give it
a minimal `pyproject.toml`, then reference it from `my_agent/requirements.txt`
as a path or VCS dependency so `pip install -r requirements.txt` pulls it
into the image during the Cloud Build step:

```
# my_agent/requirements.txt
google-adk
./shared_lib          # if it's still colocated, OR:
# git+https://github.com/your-org/shared-lib.git@main
```

If you keep it as a local path dependency, it must be reachable from the
build context, which pushes you back toward Option 1 or Option 3 — for a
truly independent package, publish it (private PyPI, Artifact Registry
Python repo, or a git URL) and drop the path reference.

## Option 3: skip `adk deploy cloud_run`'s auto-packaging, use your own Dockerfile

Deploy from the **parent** directory that contains both `my_agent/` and
`shared_lib/`, with an explicit Dockerfile that copies both. This keeps
`shared_lib/` as a true sibling (no duplication, no packaging step) and
gives you full control. See `Dockerfile` and `deploy.sh` in this folder —
copy them next to `my_agent/` and `shared_lib/` (i.e. into their common
parent directory) and run `./deploy.sh`.

Key points in that Dockerfile:
- Build context is the parent directory, so `COPY my_agent/ shared_lib/`
  both succeed.
- `PYTHONPATH=/app` ensures `shared_lib` and `my_agent` are both
  importable as top-level packages, matching the original
  `from shared_lib.policy import evaluate` import.
- The `CMD` runs `adk api_server`, ADK's standard way of serving an agent
  over HTTP — adjust the module path / port / flags to match how you run
  the agent locally if you use a custom FastAPI wrapper
  (`google.adk.cli.fast_api.get_fast_api_app`) instead.

## Verifying the fix

After redeploying with any of the above, confirm the module is actually
in the image before trusting a live request:

```bash
# find the revision's image and inspect it without traffic
gcloud run revisions describe REVISION --region YOUR_REGION \
  --format='value(spec.containers[0].image)'

gcloud run services proxy YOUR_SERVICE --region YOUR_REGION &
curl -s localhost:8080/... # hit whatever health/invoke route your agent exposes
```

and tail logs during a real request:

```bash
gcloud beta run services logs tail YOUR_SERVICE --region YOUR_REGION
```

You should no longer see `ModuleNotFoundError: No module named
'shared_lib'`.
