from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
async def dashboard():
    return {"status": "healthy", "time": datetime.now()}