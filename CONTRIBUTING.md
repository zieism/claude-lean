# Contributing

Thank you for helping. Keep changes small, dependency-free and safe.

1. Python: standard library only (3.8+). Shell: portable bash (macOS ships bash 3.2 — no associative arrays,
   no `mapfile`).
2. Run the tests before a pull request: `python3 -m unittest -v tests/test_toolkit.py` and `bash -n scripts/*.sh`.
3. Model preservation is mandatory: never change or recommend changing the user's model or effort settings (no
   `model` edits, no `/model`, no `ANTHROPIC_MODEL`, no `--model`). Never touch settings, billing or credentials,
   and never run anything in the background. `TestModelPreservation` must stay green.
4. Never add real transcripts, checkpoints or logs — use synthetic fixtures (see `tests/test_toolkit.py`).
5. Claims about savings need measurements: describe the workload, the before/after numbers from `usage_report.py`
   and the `/usage` readings. No unmeasured percentages in docs.
6. Update `CHANGELOG.md` and the relevant page in `docs/`.
