from datetime import timedelta

import jwt
import strawberry
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.config import get_settings
from app_graphql.types.auth import ResponseType, TokenType, UserCreateInput, UserOutputType
from authentication.utils import authenticate_user, create_access_token, get_password_hash, get_user, verify_password
from common.utils import file_upload, send_email
from models.authentication import User, _hash

settings = get_settings()
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


@strawberry.type
class AuthMutations:
    @strawberry.mutation
    def register(self, user: UserCreateInput, info: strawberry.Info) -> UserOutputType:
        """
        Register a new user record in the system.
        """
        session = info.context["session"]
        request = info.context["request"]

        if session.exec(select(User).where(User.username == user.username)).first():
            raise HTTPException(status_code=409, detail="Username already exists")
        if session.exec(select(User).where(User.email == user.email)).first():
            raise HTTPException(status_code=409, detail="Email already exists")

        if user.avatar:
            file_path = file_upload(user.avatar, model_name="users")  # type: ignore
            url = request.url_for("uploads", path=file_path) if request is not None else f"/uploads/{file_path}"
        else:
            url = ""

        setattr(user, "avatar", str(url))
        setattr(user, "password", _hash(user.password))
        usr = User(**strawberry.asdict(user))  # type: ignore
        session.add(usr)
        try:
            session.commit()
            session.refresh(usr)
        except IntegrityError:
            session.rollback()
            # Race condition fallback: unique constraint at DB-level violated
            raise HTTPException(status_code=409, detail="Username or email already in use")

        delattr(usr, "password")
        return UserOutputType(**usr.model_dump())

    @strawberry.mutation
    def login_for_access_token(self, username: str, password: str, info: strawberry.Info) -> TokenType:
        """
        Log in a user and return a token.
        """

        user = authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        delattr(user, "password")
        user_out = UserOutputType(**user.model_dump())
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        return TokenType(access_token=access_token, token_type="bearer", user=user_out)

    @strawberry.mutation
    def change_password(
        self, old_password: str, new_password: str, confirm_password: str, info: strawberry.Info
    ) -> ResponseType:
        if new_password != confirm_password:
            raise ValueError("Passwords do not match")

        session = info.context["session"]
        user = info.context["user"]
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if verify_password(old_password, user.password):
            user.password = get_password_hash(new_password)
            session.add(user)
            session.commit()
            return ResponseType(detail="Password successfully changed")
        return ResponseType(detail="Could not authenticate user")

    @strawberry.mutation
    def reset_password(self, username: str, info: strawberry.Info) -> ResponseType:
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
            info.context.get("background_tasks").add_task(send_email, user.email, "Password reset", msg)
        return ResponseType(
            detail=f"Kindly check your email. If user with this username is found in our system, an email will be sent to the associated email. Kindly follow the instrcution to complete the password reset. The link expires in {ACCESS_TOKEN_EXPIRE_MINUTES} minutes"
        )

    @strawberry.mutation
    def reset_password_complete(
        self, token: str, password: str, confirm_password: str, info: strawberry.Info
    ) -> ResponseType:
        session = info.context["session"]
        if password != confirm_password:
            raise ValueError("Passwords do not match")

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                return ResponseType(detail="Invalid token")
        except jwt.InvalidTokenError:
            return ResponseType(detail="Invalid token")
        user = get_user(username=username)

        if not user:
            return ResponseType(detail="Invalid token")
        try:
            user.password = get_password_hash(password)
            session.add(user)
            session.commit()
            return ResponseType(detail="Password successfully reset")
        except Exception as exc:
            return ResponseType(detail=f"An error occured: {exc}")
