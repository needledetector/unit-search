# Unit Search

Unit Search is a Streamlit + FastAPI playground for browsing idol units from published spreadsheets. Data is loaded from public Google Sheets CSV exports, validated, cached in SQLite, and exposed to both the Streamlit UI and a small API that powers search and similarity features.

## Features at a glance
- **Spreadsheet ingestion with validation:** `backend/ingest/sheets_client.py` pulls required/optional sheets and fails fast when a required sheet is missing. `backend/ingest/validators.py` enforces required columns and ID consistency across tables, while `backend/ingest/loader.py` orchestrates fetch → validate → normalize → persist to SQLite.
- **Search and filters:** `backend/services/search.py` builds a SQLite FTS5 index over members and aliases. `backend/api/routes/members.py` exposes `/members/search` with keyword search plus branch/status/generation filters defined in `backend/api/schemas.py`.
- **Unit lookup:** `backend/api/routes/units.py` returns unit metadata with members sorted by `unit_members.weight` for deterministic display order.
- **Similarity service:** `backend/features/matrix.py` builds a member×unit matrix and `backend/features/similarity.py` serves cosine-similarity ranking. `/similarity` (see `backend/api/routes/similarity.py`) exposes the top-N similar members API.
- **Streamlit UI:** `app.py` renders multilingual search, filters, and similarity views. It caches sheet reads, validates required columns, and handles both `st.rerun` and legacy `st.experimental_rerun` for Streamlit Cloud compatibility.

## Project layout
- `app.py`: Streamlit frontend, including sheet loading, filtering, and similarity visualization.
- `backend/`: FastAPI application and supporting services.
  - `ingest/`: Sheets client, schema validation, and loader with SQLite persistence and reload hooks.
  - `api/routes/`: FastAPI routers for members search, units, and similarity endpoints.
  - `features/`: Matrix construction and similarity helpers.
  - `services/`: Search service with FTS5 indexing.
  - `main.py`: App factory wiring loaders, search, and routes together.
- `tests/`: Pytest coverage for ingestion and API behaviors.

## Running the Streamlit app
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Provide sheet URLs (CSV export links) via environment variables or `st.secrets`:
   - Required: `SHEET_MEMBERS_URL`, `SHEET_MEMBER_GENERATIONS_URL`, `SHEET_UNITS_URL`, `SHEET_UNIT_MEMBERS_URL`
   - Optional: `SHEET_MEMBER_ALIASES_URL`, `SHEET_UNITS_ALIASES_URL`
3. Launch Streamlit:
   ```bash
   streamlit run app.py
   ```
   The app validates configured sheets and raises an error if any required sheet URL is missing.

## Running the API locally
The FastAPI app is defined in `backend/main.py`. A simple way to run it locally:
```bash
uvicorn backend.main:app --reload
```
The loader uses SQLite (in-memory by default). Add your own wiring if you want to share the cache between the API and Streamlit processes.

### Endpoints
- `GET /members/search`: keyword search with optional branch/status/generation filters and pagination.
- `GET /units/{unit_id}`: unit metadata plus members sorted by weight.
- `GET /similarity?member_id=...&top=...`: cosine similarity ranking for the given member ID.

## Similarity cache
Similarity matrices are recomputed in `DataLoader.load_from_frames`, and results are cached in-memory for repeated queries. Re-ingesting sheets (for example via a poller webhook) clears the cache and rebuilds the matrix to ensure fresh results.

## Testing
Run the test suite with:
```bash
pytest -q
```
Pytest covers schema validation, required-sheet failure modes, and API endpoints.
