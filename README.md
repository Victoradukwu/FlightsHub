# FlightsHub

Simple FastAPI project for managing flights and common endpoints.

---

## Run the app

### Development (fast reload) ✅

From the project root (where the `app/` package lives):

```bash
# Install Uvicorn if needed
uv add "uvicorn[standard]"

# Run with auto-reload (recommended for development)
uvicorn app:app --reload --host 127.0.0.1 --port 8000

# Or listen on all interfaces (e.g., for testing on another device):
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open the interactive API docs at: http://127.0.0.1:8000/docs ✅

---

### Production (no reload, multiple workers) ⚠️

For production, do not use `--reload`. Run Uvicorn directly with workers or run behind Gunicorn with Uvicorn workers.

```bash
# Run Uvicorn (recommended settings for simple deployments)
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 3

# Or using Gunicorn + Uvicorn workers
uv add gunicorn uvicorn
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 app.main:app
```
