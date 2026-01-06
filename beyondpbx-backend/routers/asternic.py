# routers/asternic.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
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
    Alternativa: Obtener estado de agentes directamente desde 
    las tablas de Asterisk (queue_members, queue_log)
    """
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            qm.membername as extension,
            u.name as agent_name,
            qm.queue_name,
            qm.paused,
            qm.penalty,
            qm.calls_taken,
            qm.last_call,
            CASE 
                WHEN qm.paused = 1 THEN 'paused'
                WHEN EXISTS (
                    SELECT 1 FROM asterisk.queue_log ql 
                    WHERE ql.agent = qm.membername 
                    AND ql.event = 'CONNECT'
                    AND ql.time > UNIX_TIMESTAMP(NOW() - INTERVAL 5 MINUTE)
                ) THEN 'busy'
                ELSE 'available'
            END as status
        FROM asterisk.queue_members qm
        LEFT JOIN asterisk.users u ON qm.membername = u.extension
        WHERE qm.interface LIKE 'Local/%'
        ORDER BY qm.queue_name, qm.membername
    """)
    
    result = db.execute(query).fetchall()
    
    agents = []
    for row in result:
        agents.append({
            'extension': row[0],
            'name': row[1] or f"Agente {row[0]}",
            'queue': row[2],
            'status': row[7],
            'statusText': get_status_text(row[7]),
            'paused': bool(row[3]),
            'callsAnswered': row[5] or 0,
            'lastCall': row[6]
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