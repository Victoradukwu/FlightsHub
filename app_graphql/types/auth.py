import datetime
from typing import Optional

import strawberry
from strawberry.file_uploads import Upload


@strawberry.type
class UserOutputType:
    id: strawberry.ID
    first_name: str
    last_name: str
    username: str
    email: str
    phone_number: str
    status: Optional[str]
    role: str
    avatar: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime


@strawberry.input
class UserCreateInput:
    first_name: str
    last_name: str
    username: str
    email: str
    phone_number: str
    password: str
    confirm_password: str
    avatar: Optional[Upload] = None

    def __post_init__(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")


@strawberry.type
class TokenType:
    access_token: str
    token_type: str
    user: UserOutputType


@strawberry.type
class ResponseType:
    detail: str
