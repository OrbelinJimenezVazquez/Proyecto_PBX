from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter(prefix="/api", tags=["Telephony"])

@router.get("/extensions")
def get_extensions(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
          u.extension,
          u.name,
          CASE 
            WHEN s_host.data IS NULL THEN 'offline'
            WHEN s_host.data = 'dynamic' THEN 'online'
            WHEN s_host.data REGEXP '^[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}$' THEN 'online'
            ELSE 'offline'
          END AS status
        FROM asterisk.users u
        LEFT JOIN asterisk.sip s_host 
          ON u.extension = s_host.id AND s_host.keyword = 'host'
        ORDER BY u.extension
    """)
    result = db.execute(query).fetchall()
    return [
        {"extension": row[0], "name": row[1], "status": row[2]}
        for row in result
    ]

@router.get("/calls/recent")
def get_recent_calls(db: Session = Depends(get_db)):
    query = text("""
        SELECT src, dst, calldate, duration, disposition
        FROM asteriskcdrdb.cdr
        ORDER BY calldate DESC
        LIMIT 15
    """)
    result = db.execute(query).fetchall()
    return [
        {
            "src": row[0],
            "dst": row[1],
            "calldate": row[2],
            "duration": row[3],
            "disposition": row[4]
        }
        for row in result
    ]

@router.get("/trunks")
def get_trunks(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            name,
            tech,
            channelid
        FROM asterisk.trunks
        ORDER BY name
    """)
    result = db.execute(query).fetchall()
    return [
        {
            "name": row[0],
            "tech": row[1],
            "channelid": row[2]
        }
        for row in result
    ]
