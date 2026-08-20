---
name: adk-cloud-run-deploy
description: >-
  Deploys a Google ADK (Agent Development Kit) agent to Cloud Run and
  diagnoses the three deploy-time failures specific to that stack: a
  ModuleNotFoundError for a package that lives outside the agent directory,
  a 404 "Agent not found" on /run despite session creation succeeding, and
  a 403 on the live URL from Cloud Run's default authenticated-only access.
  Use when the request mentions `adk deploy cloud_run`, `adk api_server`,
  or deploying/debugging an ADK agent on Cloud Run — not for generic
  Cloud Run/Docker deploys of non-ADK apps.
---

# ADK Cloud Run Deploy

Get an ADK agent's plugins and hard-policy gates actually enforced on a
live Cloud Run service, and fix the three deploy-time failures that look
like generic Cloud Run problems but have ADK-specific causes and fixes.

## Root fact: `adk deploy cloud_run <agent_dir>` only bundles `<agent_dir>`

It uses `<agent_dir>` as the entire build context. Any sibling package the
agent imports (e.g. a `shared_lib/` or `assurance/` package next to the
agent folder, not inside it) never reaches the image. The build and deploy
both succeed — there's no import check at build time — so the failure only
surfaces at runtime as `ModuleNotFoundError` in the Cloud Run logs.

**The correct fix is switching the build strategy, not restructuring the
repo.** Moving/copying the sibling package into the agent directory
"works" for a toy case but duplicates code and diverges the next time
either copy changes. Fix it by building from the repo root instead:

1. Write a `Dockerfile` at the repo root that does `COPY . .` (respecting
   `.dockerignore`) and runs `adk api_server <agent_dir_name> --host 0.0.0.0 --port $PORT`.
2. Deploy with `gcloud run deploy --source .` from the repo root — not
   `adk deploy cloud_run <agent_dir>` again with the same directory scope.
3. After redeploy, confirm the fix by tailing logs
   (`gcloud run services logs read <service> --region <region>`) or hitting
   the service, not by assuming the redeploy alone fixed it.

## Root fact: the routable `app_name` is the deployed folder name, not `App(name=...)`

If the agent module does `app = App(name="my_cool_agent", root_agent=...,
plugins=[...])` inside a folder called `deploy_agent/`, the API server's
actual routing key is `deploy_agent` — the folder name — never the `name=`
field passed to `App(...)`, which is metadata only.

This produces a specific, misleading symptom: **session creation succeeds
with the wrong app_name** (the session store doesn't validate that an agent
by that name is loaded), but **`/run` 404s** because that's the call that
actually looks up the agent. A 404 after a successful session create is the
signature of this exact mismatch, not an auth or routing bug.

Confirm with `curl https://<service-url>/list-apps` — the array it returns
is the real list of routable names. Use whichever name shows up there in
every subsequent `/run` and session call.

## Discipline: confirm before granting public access

A live Cloud Run URL returning 403 for anonymous requests is Cloud Run's
default (authenticated-only) when the deploy ran non-interactively, so the
"Allow unauthenticated invocations?" prompt never had a chance to answer
`y`. The fix is real:

```
gcloud run services add-iam-policy-binding <service> \
  --region=<region> --member="allUsers" --role="roles/run.invoker"
```

But granting `allUsers` access is a security-posture change, not a
mechanical unblock — **ask the user to confirm they want the service
public before running it**, don't hand over a ready-to-run script or run
the binding as the obvious next step. If they only wanted authenticated
access restored to a specific caller, `allUsers` is the wrong fix.

## Resources

None bundled — the three fixes above are self-contained shell/gcloud
commands, not scripts worth packaging.
