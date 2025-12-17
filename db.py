
from sqlmodel import Session

def get_session():
    with Session() as session:
        yield session