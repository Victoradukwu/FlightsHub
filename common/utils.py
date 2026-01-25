import re
import smtplib
import uuid
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.config import get_settings

settings = get_settings()


def file_upload(file: UploadFile, model_name: Optional[str] = None) -> str:
    """
    Save an UploadFile into uploads/medias[/<model_name>]/<uuid>.<ext>
    Returns the path relative to the uploads directory that can be used
    with the mounted static files (e.g., "medias/user/abcd1234.jpg")
    """
    if file is None or file.filename is None:
        raise ValueError("No file provided")

    location = "medias"
    if model_name:
        location += f"/{model_name}"

    pth = Path("uploads") / location
    pth.mkdir(parents=True, exist_ok=True)

    filename = file.filename
    ext = filename.split(".")[-1] if "." in filename else ""
    filename = f"{uuid.uuid4().hex}{f'.{ext}' if ext else ''}"

    file_path = Path(location) / filename
    dest_path = pth / filename

    content = file.file.read()
    dest_path.write_bytes(content)
    file.file.close()

    return str(file_path)


def send_email(to_email: str, subject: str, body: str):
    email_address = settings.EMAIL_ADDRESS
    email_password = settings.EMAIL_PASSWORD
    plain = re.sub(r"<[^>]*>", "", body)

    msg = EmailMessage()
    msg["From"] = settings.EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(plain)
    msg.add_alternative(body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_address, email_password)  # type: ignore
        server.send_message(msg)
