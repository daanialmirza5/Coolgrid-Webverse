# Scripts

Project scripts live alongside the code they operate on rather than in one shared bucket:

- `scripts/verify_setup.py` — validates Python environment, dependencies, and pre-trained ML artifacts.
- `ml/train.py` — trains and exports all ML/physics artifacts and the demo dataset.
- `backend/app/seed.py` — seeds the database with the demo city, wards, observations, users, and intervention catalog (run as `python -m app.seed` from `backend/`).
- `frontend/scripts/copy-maplibre-worker.js` — copies maplibre-gl's worker bundle into `public/` (runs automatically via `postinstall`).

See the root [README.md](../README.md#local-installation) for the full setup sequence.
