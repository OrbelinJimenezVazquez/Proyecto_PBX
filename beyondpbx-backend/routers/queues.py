# routers/queues.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from database import get_db
from models import QueueName, QueueStats, SQLRealtime, QEvent, QueueLog, Queue, QueueMember
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio padre al path para importar utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.php_parser import parse_sqlrealtime_data

router = APIRouter(prefix="/api/queues", tags=["queues"])

# Schemas
class QueueBase(BaseModel):
    queue: str

class QueueCreate(QueueBase):
    pass

class QueueUpdate(QueueBase):
    pass

class QueueResponse(QueueBase):
    device: str

    class Config:
        from_attributes = True

# CRUD Endpoints
@router.get("")
def get_queues(db: Session = Depends(get_db)):
    """Obtener todas las colas"""
    try:
        queues = db.query(QueueName).order_by(QueueName.device).all()
        
        # IMPORTANTE: Devolver lista directa para que funcione con el frontend
        queues_list = [
            {
                "device": q.device,
                "queue": q.queue
            }
            for q in queues
        ]
        
        # Devolver en formato directo que ya está manejando el frontend
        return queues_list
        
    except Exception as e:
        print(f"Error en get_queues: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=f"Error al obtener colas: {str(e)}")

@router.get("/{queue_id}", response_model=QueueResponse)
def get_queue(queue_id: str, db: Session = Depends(get_db)):
    """Obtener una cola por device ID"""
    queue = db.query(QueueName).filter(QueueName.device == queue_id).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Cola no encontrada")
    return queue

@router.post("", status_code=201)
def create_queue(queue_data: QueueCreate, db: Session = Depends(get_db)):
    """Crear una nueva cola"""
    try:
        print(f"📥 Recibiendo solicitud para crear cola: {queue_data.queue}")
        
        # Verificar si ya existe una cola con el mismo nombre
        existing = db.query(QueueName).filter(
            QueueName.queue == queue_data.queue
        ).first()
        
        if existing:
            print(f"⚠️ Cola duplicada: {queue_data.queue}")
            raise HTTPException(
                status_code=400, 
                detail="Ya existe una cola con ese nombre"
            )
        
        # Obtener el siguiente device ID disponible
        print("🔍 Buscando último device ID...")
        max_device_query = db.query(QueueName).order_by(QueueName.device.desc()).first()
        
        if max_device_query and max_device_query.device:
            print(f"📌 Último device encontrado: {max_device_query.device}")
            try:
                # Intentar convertir a int y sumar 1
                next_device_num = int(max_device_query.device) + 1
                next_device = str(next_device_num)
                print(f"✅ Nuevo device ID: {next_device}")
            except ValueError:
                # Si no es numérico, buscar el mayor número
                print("⚠️ Device ID no numérico, buscando alternativa...")
                all_devices = db.query(QueueName.device).all()
                numeric_devices = []
                for d in all_devices:
                    try:
                        numeric_devices.append(int(d[0]))
                    except:
                        continue
                
                if numeric_devices:
                    next_device = str(max(numeric_devices) + 1)
                else:
                    next_device = "100"  # Empezar desde 100 si no hay numéricos
                print(f"✅ Nuevo device ID (alternativo): {next_device}")
        else:
            next_device = "1"
            print(f"✅ Primera cola, device ID: {next_device}")
        
        # Crear nueva cola
        print(f"💾 Creando cola en BD: device={next_device}, queue={queue_data.queue}")
        new_queue = QueueName(
            device=next_device,
            queue=queue_data.queue
        )
        
        db.add(new_queue)
        db.commit()
        db.refresh(new_queue)
        
        print(f"✅ Cola creada exitosamente: {new_queue.device} - {new_queue.queue}")
        
        # Devolver en formato simple
        return {
            "device": new_queue.device,
            "queue": new_queue.queue,
            "message": "Cola creada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error en create_queue: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al crear cola: {str(e)}")

@router.put("/{queue_id}", response_model=QueueResponse)
def update_queue(queue_id: str, queue_data: QueueUpdate, db: Session = Depends(get_db)):
    """Actualizar una cola existente"""
    try:
        # Buscar la cola
        queue = db.query(QueueName).filter(QueueName.device == queue_id).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Cola no encontrada")
        
        # Verificar si el nuevo nombre ya existe en otra cola
        existing = db.query(QueueName).filter(
            QueueName.device != queue_id,
            QueueName.queue == queue_data.queue
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe otra cola con ese nombre"
            )
        
        # Actualizar campos
        queue.queue = queue_data.queue
        
        db.commit()
        db.refresh(queue)
        
        return queue
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error en update_queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar cola: {str(e)}")

@router.delete("/{queue_id}")
def delete_queue(queue_id: str, db: Session = Depends(get_db)):
    """Eliminar una cola"""
    try:
        queue = db.query(QueueName).filter(QueueName.device == queue_id).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Cola no encontrada")
        
        db.delete(queue)
        db.commit()
        
        return {"message": "Cola eliminada exitosamente", "id": queue_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error en delete_queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar cola: {str(e)}")


# ============================================================================
# ENDPOINTS DE MONITOREO Y ESTADÍSTICAS
# ============================================================================

@router.get("/stats/realtime")
def get_queues_realtime_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas en tiempo real de todas las colas
    usando datos de sqlrealtime (datos parseados de PHP)
    """
    try:
        # Obtener todos los registros de sqlrealtime
        realtime_records = db.query(SQLRealtime).all()
        
        queues_stats = []
        
        for record in realtime_records:
            # Parsear datos PHP serializados
            metrics = parse_sqlrealtime_data(record.data)
            
            if metrics:
                queues_stats.append({
                    "session_id": record.user,
                    "last_update": record.lastupdate.isoformat() if record.lastupdate else None,
                    "metrics": metrics
                })
        
        # Calcular totales globales
        total_metrics = calculate_global_metrics(queues_stats)
        
        return {
            "queues": queues_stats,
            "totals": total_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error en get_queues_realtime_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get("/stats/summary")
def get_queues_summary(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Obtiene resumen de estadísticas de colas usando queue_stats
    Parámetros:
    - hours: Horas hacia atrás para calcular estadísticas (default: 24)
    """
    try:
        since = datetime.now() - timedelta(hours=hours)
        
        # Query para obtener estadísticas desde queue_stats
        query = text("""
            SELECT 
                DATE(qs.datetime) as date,
                COUNT(DISTINCT qs.uniqued) as total_calls,
                COUNT(CASE WHEN qe.event = 'CONNECT' THEN 1 END) as answered_calls,
                COUNT(CASE WHEN qe.event = 'ABANDON' THEN 1 END) as abandoned_calls,
                COUNT(CASE WHEN qe.event = 'EXITWITHTIMEOUT' THEN 1 END) as timeout_calls,
                AVG(CASE WHEN qe.event = 'CONNECT' THEN CAST(qs.info1 AS UNSIGNED) END) as avg_wait_time,
                MAX(CASE WHEN qe.event = 'CONNECT' THEN CAST(qs.info1 AS UNSIGNED) END) as max_wait_time
            FROM qstats.queue_stats qs
            LEFT JOIN qstats.qevent qe ON qs.gevent = qe.event_id
            WHERE qs.datetime >= :since
            GROUP BY DATE(qs.datetime)
            ORDER BY date DESC
        """)
        
        result = db.execute(query, {"since": since}).fetchall()
        
        daily_stats = []
        for row in result:
            daily_stats.append({
                "date": row[0].isoformat() if row[0] else None,
                "total_calls": row[1] or 0,
                "answered_calls": row[2] or 0,
                "abandoned_calls": row[3] or 0,
                "timeout_calls": row[4] or 0,
                "avg_wait_time": round(row[5], 2) if row[5] else 0,
                "max_wait_time": row[6] or 0
            })
        
        return {
            "period": f"Last {hours} hours",
            "daily_stats": daily_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error en get_queues_summary: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")


@router.get("/events")
def get_queue_events(
    limit: int = 100,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene eventos recientes de colas
    Parámetros:
    - limit: Número máximo de eventos a retornar
    - event_type: Filtrar por tipo de evento (CONNECT, ABANDON, etc.)
    """
    try:
        query = text("""
            SELECT 
                ql.time,
                ql.callid,
                ql.queuename,
                qn.queue as queue_display_name,
                ql.agent,
                ql.event,
                ql.data1,
                ql.data2,
                ql.data3
            FROM asteriskcdrdb.queuelog ql
            LEFT JOIN qstats.queuenames qn ON ql.queuename = qn.device
            WHERE 1=1
            """ + (f" AND ql.event = :event_type" if event_type else "") + """
            ORDER BY ql.time DESC
            LIMIT :limit
        """)
        
        params = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        
        result = db.execute(query, params).fetchall()
        
        events = []
        for row in result:
            events.append({
                "timestamp": row[0].isoformat() if row[0] else None,
                "call_id": row[1],
                "queue": row[2],
                "queue_name": row[3] or row[2],
                "agent": row[4],
                "event": row[5],
                "data": {
                    "data1": row[6],
                    "data2": row[7],
                    "data3": row[8]
                }
            })
        
        return {
            "events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error en get_queue_events: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos: {str(e)}")


@router.get("/{queue_id}/members")
def get_queue_members(queue_id: str, db: Session = Depends(get_db)):
    """
    Obtiene miembros (agentes) de una cola específica
    """
    try:
        # Buscar cola
        queue = db.query(QueueName).filter(QueueName.device == queue_id).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Cola no encontrada")
        
        # Obtener miembros de la cola
        members = db.query(QueueMember).filter(
            QueueMember.queue_name == queue.queue
        ).all()
        
        members_list = []
        for member in members:
            members_list.append({
                "id": member.uniqueid,
                "name": member.membername,
                "interface": member.interface,
                "penalty": member.penalty,
                "paused": bool(member.paused),
                "state_interface": member.state_interface
            })
        
        return {
            "queue_id": queue_id,
            "queue_name": queue.queue,
            "members": members_list,
            "total_members": len(members_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en get_queue_members: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener miembros: {str(e)}")


@router.get("/types/events")
def get_event_types(db: Session = Depends(get_db)):
    """
    Obtiene catálogo de tipos de eventos disponibles
    """
    try:
        events = db.query(QEvent).order_by(QEvent.event_id).all()
        
        event_list = []
        for event in events:
            event_list.append({
                "id": event.event_id,
                "name": event.event,
                "description": get_event_description(event.event)
            })
        
        return {
            "events": event_list,
            "total": len(event_list)
        }
        
    except Exception as e:
        print(f"Error en get_event_types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener tipos de eventos: {str(e)}")


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calculate_global_metrics(queues_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula métricas globales sumando todas las colas
    """
    totals = {
        "calls": {
            "received": 0,
            "answered": 0,
            "abandoned": 0,
            "unanswered": 0
        },
        "times": {
            "avg_wait": 0,
            "avg_talk": 0
        },
        "sla": {
            "percentage": 0
        }
    }
    
    total_received = 0
    total_answered_sla = 0
    
    for queue in queues_stats:
        metrics = queue.get("metrics", {})
        calls = metrics.get("calls", {})
        
        totals["calls"]["received"] += calls.get("received", 0)
        totals["calls"]["answered"] += calls.get("answered", 0)
        totals["calls"]["abandoned"] += calls.get("abandoned", 0)
        totals["calls"]["unanswered"] += calls.get("unanswered", 0)
        
        total_received += calls.get("received", 0)
        total_answered_sla += calls.get("answered_sla", 0)
    
    # Calcular SLA global
    if total_received > 0:
        totals["sla"]["percentage"] = round((total_answered_sla / total_received) * 100, 2)
    
    return totals


def get_event_description(event_name: Optional[str]) -> str:
    """
    Retorna descripción legible de un evento
    """
    descriptions = {
        "ABANDON": "Llamada abandonada por el cliente",
        "ADDMEMBER": "Agente agregado a la cola",
        "AGENTCALLBACKLOGIN": "Agente inició sesión (callback)",
        "AGENTCALLBACKLOGOFF": "Agente cerró sesión (callback)",
        "AGENTDUMP": "Llamada descartada por el agente",
        "AGENTLOGIN": "Agente inició sesión",
        "AGENTLOGOFF": "Agente cerró sesión",
        "AGENTPAUSED": "Agente se pausó (obsoleto)",
        "COMPLETEAGENT": "Llamada completada por agente",
        "COMPLETECALLER": "Llamada completada por cliente",
        "CONFIGRELOAD": "Configuración recargada",
        "CONNECT": "Llamada conectada con agente",
        "CONNECTED": "Llamada conectada (event similar a CONNECT)",
        "DID": "Número marcado (DID)",
        "ENTERQUEUE": "Cliente entró a la cola",
        "EXITEMPTY": "Cliente salió por cola vacía",
        "EXITWITHKEY": "Cliente salió presionando tecla",
        "EXITWITHTIMEOUT": "Cliente salió por timeout",
        "NONE": "Sin evento específico",
        "PAUSE": "Agente en pausa",
        "PAUSEALL": "Todos los agentes pausados",
        "PAUSECUSTOM": "Pausa personalizada",
        "QUEUESTART": "Cola iniciada",
        "REMOVEMEMBER": "Agente removido de cola",
        "RINGNOANSWER": "Timbre sin respuesta",
        "TRANSFER": "Llamada transferida",
        "UNPAUSE": "Agente salió de pausa",
        "UNPAUSEALL": "Todos los agentes salieron de pausa",
        "RINGCANCELED": "Timbre cancelado"
    }
    
    return descriptions.get(event_name, "Evento desconocido") if event_name else "N/A"