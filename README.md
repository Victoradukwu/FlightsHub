# FlightsHub

Simple FastAPI project for managing flights and common endpoints.

---

## Run the app

### Set up
1. Clone directory
2. Create a file called local.env inside the app directory and populate it with the content of the sample.env file in the project root directory. Update the file accordingly
3. Run command: “uv sync”. To install packages
4. Run command: “docker compose --env-file app/local.env up
5. Run command: “uv run pytest” to ru. The automated tests

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


### GraphQL
### Websocket==Reservation created and cancelled (Updated seats)
### Background tasks