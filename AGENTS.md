# Repository Guidelines

## Project Structure & Module Organization

- `assurance/` contains the release-decision pipeline. Keep deterministic policy, evaluator, schema, and evidence logic here; its pure modules should not depend on Google ADK.
- `deploy_agent/` is the Cloud Run application and plugin chain. `spike_agent/` supports local ADK experimentation.
- `tests/` contains executable S1–S10 verification scripts. `data/` holds the committed sample queue and its generator; `evidence/` stores reproducible run artifacts.
- Keep design notes and operational material in `docs/` and `runbooks/`; use `scripts/` for small command-line helpers.

## Build, Test, and Development Commands

Use Python 3.14 with `uv` for local development:

```bash
uv venv --python 3.14 && source .venv/bin/activate
uv pip install -r requirements.txt
python -m assurance.batch --queue data/queue.jsonl
python tests/test_s10_planner.py
adk web spike_agent
```

The batch command runs the end-to-end deterministic pipeline. Test files are standalone scripts rather than a pytest suite; run the relevant `tests/test_s*.py` file from the repository root. Some tests refresh committed files under `evidence/`, so inspect those changes before committing. Deploy with `gcloud run deploy assurance-agent --source . --region=asia-east1`.

## Coding Style & Naming Conventions

Write Python with four-space indentation, type annotations for public interfaces, and `snake_case` for modules, functions, variables, and test files. Use `PascalCase` for classes and Pydantic models, and `UPPER_SNAKE_CASE` for constants. Keep policy evaluation deterministic and fail closed: unknown inputs must take the most restrictive route and produce a policy ID plus evidence. Match nearby code style; no formatter or linter is currently configured.

## Testing Guidelines

Name verification scripts `test_s<N>_<area>.py` and keep assertions focused on both the decision and its execution path. Add regression coverage for policy changes, including unknown or adversarial inputs. Run the narrowest affected test first, then the batch command when modifying routing, evaluators, or evidence schemas.

## Commit & Pull Request Guidelines

Follow the existing Conventional Commit pattern: `feat:`, `fix:`, `test:`, `docs:`, or `chore:`; optional scopes are welcome (for example, `fix(data): align thresholds`). Keep commits small and imperative. Pull requests should explain the policy or behavior change, list commands run, link the relevant issue or task, and include updated evidence or screenshots when they support a claim. Never commit `.env`, API keys, or generated credentials.
