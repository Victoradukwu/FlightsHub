
from fastapi import APIRouter

router = APIRouter(
    prefix="/common",
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/",
    summary="Just testing",
    response_description="Testing path in the Common module",
)
def common():
    return "Hello from here again updated"