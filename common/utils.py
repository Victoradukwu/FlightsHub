import os
import uuid
from typing import Optional

from fastapi import UploadFile


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

