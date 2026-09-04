# Shared-Account Elimination Workflow — Frontend

This frontend is a self-contained HTML application.

## How to Run

Simply open `index.html` in any modern browser (Chrome, Edge, Firefox).

No Node.js, npm, or build step is required.

## API Backend

The frontend connects to the FastAPI backend at: `http://localhost:8000`

Start the backend first:
```bash
cd ../backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## Files

- `index.html` — Complete self-contained React app (via CDN)
- All pages are in a single HTML file using React with Babel standalone
