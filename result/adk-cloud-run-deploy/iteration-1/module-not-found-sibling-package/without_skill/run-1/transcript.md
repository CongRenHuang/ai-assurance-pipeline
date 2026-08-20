[tool_use] Bash

The empty temp directory here confirms this is a described scenario rather than an actual checked-out project, so I'll produce diagnosis + ready-to-use fix artifacts under `outputs/` that you can drop into your real repo.

## Root cause

`adk deploy cloud_run ./my_agent` uses **only `./my_agent` as the build context**. It copies that directory's contents into the container image (and generates a Dockerfile that does `COPY . /app` from that same directory). Anything outside `my_agent/` — including a sibling `shared_lib/` — never reaches the image. The build/deploy still succeeds because there's no static import check at build time; the failure only shows up at runtime when `agent.py` executes `from shared_lib.policy import evaluate` and Python can't find the module in the container's filesystem → `ModuleNotFoundError`.

## Fix options (ranked)

1. **Nest `shared_lib/` inside `my_agent/`** (simplest, zero code changes). Since the agent directory's *contents* become the container's `/app`, moving `shared_lib/` to `my_agent/shared_lib/` makes it land at `/app/shared_lib`, and the existing `from shared_lib.policy import evaluate` still resolves.
2. **Ship it as an installable package** via `requirements.txt` (e.g. a local sdist/wheel or a git URL) if `shared_lib` is reused by multiple agents and duplicating it isn't desirable.
3. **Bypass `adk deploy cloud_run`'s auto-packaging** and deploy with your own Dockerfile from the *parent* directory (containing both `my_agent/` and `shared_lib/`), giving full control over what's copied.

I've written up all three with commands, plus concrete files for options 1 and 3.

[tool_use] Write

[tool_use] Write

[tool_use] Write

[tool_use] Bash

[tool_use] Bash

That's a minor permission bit, not essential — the script works fine run as `bash outputs/deploy.sh` without the executable bit, so I'll leave it as is rather than push on the approval.

## Summary

**Root cause:** `adk deploy cloud_run ./my_agent` only packages `./my_agent`'s contents into the container image. `shared_lib/`, being a sibling directory, is never copied in, so `agent.py`'s `from shared_lib.policy import evaluate` fails at runtime with `ModuleNotFoundError` even though the build/deploy itself succeeds.

Wrote to `outputs/`:
- **`README.md`** — full diagnosis and three ranked fix options (nest `shared_lib` into `my_agent`; make it an installable dependency; or deploy with a custom Dockerfile), plus verification steps.
- **`Dockerfile`** — custom image build that copies both `my_agent/` and `shared_lib/` from their common parent directory, for Option 3.
- **`deploy.sh`** — wraps `gcloud builds submit` + `gcloud run deploy` to use that Dockerfile instead of `adk deploy cloud_run`'s auto-packaging.

For your case, the fastest fix is Option 1: `mv shared_lib my_agent/shared_lib`, then redeploy with the same `adk deploy cloud_run ./my_agent` command — no code changes needed since `/app` (the container root) becomes `my_agent`'s contents.

[result] That's a minor permission bit, not essential — the script works fine run as `bash outputs/deploy.sh` without the executable bit, so I'll leave it as is rather than push on the approval.

## Summary

**Root cause:** `adk deploy cloud_run ./my_agent` only packages `./my_agent`'s contents into the container image. `shared_lib/`, being a sibling directory, is never copied in, so `agent.py`'s `from shared_lib.policy import evaluate` fails at runtime with `ModuleNotFoundError` even though the build/deploy itself succeeds.

Wrote to `outputs/`:
- **`README.md`** — full diagnosis and three ranked fix options (nest `shared_lib` into `my_agent`; make it an installable dependency; or deploy with a custom Dockerfile), plus verification steps.
- **`Dockerfile`** — custom image build that copies both `my_agent/` and `shared_lib/` from their common parent directory, for Option 3.
- **`deploy.sh`** — wraps `gcloud builds submit` + `gcloud run deploy` to use that Dockerfile instead of `adk deploy cloud_run`'s auto-packaging.

For your case, the fastest fix is Option 1: `mv shared_lib my_agent/shared_lib`, then redeploy with the same `adk deploy cloud_run ./my_agent` command — no code changes needed since `/app` (the container root) becomes `my_agent`'s contents.
