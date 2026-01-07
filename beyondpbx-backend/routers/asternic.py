
# routers/asternic.py 
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, and_, case
from database import get_db
import os
from models import (
    AgentActivity, AgentActivityPause, AgentActivitySession, 
    QueueName, QEvent, QueueLog
)
from datetime import datetime, timedelta
from typing import List, Optional

router = APIRouter(prefix="/api/asternic", tags=["Asternic"])

# Configuración de Asternic
ASTERNIC_URL = os.getenv("ASTERNIC_URL", "http://10.10.16.9/stats")
ASTERNIC_USER = os.getenv("ASTERNIC_USER", "adminbeyond")
ASTERNIC_PASS = os.getenv("ASTERNIC_PASS", "adminbeyond")

def get_asternic_auth():
    """Retorna la autenticación para Asternic"""
    return HTTPBasicAuth(ASTERNIC_USER, ASTERNIC_PASS)


@router.get("/agents/realtime-status")
def get_agents_realtime_status(db: Session = Depends(get_db)):
    """
    Obtiene estado en tiempo real de todos los agentes con información detallada
    Similar a la vista de Asternic Stats - OPTIMIZADO
    """
    try:
        # Query optimizada - sin subconsultas costosas en CDR
        query = text("""
            SELECT 
                aa.agent,
                aa.queue,
                aa.event,
                aa.data,
                aa.datetime,
                aa.lastedforseconds,
                TIMESTAMPDIFF(SECOND, aa.datetime, NOW()) as time_in_state,
                qn.queue as queue_name,
                aa.uniqueid,
                COALESCE(an.agent, CONCAT('Agente ', aa.agent)) as agent_name
            FROM qstats.agent_activity aa
            LEFT JOIN qstats.queuenames qn ON aa.queue = qn.device
            LEFT JOIN qstats.agentnames an ON aa.agent = an.device
            INNER JOIN (
                SELECT agent, MAX(id) as max_id
                FROM qstats.agent_activity 
                GROUP BY agent
            ) latest ON aa.id = latest.max_id
            ORDER BY qn.queue, aa.agent
        """)
        
        result = db.execute(query).fetchall()
        
        agents = []
        queues_dict = {}
        agent_extensions = [row[0] for row in result]
        
        # Obtener estadísticas de llamadas del día en una sola query (OPTIMIZADO)
        if agent_extensions:
            calls_query = text("""
                SELECT 
                    CASE 
                        WHEN src IN :agents THEN src
                        WHEN dst IN :agents THEN dst
                    END as agent,
                    COUNT(*) as call_count,
                    MAX(calldate) as last_call
                FROM asteriskcdrdb.cdr
                WHERE (src IN :agents OR dst IN :agents)
                AND disposition = 'ANSWERED'
                AND DATE(calldate) = CURDATE()
                GROUP BY agent
            """)
            
            calls_result = db.execute(calls_query, {"agents": tuple(agent_extensions)}).fetchall()
            calls_dict = {row[0]: {'count': row[1], 'last_call': row[2]} for row in calls_result}
        else:
            calls_dict = {}
        
        for row in result:
            event = row[2] or ''
            status = determine_status(event)
            queue_device = row[1] or 'sin_cola'
            queue_name = row[7] or 'Sin Cola'
            agent_ext = row[0]
            
            # Obtener info de llamadas del diccionario pre-cargado
            call_info = calls_dict.get(agent_ext, {'count': 0, 'last_call': None})
            
            agent_data = {
                'extension': agent_ext,
                'name': row[9],
                'queue': queue_device,
                'queueName': queue_name,
                'status': status,
                'statusText': get_status_text(status),
                'event': event,
                'lastActivity': row[4].isoformat() if row[4] else None,
                'timeInState': row[6] or 0,
                'duration': format_duration(row[6] or 0),
                'paused': 'PAUSE' in event,
                'pauseReason': row[3] if 'PAUSE' in event else None,
                'inCall': 'CONNECT' in event or 'COMPLETE' in event,
                'uniqueid': row[8],
                'callerId': row[3] if ('CONNECT' in event or 'COMPLETE' in event) else '',
                'lastCallTime': call_info['last_call'].isoformat() if call_info['last_call'] else None,
                'lastCallFormatted': format_last_call_time(call_info['last_call']) if call_info['last_call'] else 'Sin datos',
                'callsToday': call_info['count']
            }
            
            agents.append(agent_data)
            
            # Agrupar por cola
            if queue_device not in queues_dict:
                queues_dict[queue_device] = {
                    'queue': queue_device,
                    'queueName': queue_name,
                    'agents': []
                }
            queues_dict[queue_device]['agents'].append(agent_data)
        
        # Resumen por estado
        summary = {
            'total': len(agents),
            'available': sum(1 for a in agents if a['status'] == 'available'),
            'busy': sum(1 for a in agents if a['status'] == 'busy'),
            'paused': sum(1 for a in agents if a['status'] == 'paused'),
            'offline': sum(1 for a in agents if a['status'] == 'offline'),
            'ringing': sum(1 for a in agents if a['status'] == 'ringing')
        }
        
        return {
            "agents": agents,
            "queues": list(queues_dict.values()),
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error en get_agents_realtime_status: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener agentes: {str(e)}")
    

@router.get("/queues/status")
def get_queues_real_time_status():
    """
    Obtiene el estado en tiempo real de todas las colas desde Asternic
    """
    try:
        response = requests.get(
            f"{ASTERNIC_URL}/api/queues",
            auth=get_asternic_auth(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            queues = []
            if isinstance(data, dict) and 'queues' in data:
                for queue in data['queues']:
                    queues.append({
                        'name': queue.get('name'),
                        'waiting': int(queue.get('waiting', 0)),
                        'answered': int(queue.get('answered', 0)),
                        'abandoned': int(queue.get('abandoned', 0)),
                        'agentsLoggedIn': int(queue.get('agentsloggedin', 0)),
                        'agentsAvailable': int(queue.get('agentsavailable', 0)),
                        'longestWait': int(queue.get('longestwait', 0))
                    })
            
            return {"queues": queues}
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Error al obtener datos de colas"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo conectar con Asternic: {str(e)}"
        )

@router.get("/agent/{extension}/stats")
def get_agent_statistics(extension: str):
    """
    Obtiene estadísticas detalladas de un agente específico
    """
    try:
        response = requests.get(
            f"{ASTERNIC_URL}/api/agent-stats",
            auth=get_asternic_auth(),
            params={'agent': extension},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Error al obtener estadísticas del agente"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo conectar con Asternic: {str(e)}"
        )

@router.get("/dashboard/summary")
def get_realtime_dashboard_summary(db: Session = Depends(get_db)):
    """
    Combina datos de Asternic con datos de la base de datos
    para crear un resumen completo en tiempo real
    """
    try:
        # Obtener datos de agentes en tiempo real
        agents_response = requests.get(
            f"{ASTERNIC_URL}/api/agents",
            auth=get_asternic_auth(),
            timeout=10
        )
        
        # Obtener datos de colas en tiempo real
        queues_response = requests.get(
            f"{ASTERNIC_URL}/api/queues",
            auth=get_asternic_auth(),
            timeout=10
        )
        
        agents_data = agents_response.json() if agents_response.status_code == 200 else {}
        queues_data = queues_response.json() if queues_response.status_code == 200 else {}
        
        # Calcular métricas
        agents = agents_data.get('agents', [])
        total_agents = len(agents)
        available = sum(1 for a in agents if 'available' in str(a.get('status', '')).lower())
        busy = sum(1 for a in agents if 'busy' in str(a.get('status', '')).lower())
        paused = sum(1 for a in agents if 'pause' in str(a.get('status', '')).lower())
        
        queues = queues_data.get('queues', [])
        total_waiting = sum(int(q.get('waiting', 0)) for q in queues)
        
        return {
            "agents": {
                "total": total_agents,
                "available": available,
                "busy": busy,
                "paused": paused,
                "offline": total_agents - (available + busy + paused)
            },
            "queues": {
                "total_waiting": total_waiting,
                "queues": queues
            },
            "timestamp": "now"
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error al obtener resumen: {str(e)}"
        )

def normalize_status(status: str) -> str:
    """
    Normaliza el estado del agente a valores estándar
    """
    status_lower = status.lower()
    
    if any(x in status_lower for x in ['available', 'idle', 'ready', 'libre']):
        return 'available'
    elif any(x in status_lower for x in ['busy', 'incall', 'oncall', 'ocupado']):
        return 'busy'
    elif any(x in status_lower for x in ['pause', 'break', 'pausa']):
        return 'paused'
    elif 'ring' in status_lower:
        return 'ringing'
    else:
        return 'offline'

# ============================================
# ENDPOINTS NUEVOS PARA MONITOR DE AGENTES COMPLETO
# ============================================

@router.get("/agents/realtime-status")
def get_agents_realtime_status(db: Session = Depends(get_db)):
    """
    Obtiene estado en tiempo real de todos los agentes usando qstats.agent_activity
    Incluye nombres de agentes, pausas y colas desde qstats
    """
    try:
        # Obtener última actividad de cada agente - Simplificado sin JOINs complejos
        latest_activities = text("""
            SELECT 
                aa.agent,
                aa.queue,
                aa.event,
                aa.data,
                aa.datetime,
                aa.lastedforseconds,
                TIMESTAMPDIFF(SECOND, aa.datetime, NOW()) as time_in_state
            FROM qstats.agent_activity aa
            INNER JOIN (
                SELECT agent, MAX(id) as max_id
                FROM qstats.agent_activity 
                GROUP BY agent
            ) latest ON aa.id = latest.max_id
            ORDER BY aa.agent
        """)
        
        result = db.execute(latest_activities).fetchall()
        result = db.execute(latest_activities).fetchall()
        
        agents = []
        for row in result:
            # Determinar estado basado en event
            event = row[2] or ''
            status = 'offline'
            status_text = 'Desconectado'
            
            if 'CONNECT' in event or 'COMPLETEAGENT' in event:
                status = 'busy'
                status_text = 'En llamada'
            elif 'PAUSE' in event:
                status = 'paused'
                status_text = 'En pausa'
            elif 'UNPAUSE' in event or 'ADDMEMBER' in event:
                status = 'available'
                status_text = 'Disponible'
            elif 'RINGNOANSWER' in event or 'RINGCANCELED' in event:
                status = 'ringing'
                status_text = 'Timbrando'
            
            agents.append({
                'extension': row[0],
                'name': f"Agente {row[0]}",  # Nombre simple por ahora
                'queue': row[1] or 'General',
                'queueName': row[1] or 'General',
                'status': status,
                'statusText': status_text,
                'event': event,
                'lastActivity': row[4].isoformat() if row[4] else None,
                'timeInState': row[6] or 0,
                'paused': 'PAUSE' in event,
                'pauseReason': row[3] if 'PAUSE' in event else None,
                'inCall': 'CONNECT' in event
            })
        
        # Agrupar por estado para resumen
        summary = {
            'total': len(agents),
            'available': sum(1 for a in agents if a['status'] == 'available'),
            'busy': sum(1 for a in agents if a['status'] == 'busy'),
            'paused': sum(1 for a in agents if a['status'] == 'paused'),
            'offline': sum(1 for a in agents if a['status'] == 'offline'),
            'ringing': sum(1 for a in agents if a['status'] == 'ringing')
        }
        
        return {
            "agents": agents,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener agentes: {str(e)}")


@router.get("/agents/{agent_extension}/details")
def get_agent_details(agent_extension: str, db: Session = Depends(get_db)):
    """
    Obtiene detalles completos de un agente específico
    Incluye estadísticas históricas y eventos recientes
    """
    try:
        # Última actividad
        latest_activity = (
            db.query(AgentActivity)
            .filter(AgentActivity.agent == agent_extension)
            .order_by(desc(AgentActivity.datetime))
            .first()
        )
        
        if not latest_activity:
            raise HTTPException(status_code=404, detail=f"Agente '{agent_extension}' no encontrado")
        
        # Estado de pausa actual
        pause_status = (
            db.query(AgentActivityPause)
            .filter(AgentActivityPause.agent == agent_extension)
            .first()
        )
        
        # Sesión actual
        current_session = (
            db.query(AgentActivitySession)
            .filter(AgentActivitySession.agent == agent_extension)
            .first()
        )
        
        # Estadísticas del día
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_stats = text("""
            SELECT 
                COUNT(CASE WHEN event LIKE '%CONNECT%' THEN 1 END) as calls_answered,
                SUM(CASE WHEN event LIKE '%COMPLETE%' THEN lastedforseconds END) as total_talk_time,
                AVG(CASE WHEN event LIKE '%COMPLETE%' THEN lastedforseconds END) as avg_talk_time,
                COUNT(CASE WHEN event LIKE '%PAUSE%' THEN 1 END) as pause_count,
                SUM(CASE WHEN event LIKE '%PAUSE%' THEN lastedforseconds END) as total_pause_time,
                COUNT(CASE WHEN event LIKE '%RINGNOANSWER%' THEN 1 END) as missed_calls
            FROM qstats.agent_activity
            WHERE agent = :agent
            AND datetime >= :today
        """)
        
        stats = db.execute(daily_stats, {"agent": agent_extension, "today": today}).fetchone()
        
        # Estadísticas de la semana
        week_ago = datetime.now() - timedelta(days=7)
        
        weekly_stats = text("""
            SELECT 
                COUNT(CASE WHEN event LIKE '%CONNECT%' THEN 1 END) as calls_answered,
                AVG(CASE WHEN event LIKE '%COMPLETE%' THEN lastedforseconds END) as avg_talk_time,
                SUM(CASE WHEN event LIKE '%COMPLETE%' THEN lastedforseconds END) as total_talk_time
            FROM qstats.agent_activity
            WHERE agent = :agent
            AND datetime >= :week_ago
        """)
        
        week_stats = db.execute(weekly_stats, {"agent": agent_extension, "week_ago": week_ago}).fetchone()
        
        # Eventos recientes (últimas 10 actividades)
        recent_events_query = text("""
            SELECT 
                datetime,
                event,
                queue,
                data,
                lastedforseconds
            FROM qstats.agent_activity
            WHERE agent = :agent
            ORDER BY datetime DESC
            LIMIT 10
        """)
        
        recent_events_result = db.execute(recent_events_query, {"agent": agent_extension}).fetchall()
        
        recent_events = [
            {
                "datetime": row[0].isoformat() if row[0] else None,
                "event": row[1],
                "queue": row[2],
                "data": row[3],
                "duration": row[4]
            }
            for row in recent_events_result
        ]
        
        return {
            "extension": agent_extension,
            "name": agent_extension,
            "currentActivity": {
                "event": latest_activity.event if latest_activity else None,
                "queue": latest_activity.queue if latest_activity else None,
                "datetime": latest_activity.datetime.isoformat() if latest_activity else None,
                "duration": latest_activity.lastedforseconds if latest_activity else 0
            },
            "pauseStatus": {
                "isPaused": pause_status.state == 'PAUSED' if pause_status else False,
                "reason": pause_status.data if pause_status and pause_status.state == 'PAUSED' else None,
                "since": pause_status.datetime.isoformat() if pause_status else None
            },
            "session": {
                "isLoggedIn": current_session.state == 'LOGGEDIN' if current_session else False,
                "inCall": bool(current_session.incall) if current_session else False,
                "queue": current_session.queue if current_session else None,
                "sessionCount": current_session.sessioncount if current_session else 0
            },
            "dailyStats": {
                "callsAnswered": stats[0] or 0,
                "totalTalkTime": stats[1] or 0,
                "avgTalkTime": round(stats[2] or 0, 1),
                "pauseCount": stats[3] or 0,
                "totalPauseTime": stats[4] or 0,
                "missedCalls": stats[5] or 0
            },
            "weeklyStats": {
                "callsAnswered": week_stats[0] or 0,
                "avgTalkTime": round(week_stats[1] or 0, 1),
                "totalTalkTime": week_stats[2] or 0
            },
            "recentEvents": recent_events
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en get_agent_details: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener detalles del agente: {str(e)}")

@router.get("/agents/sessions")
def get_agents_sessions(db: Session = Depends(get_db)):
    """
    Obtiene todas las sesiones activas de agentes
    """
    sessions_query = text("""
        SELECT 
            ases.agent,
            u.name as agent_name,
            ases.state,
            ases.queue,
            ases.datetime,
            ases.incall,
            ases.sessioncount,
            TIMESTAMPDIFF(SECOND, ases.datetime, NOW()) as session_duration
        FROM qstats.agent_activity_session ases
        LEFT JOIN asterisk.users u ON ases.agent = u.extension
        WHERE ases.state = 'LOGGEDIN'
        ORDER BY ases.datetime DESC
    """)
    
    result = db.execute(sessions_query).fetchall()
    
    sessions = []
    for row in result:
        sessions.append({
            'agent': row[0],
            'name': row[1] or f"Agente {row[0]}",
            'state': row[2],
            'queue': row[3],
            'loginTime': row[4].isoformat() if row[4] else None,
            'inCall': bool(row[5]),
            'sessionCount': row[6],
            'sessionDuration': row[7] or 0
        })
    
    return {
        "sessions": sessions,
        "totalActive": len(sessions),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/queues/realtime-metrics")
def get_queues_realtime_metrics(db: Session = Depends(get_db)):
    """
    Obtiene métricas en tiempo real de todas las colas
    Usando queuelog y estadísticas de QStats
    """
    try:
        metrics_query = text("""
            SELECT 
                qn.queue as queue_name,
                qn.device as queue_id,
                -- Llamadas en espera (últimos 5 minutos)
                (SELECT COUNT(DISTINCT callid)
                 FROM asteriskcdrdb.queuelog ql
                 WHERE ql.queuename = qn.device
                 AND ql.event = 'ENTERQUEUE'
                 AND ql.time >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
                 AND NOT EXISTS (
                     SELECT 1 FROM asteriskcdrdb.queuelog ql2
                     WHERE ql2.callid = ql.callid
                     AND ql2.event IN ('CONNECT', 'ABANDON', 'EXITWITHTIMEOUT')
                 )
                ) as calls_waiting,
                -- Agentes logueados
                (SELECT COUNT(DISTINCT agent)
                 FROM qstats.agent_activity_session
                 WHERE queue = qn.device
                 AND state = 'LOGGEDIN'
                ) as agents_logged,
                -- Agentes disponibles
                (SELECT COUNT(DISTINCT aa.agent)
                 FROM qstats.agent_activity aa
                 INNER JOIN (
                     SELECT agent, MAX(id) as max_id
                     FROM qstats.agent_activity
                     WHERE queue = qn.device
                     GROUP BY agent
                 ) latest ON aa.id = latest.max_id
                 WHERE aa.event LIKE '%UNPAUSE%' OR aa.event LIKE '%ADDMEMBER%'
                ) as agents_available,
                -- Llamadas del día
                (SELECT COUNT(*)
                 FROM asteriskcdrdb.queuelog ql
                 WHERE ql.queuename = qn.device
                 AND ql.event = 'ENTERQUEUE'
                 AND DATE(ql.time) = CURDATE()
                ) as calls_today,
                -- Llamadas contestadas hoy
                (SELECT COUNT(DISTINCT callid)
                 FROM asteriskcdrdb.queuelog ql
                 WHERE ql.queuename = qn.device
                 AND ql.event IN ('CONNECT', 'COMPLETEAGENT', 'COMPLETECALLER')
                 AND DATE(ql.time) = CURDATE()
                ) as answered_today
            FROM qstats.queuenames qn
            ORDER BY qn.queue
        """)
        
        result = db.execute(metrics_query).fetchall()
        
        queues = []
        for row in result:
            total_today = row[5] or 0
            answered_today = row[6] or 0
            answer_rate = round((answered_today / total_today * 100), 1) if total_today > 0 else 0
            
            queues.append({
                "queueName": row[0],
                "queueId": row[1],
                "callsWaiting": row[2] or 0,
                "agentsLogged": row[3] or 0,
                "agentsAvailable": row[4] or 0,
                "callsToday": total_today,
                "answeredToday": answered_today,
                "answerRate": answer_rate
            })
        
        return {
            "queues": queues,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error en get_queues_realtime_metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener métricas: {str(e)}")

@router.get("/events/types")
def get_event_types(db: Session = Depends(get_db)):
    """
    Obtiene todos los tipos de eventos disponibles en el sistema
    """
    try:
        events = db.query(QEvent).order_by(QEvent.event_id).all()
        
        return {
            "events": [
                {
                    "id": e.event_id,
                    "name": e.event,
                    "description": get_event_description(e.event)
                }
                for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
@router.get("/agents/pauses")
def get_agents_pauses(db: Session = Depends(get_db)):
    """
    Obtiene todos los agentes en pausa con sus motivos
    """
    pauses_query = text("""
        SELECT 
            ap.agent,
            u.name as agent_name,
            ap.state,
            ap.queue,
            ap.data as pause_reason,
            ap.datetime,
            TIMESTAMPDIFF(SECOND, ap.datetime, NOW()) as pause_duration
        FROM qstats.agent_activity_pause ap
        LEFT JOIN asterisk.users u ON ap.agent = u.extension
        WHERE ap.state = 'PAUSED'
        ORDER BY ap.datetime DESC
    """)
    
    result = db.execute(pauses_query).fetchall()
    
    pauses = []
    for row in result:
        pauses.append({
            'agent': row[0],
            'name': row[1] or f"Agente {row[0]}",
            'state': row[2],
            'queue': row[3],
            'pauseReason': row[4] or 'Sin motivo',
            'pauseStart': row[5].isoformat() if row[5] else None,
            'pauseDuration': row[6] or 0
        })
    
    return {
        "pauses": pauses,
        "totalPaused": len(pauses),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/agents/activity-detailed")
def get_agents_activity_detailed(
    hours: int = 24,
    agent: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene actividad detallada de agentes con eventos específicos
    Usa las tablas qevent y agent_activity para datos precisos
    
    Parámetros:
    - hours: Horas hacia atrás para obtener datos (default: 24)
    - agent: Filtrar por agente específico (opcional)
    """
    try:
        since = datetime.now() - timedelta(hours=hours)
        
        # Query que une agent_activity con qevent para obtener nombres de eventos
        query = text("""
            SELECT 
                aa.id,
                aa.datetime,
                aa.queue,
                qn.queue as queue_name,
                aa.agent,
                aa.event as event_code,
                aa.data,
                aa.lastedforseconds,
                aa.uniqueid,
                aa.computed
            FROM qstats.agent_activity aa
            LEFT JOIN qstats.queuenames qn ON aa.queue = qn.device
            WHERE aa.datetime >= :since
            """ + (" AND aa.agent = :agent" if agent else "") + """
            ORDER BY aa.datetime DESC
            LIMIT 500
        """)
        
        params = {"since": since}
        if agent:
            params["agent"] = agent
        
        result = db.execute(query, params).fetchall()
        
        activities = []
        for row in result:
            activities.append({
                "id": row[0],
                "timestamp": row[1].isoformat() if row[1] else None,
                "queue": row[2],
                "queue_name": row[3] or row[2],
                "agent": row[4],
                "event": row[5],
                "event_description": get_event_description(row[5]),
                "data": row[6],
                "duration": row[7],
                "uniqueid": row[8],
                "computed": row[9]
            })
        
        # Agrupar por agente para estadísticas
        agent_stats = {}
        for activity in activities:
            agent_id = activity["agent"]
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "agent": agent_id,
                    "total_activities": 0,
                    "events": {},
                    "total_duration": 0
                }
            
            agent_stats[agent_id]["total_activities"] += 1
            
            event = activity["event"]
            if event not in agent_stats[agent_id]["events"]:
                agent_stats[agent_id]["events"][event] = 0
            agent_stats[agent_id]["events"][event] += 1
            
            if activity["duration"]:
                agent_stats[agent_id]["total_duration"] += activity["duration"]
        
        return {
            "activities": activities,
            "agent_summaries": list(agent_stats.values()),
            "total_activities": len(activities),
            "period": f"Last {hours} hours",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error en get_agents_activity_detailed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener actividad: {str(e)}")


@router.get("/events/types")
def get_all_event_types(db: Session = Depends(get_db)):
    """
    Obtiene todos los tipos de eventos registrados en qevent
    """
    try:
        events = db.query(QEvent).order_by(QEvent.event_id).all()
        
        event_list = []
        for event in events:
            event_list.append({
                "id": event.event_id,
                "code": event.event,
                "description": get_event_description(event.event)
            })
        
        return {
            "events": event_list,
            "total": len(event_list),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error en get_all_event_types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener tipos de eventos: {str(e)}")


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def determine_status(event: str) -> str:
    """Determina el estado del agente basado en el evento"""
    if not event:
        return 'offline'
    
    event_upper = event.upper()
    
    if 'CONNECT' in event_upper or 'COMPLETEAGENT' in event_upper:
        return 'busy'
    elif 'PAUSE' in event_upper:
        return 'paused'
    elif 'UNPAUSE' in event_upper or 'ADDMEMBER' in event_upper:
        return 'available'
    elif 'RINGNOANSWER' in event_upper or 'RINGCANCELED' in event_upper:
        return 'ringing'
    else:
        return 'offline'

def get_status_text(status: str) -> str:
    """Convierte status a texto legible en español"""
    status_map = {
        'available': 'Disponible',
        'busy': 'En llamada',
        'paused': 'En pausa',
        'ringing': 'Timbrando',
        'offline': 'Desconectado'
    }
    return status_map.get(status, status)

def get_event_description(event: str) -> str:
    """Devuelve descripción del evento"""
    descriptions = {
        'ABANDON': 'Llamada abandonada',
        'ADDMEMBER': 'Agente agregado a cola',
        'CONNECT': 'Llamada conectada',
        'COMPLETEAGENT': 'Llamada finalizada por agente',
        'COMPLETECALLER': 'Llamada finalizada por cliente',
        'ENTERQUEUE': 'Llamada entra a cola',
        'EXITWITHTIMEOUT': 'Salida por timeout',
        'PAUSE': 'Agente en pausa',
        'UNPAUSE': 'Agente disponible',
        'RINGNOANSWER': 'Llamada no contestada',
        'RINGCANCELED': 'Llamada cancelada',
        'AGENTLOGIN': 'Agente conectado',
        'AGENTLOGOFF': 'Agente desconectado'
    }
    return descriptions.get(event, event or 'Desconocido')

def format_duration(seconds: int) -> str:
    """Formatea duración en formato HH:MM:SS"""
    if not seconds or seconds < 0:
        return '00:00:00'
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_last_call_time(call_time: datetime) -> str:
    """Formatea el tiempo de la última llamada de forma legible"""
    if not call_time:
        return 'Sin datos'
    
    now = datetime.now()
    diff = now - call_time
    
    if diff.days > 0:
        if diff.days == 1:
            return 'hace un día'
        elif diff.days < 7:
            return f'hace {diff.days} días'
        elif diff.days < 30:
            weeks = diff.days // 7
            return f'hace {weeks} {"semana" if weeks == 1 else "semanas"}'
        else:
            return f'hace {diff.days} días'
    
    hours = diff.seconds // 3600
    if hours > 0:
        if hours == 1:
            return 'hace una hora'
        else:
            return f'hace {hours} horas'
    
    minutes = (diff.seconds % 3600) // 60
    if minutes > 0:
        return f'hace {minutes} minutos'
    
    return 'hace un momento'