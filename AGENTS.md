# Agent Guidance

This repository has a Streamlit frontend plus a small FastAPI backend for search and similarity APIs. When making changes:

- Always prefer the shared rerun helper (`_rerun` in `app.py`) instead of calling Streamlit rerun APIs directly.
- Keep sheet ingestion strict: required sheets must raise fast-fail errors, and schema/ID validation should remain in place (`backend/ingest/*`).
- Rebuild or update the README whenever you introduce user-visible workflows or new endpoints so humans can operate the stack without digging through code.
- Run `pytest -q` before opening a PR.
