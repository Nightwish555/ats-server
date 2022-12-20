from fastapi import APIRouter, Depends

router = APIRouter(prefix="/auth")


@router.get("/github/login")
async def login_with_github(code: str):
    ...
