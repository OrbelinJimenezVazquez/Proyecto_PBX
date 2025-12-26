from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import CDR
from schemas import CDRResponse
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/calls")
def get_recent_calls(db: Session = Depends(get_db)):
    calls = db.query(CDR).order_by(CDR.calldate.desc()).limit(20).all()
    return calls

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    now = datetime.now()

    total_calls = db.query(CDR).count()
    answered_calls = db.query(CDR).filter(CDR.disposition == 'ANSWERED').count()
    missed_calls = db.query(CDR).filter(CDR.disposition == 'NO ANSWER').count()

    calls_today = db.query(CDR).filter(
        CDR.calldate >= now.replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()

    calls_this_week = db.query(CDR).filter(
        CDR.calldate >= (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()

    calls_this_month = db.query(CDR).filter(
        CDR.calldate >= now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ).count()

    return {
        "total_calls": total_calls,
        "answered_calls": answered_calls,
        "missed_calls": missed_calls,
        "calls_today": calls_today,
        "calls_this_week": calls_this_week,
        "calls_this_month": calls_this_month
    }
