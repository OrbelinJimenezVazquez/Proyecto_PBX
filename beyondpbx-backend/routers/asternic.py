# routers/asternic.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc
from database import get_db
from models import AgentActivity, AgentActivityPause, AgentActivitySession, User, AgentName, Pause, QueueName
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
import os
from typing import List, Optional

router = APIRouter(prefix="/api/asternic", tags=["Asternic"])

# Configuración de Asternic
ASTERNIC_URL = os.getenv("ASTERNIC_URL", "http://10.10.16.9/stats")
ASTERNIC_USER = os.getenv("ASTERNIC_USER", "adminbeyond")
ASTERNIC_PASS = os.getenv("ASTERNIC_PASS", "adminbeyond")

def get_asternic_auth():
    """Retorna la autenticación para Asternic"""
    return HTTPBasicAuth(ASTERNIC_USER, ASTERNIC_PASS)

@router.get("/agents/status")
def get_agents_real_time_status():
    """
    Obtiene el estado en tiempo real de todos los agentes desde Asternic
    """
    try:
        # Endpoint de Asternic para obtener estado de agentes
        # Ajusta la ruta según la versión de tu Asternic
        response = requests.get(
            f"{ASTERNIC_URL}/api/agents",
            auth=get_asternic_auth(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Procesar y normalizar la respuesta
            agents = []
            if isinstance(data, dict) and 'agents' in data:
                for agent in data['agents']:
                    agents.append({
                        'extension': agent.get('extension') or agent.get('agent'),
                        'name': agent.get('name', f"Agente {agent.get('extension')}"),
                        'queue': agent.get('queue', 'General'),
                        'status': normalize_status(agent.get('status', 'offline')),
                        'statusText': agent.get('statustext', agent.get('status', 'Offline')),
                        'pauseReason': agent.get('pausereason'),
                        'lastCall': agent.get('lastcall'),
                        'callsAnswered': int(agent.get('callsanswered', 0)),
                        'callsMissed': int(agent.get('callsmissed', 0)),
                        'avgTalkTime': int(agent.get('avgtalktime', 0)),
                        'loginTime': agent.get('logintime'),
                        'totalPauseTime': int(agent.get('pausetime', 0))
                    })
            
            return {"agents": agents}
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Error al obtener datos de Asternic: {response.text}"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"No se pudo conectar con Asternic: {str(e)}"
        )

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
# ALTERNATIVA: Si Asternic no tiene API REST
# ============================================

@router.get("/agents/from-asterisk")
def get_agents_from_asterisk_db(db: Session = Depends(get_db)):
    """
    Alternativa: Obtener agentes desde las tablas de Asterisk 
    (usando queuelog en lugar de queue_members que no existe)
    """
    from sqlalchemy import text
    
    # Como queue_members no existe, obtenemos agentes activos desde queuelog
    query = text("""
        SELECT DISTINCT
            ql.agent as extension,
            u.name as agent_name,
            ql.queuename as queue_name,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM asteriskcdrdb.queuelog ql2
                    WHERE ql2.agent = ql.agent 
                    AND ql2.event = 'CONNECT'
                    AND ql2.time > DATE_SUB(NOW(), INTERVAL 5 MINUTE)
                ) THEN 'busy'
                WHEN EXISTS (
                    SELECT 1 FROM asteriskcdrdb.queuelog ql3
                    WHERE ql3.agent = ql.agent 
                    AND ql3.event IN ('ENTERQUEUE', 'RINGNOANSWER')
                    AND ql3.time > DATE_SUB(NOW(), INTERVAL 10 MINUTE)
                ) THEN 'available'
                ELSE 'offline'
            END as status
        FROM asteriskcdrdb.queuelog ql
        LEFT JOIN asterisk.users u ON ql.agent = u.extension
        WHERE ql.agent IS NOT NULL
            AND ql.agent != 'NONE'
            AND ql.time > DATE_SUB(NOW(), INTERVAL 24 HOUR)
        GROUP BY ql.agent, ql.queuename
        ORDER BY ql.queuename, ql.agent
    """)
    
    result = db.execute(query).fetchall()
    
    agents = []
    for row in result:
        agents.append({
            'extension': row[0],
            'name': row[1] or f"Agente {row[0]}",
            'queue': row[2],
            'status': row[3],
            'statusText': get_status_text(row[3]),
            'paused': False,
            'callsAnswered': 0,
            'lastCall': None
        })
    
    return {"agents": agents}

def get_status_text(status: str) -> str:
    """Convierte status a texto legible"""
    status_map = {
        'available': 'Disponible',
        'busy': 'En llamada',
        'paused': 'En pausa',
        'ringing': 'Timbrando',
        'offline': 'Desconectado'
    }
    return status_map.get(status, status)

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
    """
    # Información básica del agente desde qstats.agentnames
    agent_info = db.query(AgentName).filter(AgentName.agent == agent_extension).first()
    
    if not agent_info:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    # Última actividad
    latest_activity = (
        db.query(AgentActivity)
        .filter(AgentActivity.agent == agent_extension)
        .order_by(desc(AgentActivity.datetime))
        .first()
    )
    
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
            SUM(CASE WHEN event LIKE '%PAUSE%' THEN lastedforseconds END) as total_pause_time
        FROM qstats.agent_activity
        WHERE agent = :agent
        AND datetime >= :today
    """)
    
    stats = db.execute(daily_stats, {"agent": agent_extension, "today": today}).fetchone()
    
    return {
        "extension": agent_extension,
        "name": agent_info.name,
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
            "totalPauseTime": stats[4] or 0
        }
    }

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