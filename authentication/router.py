from datetime import timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from authentication.utils import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    get_settings,
    get_user,
    verify_password,
)
from common.utils import file_upload, send_email
from db import SessionDep
from models.authentication import PasswordChange, PasswordReset, Token, User, UserCreate, UserOut

settings = get_settings()
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

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


@router.post("/password/change/")
async def change_password(
    user: PasswordChange, current_user: Annotated[User, Depends(get_current_active_user)], session: SessionDep
):
    if verify_password(user.old_password, current_user.password):
        current_user.password = get_password_hash(user.new_password)
        session.add(current_user)
        session.commit()
        return JSONResponse(content="Password successfully changed")
    return JSONResponse(content="Could not authenticate user")


@router.get("/password/request-reset/")
async def reset_password(username: str, background_tasks: BackgroundTasks):
    user = get_user(username=username)
    if user:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        msg = f"""
        <html>
        <head></head>
        <body>
        Hi {user.first_name},
        <p>
        We received a password reset request from you.  <a href={settings.FE_PW_RESET_URL}/?token={access_token}>Click here to reset password</a>. 
        </p>
        <p>
        If the link does not respond, copy this and past into your browser: {settings.FE_PW_RESET_URL}/?token={access_token}
        </p>
        Thank you,
        <br>
        FlightsHub Team
        </body>
        </html>
        """
        background_tasks.add_task(send_email, user.email, "Password reset", msg)
    return {
        "message": f"Kindly check your email. If user with this username is found in our system, an email will be sent to the associated email. Kindly follow the instrcution to complete the password reset. The link expires in {ACCESS_TOKEN_EXPIRE_MINUTES} minutes"
    }


@router.post("/password/complete-reset/")
async def reset_password_complete(data: PasswordReset, session: SessionDep):
    token = data.token

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return JSONResponse("Invalid token", status_code=status.HTTP_400_BAD_REQUEST)
    except jwt.InvalidTokenError:
        return JSONResponse("Invalid token", status_code=status.HTTP_400_BAD_REQUEST)
    user = get_user(username=username)

    if not user:
        return JSONResponse("Invalid token", status_code=status.HTTP_400_BAD_REQUEST)
    try:
        user.password = get_password_hash(data.password)  # type: ignore
        session.add(user)
        session.commit()
        return JSONResponse(content="Password successfully reset")
    except Exception as exc:
        return JSONResponse(content=f"An error occured: {exc}")
