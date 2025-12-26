from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from common.utils import file_upload
from db import SessionDep

from .models import User, UserCreate, UserOut

router = APIRouter(
    prefix="/auth",
    responses={404: {"description": "Not found"}},
)


@router.post("/register/", response_model=UserOut)
async def register(
    request: Request,
    session: SessionDep,
    user: UserCreate = Depends(UserCreate.as_form),
    avatar: Annotated[UploadFile | None, File(description="User Registration")] = None,
):
    """register new user."""

    # Pre-check for duplicates to provide a friendly error message
    if session.exec(select(User).where(User.username == user.username)).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    if session.exec(select(User).where(User.email == user.email)).first():
        raise HTTPException(status_code=409, detail="Email already exists")

    # Save file under uploads/medias/avatars/<uuid>.<ext>
    if avatar:
        file_path = await file_upload(avatar, model_name="users")

        # Build a full URL to the saved file using the mounted static route name 'uploads' if request available
        url = request.url_for("uploads", path=file_path) if request is not None else f"/uploads/{file_path}"
    else:
        url = ""

    usr = User(**user.model_dump(), avatar=str(url))
    session.add(usr)
    try:
        session.commit()
        session.refresh(usr)
    except IntegrityError:
        session.rollback()
        # Race condition fallback: unique constraint at DB-level violated
        raise HTTPException(status_code=409, detail="Username or email already in use")
    return usr
