# backend/app/api/routes_root.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["root"])
async def read_root():
    return {"message": "Welcome to the Med Consult AI backend."}
