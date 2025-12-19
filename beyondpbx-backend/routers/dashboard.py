from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import CDR
from schemas import CDRResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/calls")
def get_recent_calls(db: Session = Depends(get_db)):
    calls = db.query(CDR).order_by(CDR.calldate.desc()).limit(20).all()
    return calls