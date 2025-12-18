
from datetime import datetime
from sqlmodel import SQLModel, Field



class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str
    phone_number: str
    created_at: datetime
    updated_at: datetime
    status: str