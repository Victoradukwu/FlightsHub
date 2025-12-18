from fastapi import APIRouter

router = APIRouter(
    prefix="/common",
    responses={404: {"description": "Not found"}},
)

@router.get("/", tags=["custom"])
def common():
    return "Hello from here again updated"