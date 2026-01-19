#!/bin/sh
# entrypoint.sh

echo "Applying Alembic migrations..."
alembic upgrade head
echo "Migrations applied."

# Execute the main command (e.g., uvicorn) passed to the container
exec "$@"