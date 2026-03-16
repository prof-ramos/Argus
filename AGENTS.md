# Repository Guidelines

## Project Structure & Module Organization
- Current repository layout is root-heavy. Main reference files live at the top level: `ARCHITECTURE.md`, `IMPLEMENTATION_GUIDE.md`, `DOCUMENTATION_SUMMARY.md`, and `argus_codigo_completo.md`.
- `codigocompleto.py` is the current all-in-one Python prototype. Helper/demo scripts are `script.py`, `script_1.py`, and `script_2.py`.
- The intended production layout is documented in `argus_codigo_completo.md`: `config/`, `collectors/`, `processing/`, `ai/`, `output/`, plus a CLI entry module such as `argus.py`.
- Store generated assets and diagrams near the docs they support; avoid creating new top-level files unless they are repository-wide.

## Build, Test, and Development Commands
- Use `uv` for Python workflows.
- Create and confirm the virtualenv before changes:
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```
- Run the current prototype locally:
```bash
uv run python codigocompleto.py --help
uv run python script.py
```
- When package files are added, prefer `uv run pytest` for tests and `uv run python -m <module>` for module execution.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation, type hints, and small focused functions.
- Use `snake_case` for files, functions, and variables; use `PascalCase` for classes like `ReportGenerator`.
- Keep async workflows explicit with `async def` and avoid mixing sync and async orchestration in the same helper unless necessary.
- Preserve Portuguese documentation when editing existing docs; keep code identifiers in English.

## Testing Guidelines
- There is no committed automated test suite yet. Add `pytest` tests under a future `tests/` directory when extracting logic from `codigocompleto.py`.
- Name tests by behavior, for example `tests/test_filter.py` and `test_removes_false_positives`.
- For now, validate changes with targeted CLI/manual runs and document the exact command used in the PR.

## Commit & Pull Request Guidelines
- Git history currently contains only `initial commit`, so there is no strong convention yet. Prefer short imperative commits such as `feat: split collectors into package`.
- Keep commits scoped to one concern.
- PRs should include: objective, affected files, validation commands, related issue if any, and screenshots only when docs or generated visuals change.

## Agent-Specific Notes
- Read local architecture docs before restructuring code.
- Prefer moving toward the documented modular layout instead of expanding the monolithic prototype.
