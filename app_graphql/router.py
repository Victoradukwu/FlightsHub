

from typing import Annotated

from fastapi import Depends
from strawberry.fastapi import GraphQLRouter

from authentication.utils import get_current_user_optional
from db import SessionDep
from models.authentication import User

from .schema import schema


async def get_context(session: SessionDep, current_user: Annotated[User, Depends(get_current_user_optional)]):
    return {
        "session": session,
        "user": current_user,
    }

graphql_router = GraphQLRouter(schema, context_getter=get_context)
