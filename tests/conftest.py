
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

import db as db_module
from app.config import get_settings, reset_settings_cache

reset_settings_cache()
settings = get_settings()
TEST_DATABASE_URL = settings.TEST_DATABASE_URL
engine = create_engine(TEST_DATABASE_URL)

# ---------------------------
# Run Alembic migrations once
# ---------------------------
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    with engine.connect() as conn:
        conn.exec_driver_sql("DROP TYPE IF EXISTS admin_status CASCADE")
        conn.commit()
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield
    command.downgrade(alembic_cfg, "base")
    # Ensure enum types created by migrations are removed for clean subsequent runs
    with engine.connect() as conn:
        conn.exec_driver_sql("DROP TYPE IF EXISTS admin_status CASCADE")
        conn.commit()


# @pytest.fixture(scope="function")
# def db_session():
#     connection = engine.connect()
#     transaction = connection.begin()
#     session = Session(bind=connection)
#     yield session
#     session.close()
#     transaction.rollback()
#     connection.close()
    

@pytest.fixture(scope="function")
def db_session():
    # Use explicit transaction with rollback to keep DB clean per test
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_session():
        # Reuse the per-test transactional session
        yield db_session

    # Import the FastAPI app lazily after wiring the test engine
    from app import app as fastapi_app
    fastapi_app.dependency_overrides[db_module.get_session] = override_get_session

    with TestClient(fastapi_app) as client:
        yield client

    fastapi_app.dependency_overrides.clear()
