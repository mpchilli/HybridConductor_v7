# Changelog

All notable changes to the Hybrid Conductor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [7.2.9] - 2026-02-13
### Added
- Comprehensive pytest suite (68 tests) covering all core modules.
- Shared pytest fixtures in `tests/conftest.py`.
- Automated test runs via `python -m pytest tests/`.
- New dependencies: `pytest`, `rich`, `pyyaml`, `requests`.

### Changed
- Migrated legacy `__main__` block tests into dedicated test files.
- Refactored `requirements.txt` to include all runtime and dev dependencies.
- Updated `README.md` with gap analysis and ecosystem scorecard.

## [7.2.8] - 2026-02-13
### Added
- First stable release of Hybrid Orchestrator v7.
- Deterministic State Machine in `orchestrator.py`.
- Rick Protocol implementation in `loop_guardian.py`.
- Tiered Context Fetcher (Openground + Regex fallback).
- Interactive Web Dashboard with SSE stream.
- Windows-blind installation via `setup.py`.

### Fixed
- Unicode encoding errors in Windows-native subprocess calls.
- Subprocess window flickering on Windows.
- Path normalization across Windows and Linux formats.
