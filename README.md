# FlightsHub

Simple FastAPI project for managing flights and common endpoints.

---

### Set up
1. Clone directory
2. Create a file called local.env inside the app directory and populate it with the content of the `sample.env` file in the project root directory. Update the file accordingly
3. Run command: “uv sync”. To install packages
5. Run command: “uv run pytest” to run the automated tests

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


## Docker
You can also run the application with Docker. Docker compose is used to ochestrate the app and its related services: postgres, redis, and Celery
1. Run command: “docker compose --env-file app/local.env up
2. Visit `http://localhost:8000/docs` to access the API documentation


## API Paradigms
The application provides two API paradigms
- REST API: All features are available in RESTFUL API
- GraphQL: The application also provides  GraphQL supports for some operations


## Other Features
### Background tasks: Tasks such as user emails are handled with built in FastAPI Background task
### Celery: Celery Beat is used to handle schedulled tasks such as flight booking payment reminder
### Websocket: This is used to emmit the current seats of a given flight. This ensures the users always have the current status of each seat, whether available or not. It is also used to return result of flights obtained from external sources using AI

---

## GenAI Flight Search (REST)
- Flight search using GenAI with OpenAI and HuggingFace
- Endpoint: `/api/v1/flights/search` (POST)
- Purpose: Search flights between two airports for a given date using the internal database. Also returns external AI-suggested flights (GenAI) with booking links.
- The results from our system is returned immediately, while the result obtained by GenAI from external search is returned via webhook when ready.


### Provider switching (LangChain)

- Configure in `app/local.env`:
	- `AI_PROVIDER=MOCK` (default) or `OPENAI` or `HuggingFace`
	- `OPENAI_API_KEY=<your_key>`
	- `OPENAI_MODEL=gpt-4.1-mini`

When `AI_PROVIDER=OPENAI`, the app uses LangChain (`ChatOpenAI`) with structured output into the `ExternalFlightsResponse` Pydantic model. `MOCK` returns deterministic samples for development.