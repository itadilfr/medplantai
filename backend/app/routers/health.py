from fastapi import APIRouter
from sqlalchemy import text
from ..database import get_db

router = APIRouter(tags=["health"])

@router.get("/health")
async def health(db=__import__("fastapi").Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}
