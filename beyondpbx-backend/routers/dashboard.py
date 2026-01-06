from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, case
from database import get_db
from models import CDR, QueueLog, QueueStats, QueueStatsMV
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

# ============================================
# ENDPOINTS NUEVOS PARA MÉTRICAS DE COLAS
# ============================================

@router.get("/queue-metrics")
def get_queue_metrics(
    period: str = Query("today", enum=["today", "week", "month"]),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas detalladas por cola usando queuelog
    """
    now = datetime.now()
    
    # Calcular fecha de inicio según período
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    else:  # month
        start_date = now - timedelta(days=30)
    
    # Consulta usando queuelog (nombre correcto de tabla) con time como datetime
    metrics_query = text("""
        SELECT 
            queuename,
            COUNT(DISTINCT CASE WHEN event = 'ENTERQUEUE' THEN callid END) as total_calls,
            COUNT(DISTINCT CASE WHEN event IN ('CONNECT', 'COMPLETEAGENT', 'COMPLETECALLER') THEN callid END) as answered_calls,
            COUNT(DISTINCT CASE WHEN event IN ('ABANDON', 'EXITWITHTIMEOUT', 'EXITWITHKEY') THEN callid END) as abandoned_calls,
            AVG(CASE WHEN event = 'CONNECT' AND data1 REGEXP '^[0-9]+$' THEN CAST(data1 AS DECIMAL(10,2)) END) as avg_wait_time,
            AVG(CASE WHEN event IN ('COMPLETEAGENT', 'COMPLETECALLER') AND data2 REGEXP '^[0-9]+$' THEN CAST(data2 AS DECIMAL(10,2)) END) as avg_talk_time,
            MAX(CASE WHEN event = 'CONNECT' AND data1 REGEXP '^[0-9]+$' THEN CAST(data1 AS DECIMAL(10,2)) END) as max_wait_time
        FROM asteriskcdrdb.queuelog
        WHERE time >= :start_date
            AND queuename != 'NONE'
        GROUP BY queuename
        ORDER BY queuename
    """)
    
    result = db.execute(metrics_query, {"start_date": start_date}).fetchall()
    
    queue_metrics = []
    for row in result:
        total = row[1] or 0
        answered = row[2] or 0
        abandoned = row[3] or 0
        answer_rate = round((answered / total * 100), 1) if total > 0 else 0
        abandon_rate = round((abandoned / total * 100), 1) if total > 0 else 0
        
        queue_metrics.append({
            "queue_name": row[0],
            "total_calls": total,
            "answered_calls": answered,
            "abandoned_calls": abandoned,
            "answer_rate": answer_rate,
            "abandon_rate": abandon_rate,
            "avg_wait_time": round(row[4] or 0, 1),
            "avg_talk_time": round(row[5] or 0, 1),
            "max_wait_time": round(row[6] or 0, 1)
        })
    
    return {
        "period": period,
        "queues": queue_metrics
    }

@router.get("/queue-sla")
def get_queue_sla(
    period: str = Query("today", enum=["today", "week", "month"]),
    sla_threshold: int = Query(30, description="SLA threshold in seconds"),
    db: Session = Depends(get_db)
):
    """
    Calcula el nivel de servicio (SLA) por cola
    SLA = % de llamadas contestadas dentro del umbral definido
    """
    now = datetime.now()
    
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    else:  # month
        start_date = now - timedelta(days=30)
    
    # Calcular SLA usando queuelog (datetime, no timestamp)
    sla_query = text("""
        SELECT 
            queuename,
            COUNT(DISTINCT CASE WHEN event = 'ENTERQUEUE' THEN callid END) as total_calls,
            COUNT(DISTINCT CASE 
                WHEN event = 'CONNECT' 
                AND data1 REGEXP '^[0-9]+$'
                AND CAST(data1 AS DECIMAL(10,2)) <= :sla_threshold 
                THEN callid 
            END) as calls_within_sla,
            AVG(CASE 
                WHEN event = 'CONNECT' AND data1 REGEXP '^[0-9]+$'
                THEN CAST(data1 AS DECIMAL(10,2)) 
            END) as avg_answer_time
        FROM asteriskcdrdb.queuelog
        WHERE time >= :start_date
            AND queuename != 'NONE'
        GROUP BY queuename
        ORDER BY queuename
    """)
    
    result = db.execute(sla_query, {
        "start_date": start_date,
        "sla_threshold": sla_threshold
    }).fetchall()
    
    sla_data = []
    for row in result:
        total = row[1] or 0
        within_sla = row[2] or 0
        sla_percentage = round((within_sla / total * 100), 1) if total > 0 else 0
        
        # Clasificar el SLA
        if sla_percentage >= 80:
            sla_status = "excellent"
        elif sla_percentage >= 60:
            sla_status = "good"
        elif sla_percentage >= 40:
            sla_status = "fair"
        else:
            sla_status = "poor"
        
        sla_data.append({
            "queue_name": row[0],
            "total_calls": total,
            "calls_within_sla": within_sla,
            "sla_percentage": sla_percentage,
            "sla_status": sla_status,
            "avg_answer_time": round(row[3] or 0, 1),
            "sla_threshold": sla_threshold
        })
    
    return {
        "period": period,
        "sla_threshold": sla_threshold,
        "queues": sla_data
    }

@router.get("/active-calls")
def get_active_calls(db: Session = Depends(get_db)):
    """
    Obtiene llamadas activas en tiempo real usando queuelog
    Detecta llamadas que entraron (ENTERQUEUE) pero no han terminado
    """
    # Buscar llamadas de las últimas 2 horas que aún no han finalizado
    two_hours_ago = datetime.now() - timedelta(hours=2)
    
    active_calls_query = text("""
        SELECT DISTINCT
            enter_log.queuename,
            enter_log.callid,
            enter_log.time as enter_time,
            connect_log.agent,
            connect_log.time as connect_time,
            TIMESTAMPDIFF(SECOND, enter_log.time, NOW()) as wait_duration
        FROM asteriskcdrdb.queuelog enter_log
        LEFT JOIN asteriskcdrdb.queuelog connect_log 
            ON enter_log.callid = connect_log.callid 
            AND connect_log.event = 'CONNECT'
        WHERE enter_log.event = 'ENTERQUEUE'
            AND enter_log.time >= :start_time
            AND enter_log.queuename != 'NONE'
            AND NOT EXISTS (
                SELECT 1 FROM asteriskcdrdb.queuelog exit_log
                WHERE exit_log.callid = enter_log.callid
                AND exit_log.event IN ('COMPLETEAGENT', 'COMPLETECALLER', 'ABANDON', 'EXITWITHTIMEOUT', 'EXITWITHKEY')
            )
        ORDER BY enter_log.time DESC
        LIMIT 100
    """)
    
    result = db.execute(active_calls_query, {"start_time": two_hours_ago}).fetchall()
    
    active_calls = []
    waiting_calls = 0
    calls_in_progress = 0
    
    for row in result:
        call_status = "waiting" if row[3] is None else "in_progress"
        
        if call_status == "waiting":
            waiting_calls += 1
        else:
            calls_in_progress += 1
        
        active_calls.append({
            "queue_name": row[0],
            "call_id": row[1],
            "enter_time": row[2].isoformat() if row[2] else None,
            "agent": row[3],
            "connect_time": row[4].isoformat() if row[4] else None,
            "wait_duration": row[5],
            "status": call_status
        })
    
    return {
        "total_active": len(active_calls),
        "waiting_calls": waiting_calls,
        "calls_in_progress": calls_in_progress,
        "calls": active_calls,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/queue-summary")
def get_queue_summary(db: Session = Depends(get_db)):
    """
    Resumen ejecutivo de todas las colas combinando métricas en tiempo real
    """
    # Métricas de hoy
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    summary_query = text("""
        SELECT 
            COUNT(DISTINCT queuename) as total_queues,
            COUNT(DISTINCT CASE WHEN event = 'ENTERQUEUE' THEN callid END) as total_calls_today,
            COUNT(DISTINCT CASE WHEN event IN ('CONNECT', 'COMPLETEAGENT', 'COMPLETECALLER') THEN callid END) as answered_today,
            COUNT(DISTINCT CASE WHEN event IN ('ABANDON', 'EXITWITHTIMEOUT') THEN callid END) as abandoned_today,
            AVG(CASE 
                WHEN event = 'CONNECT' AND data1 REGEXP '^[0-9]+$'
                THEN CAST(data1 AS DECIMAL(10,2)) 
            END) as avg_wait_today
        FROM asteriskcdrdb.queuelog
        WHERE time >= :today_start
            AND queuename != 'NONE'
    """)
    
    result = db.execute(summary_query, {"today_start": today_start}).fetchone()
    
    total_calls = result[1] or 0
    answered = result[2] or 0
    abandoned = result[3] or 0
    
    return {
        "total_queues": result[0] or 0,
        "today": {
            "total_calls": total_calls,
            "answered_calls": answered,
            "abandoned_calls": abandoned,
            "answer_rate": round((answered / total_calls * 100), 1) if total_calls > 0 else 0,
            "abandon_rate": round((abandoned / total_calls * 100), 1) if total_calls > 0 else 0,
            "avg_wait_time": round(result[4] or 0, 1)
        },
        "timestamp": datetime.now().isoformat()
    }

