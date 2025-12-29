import os
import re
import smtplib
import uuid
from email.message import EmailMessage
from typing import Optional

from fastapi import UploadFile

from app.config import get_settings

settings = get_settings()


async def file_upload(file: UploadFile, model_name: Optional[str] = None) -> str:
    """
    Save an UploadFile into uploads/medias[/<model_name>]/<uuid>.<ext>
    Returns the path relative to the uploads directory that can be used
    with the mounted static files (e.g., "medias/user/abcd1234.jpg")
    """
    if file is None or file.filename is None:
        raise ValueError("No file provided")

    location = os.path.join("medias", model_name) if model_name else "medias"
    os.makedirs(os.path.join("uploads", location), exist_ok=True)

    filename = file.filename
    ext = filename.split(".")[-1] if "." in filename else ""
    filename = f"{uuid.uuid4().hex}{f'.{ext}' if ext else ''}"

    file_path = os.path.join(location, filename)
    dest_path = os.path.join("uploads", file_path)

    # Read and write the file content
    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    await file.close()

    # Return a forward-slash path usable in URLs
    return file_path.replace(os.sep, "/")


def send_email(to_email: str, subject: str, body: str):
    email_address = settings.EMAIL_ADDRESS
    email_password = settings.EMAIL_PASSWORD
    plain = re.sub(r"<[^>]*>", "", body)

    msg = EmailMessage()
    msg["From"] = email_address
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(plain)
    msg.add_alternative(body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_address, email_password)  # type: ignore
        server.send_message(msg)
        server.send_message(msg)
