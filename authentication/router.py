from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from authentication.utils import authenticate_user, create_access_token, get_current_active_user, get_settings
from common.utils import file_upload
from db import SessionDep

from .models import Token, User, UserCreate, UserOut

settings = get_settings()
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

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


@router.post("/token/")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_out = UserOut(**user.model_dump())
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer", user=user_out)


@router.get("/users/me/", response_model=UserOut)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user