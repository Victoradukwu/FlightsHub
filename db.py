
import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, create_engine

load_dotenv("app/local.env")

is_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST"))
DB_URL = os.getenv("TEST_DATABASE_URL") if is_pytest else os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, pool_pre_ping=True)  # type: ignore


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]