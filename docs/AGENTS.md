# Repository Guidelines

## Project Structure & Module Organization
The root scripts map directly to pipeline stages: `extract_content.py` pulls text, tables, and charts; `translate_paragraphs.py` and `translate_content.py` handle language conversion; `apply_alignment.py` and `apply_table_alignment.py` restore formatting; `update_pptx.py` writes results. `pipeline.py` offers a paragraph-only legacy flow. Translator adapters live in `translators/` with `base.py` defining the contract. Use `temp/` for intermediate JSONL artifacts, `input/` and `slides/` for source decks, and `output/` for generated presentations. Keep new assets alongside similar files to simplify CI scripting later.

## Build, Test, and Development Commands
`python pipeline.py input.pptx output.pptx` runs the minimal four-stage pipeline using defaults from `config.py`. `./run_pipeline.sh` activates `myenv` and executes the full end-to-end workflow, including table alignment and merge. `python test_workflow.py` drives the same stages with logging and sample inspection; run it after major changes to confirm interoperability. When iterating on a single stage, call the module directly (e.g., `python translate_content.py charts <in> temp/slide_context.jsonl <out>`).

## Coding Style & Naming Conventions
Follow the existing Python style: four-space indentation, snake_case for functions and variables, PascalCase for classes, and expressive, type-hinted signatures where feasible. Prefer f-strings, structured logging via `logging.getLogger`, and helper functions over in-line scripts. Mirror module naming on new files (`verb_noun.py`) and keep docstrings summary-first so downstream Sphinx support stays simple.

## Testing Guidelines
Integration tests rely on the sample deck in `slides/`. Maintain or extend the `test_*.py` scripts and keep fixtures lightweight; they are invoked manually, so limit external dependencies. New features should update `test_workflow.py` or add similarly named files so they are picked up by `python -m pytest` if adopted later. After test runs, inspect `temp/` outputs and clean large intermediates to avoid stale data influencing reruns.

## Commit & Pull Request Guidelines
With no shared git history, use concise imperative commits (`Add table alignment metrics`) grouped by logical change. Reference issue IDs when available and avoid bundling experimental assets. Pull requests should outline motivation, summarize stage-level effects, list commands executed (e.g., `python test_workflow.py`), and include before/after artifacts or screenshots for PPT changes.

## Configuration & Secrets
Default translator settings live in `config.py`; update those instead of hardcoding tokens. Keep API keys in environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) and document any new secret in `.env.example` before submitting a PR. Commit only redacted logs—`translation_pipeline.log` may contain content snippets, so scrub or rotate it prior to review.
