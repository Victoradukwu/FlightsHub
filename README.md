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

---

## GenAI Flight Search (REST)

- Endpoint: `/api/v1/flights/search` (POST)
- Purpose: Search flights between two airports for a given date using the internal database. Also returns external AI-suggested flights (GenAI) with booking links.
- No auto-book: Results only; differentiate internal vs GenAI suggestions.

### Request body

```
{
	"origin_iata": "LOS",
	"destination_iata": "ABV",
	"date": "2026-02-02"
}
```

### Response

```
{
	"internal_flights": [ { /* internal flight info */ } ],
	"external_flights": [ { /* GenAI suggestion with booking_url */ } ]
}
```

### Provider switching (LangChain)

- Configure in `app/local.env`:
	- `AI_PROVIDER=MOCK` (default) or `OPENAI`
	- `OPENAI_API_KEY=<your_key>`
	- `OPENAI_MODEL=gpt-4.1-mini`

When `AI_PROVIDER=OPENAI`, the app uses LangChain (`ChatOpenAI`) with structured output into the `ExternalFlightsResponse` Pydantic model. `MOCK` returns deterministic samples for development.