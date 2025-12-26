from fastapi import APIRouter, Depends, Query 
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from datetime import datetime, timedelta

# Definición del router
router = APIRouter(prefix="/api", tags=["Telephony"])

# Endpoint para Obtener lista de extensiones con su estado
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
# Endpoint para Obtener lista de llamadas detalladas
@router.get("/calls/detailed")
def get_detailed_calls(
    period: str = Query("month", enum=["today", "week", "month", "year"]),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),  # máximo 200 por página
    db: Session = Depends(get_db)
):
    now = datetime.now()
    
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=365)

    offset = (page - 1) * size

    # Contar total
    count_query = text("""
        SELECT COUNT(*)
        FROM asteriskcdrdb.cdr c
        WHERE c.calldate >= :start_date
    """)
    total = db.execute(count_query, {"start_date": start_date}).scalar()

    # Obtener datos detallados con paginación
    data_query = text("""
        SELECT 
            c.calldate,
            c.src,
            c.dst,
            c.disposition,
            c.billsec,
            c.duration,
            c.uniqueid,
            c.recordingfile,
            c.did,
            u.name as agent_name
        FROM asteriskcdrdb.cdr c
        LEFT JOIN asterisk.users u ON c.dst = u.extension
        WHERE c.calldate >= :start_date
        ORDER BY c.calldate DESC
        LIMIT :size OFFSET :offset
    """)
    
    result = db.execute(data_query, {
        "start_date": start_date,
        "size": size,
        "offset": offset
    }).fetchall()
    
    calls = []
    for row in result:
        calls.append({
            "fecha": row[0],
            "numero": row[1],
            "numero_agente": row[2],
            "agente": row[9] or row[2],
            "evento": row[3],
            "tiempo_llamada": row[4] or 0,
            "tiempo_espera": max(0, (row[5] or 0) - (row[4] or 0)),
            "uniqueid": row[6],
            "grabacion": row[7],
            "did": row[8],
            "cola": "Sí" if row[2] and not row[2].isdigit() and len(row[2]) > 3 else "No"
        })
    
    return {
        "items": calls,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size  # redondeo hacia arriba
    }

# Endpoint para Obtener lista de troncales
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

# Este es el endpoint para Obtener estadísticas para el dashboard 
@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Llamadas hoy
    today_calls = db.execute(text("""
        SELECT COUNT(*), AVG(duration), 
               SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END)
        FROM asteriskcdrdb.cdr 
        WHERE calldate >= :start_date
    """), {"start_date": start_of_day}).fetchone()

    # Llamadas este mes
    month_calls = db.execute(text("""
        SELECT COUNT(*)
        FROM asteriskcdrdb.cdr 
        WHERE calldate >= :start_date
    """), {"start_date": start_of_month}).fetchone()

    # Extensiones activas (online)
    active_extensions = db.execute(text("""
        SELECT COUNT(*)
        FROM asterisk.users u
        LEFT JOIN asterisk.sip s_host 
          ON u.extension = s_host.id AND s_host.keyword = 'host'
        WHERE s_host.data IS NOT NULL 
          AND (s_host.data = 'dynamic' OR s_host.data REGEXP '^[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}$')
    """)).fetchone()

    total_calls_today = today_calls[0] or 0
    avg_duration = round(today_calls[1] or 0, 1)
    answered_calls = today_calls[2] or 0
    answer_rate = round((answered_calls / total_calls_today * 100), 1) if total_calls_today > 0 else 0

    return {
        "calls_today": total_calls_today,
        "calls_this_month": month_calls[0] or 0,
        "avg_duration": avg_duration,
        "answer_rate": answer_rate,
        "active_extensions": active_extensions[0] or 0
    }

# Endpoint para Obtener lista de IVRs con sus opciones y estadísticas
@router.get("/ivrs")
def get_ivrs_with_stats(db: Session = Depends(get_db)):
    # 1. Obtener todos los IVRs (de ivr_details)
    ivrs_query = text("""
        SELECT id, name, announcement
        FROM asterisk.ivr_details
        ORDER BY name
    """)
    ivrs = db.execute(ivrs_query).fetchall()
    
    result = []
    
    for ivr in ivrs:
        ivr_id = ivr[0]
        ivr_name = ivr[1] or f"IVR_{ivr_id}"
        announcement_id = ivr[2]  # Esto es un ID de recording, no el nombre del archivo
        
        # 2. Obtener opciones del IVR (de ivr_entries)
        options_query = text("""
            SELECT selection, dest
            FROM asterisk.ivr_entries
            WHERE ivr_id = :ivr_id
            ORDER BY selection
        """)
        options = db.execute(options_query, {"ivr_id": ivr_id}).fetchall()
        
        options_list = []
        for opt in options:
            selection = opt[0]  # La tecla que se presiona
            dest = opt[1]       # El destino (formato: '["extension","101"]' o similar)
            
            # 3. Parsear el destino (FreePBX guarda como JSON-like string)
            dest_label = "Desconocido"
            dest_type = "unknown"
            
            if dest:
                try:
                    # FreePBX usa formato: ["type","data"]
                    if dest.startswith('["') and dest.endswith('"]'):
                        parts = dest.strip('[]').replace('"', '').split(',', 1)
                        if len(parts) == 2:
                            dest_type_raw = parts[0]
                            dest_data = parts[1]
                            
                            # Mapear tipos comunes
                            if dest_type_raw == "extension":
                                dest_label = f"Extensión → {dest_data}"
                                dest_type = "extension"
                            elif dest_type_raw == "queue":
                                dest_label = f"Cola → {dest_data}"
                                dest_type = "queue"
                            elif dest_type_raw == "ivr":
                                dest_label = f"IVR → {dest_data}"
                                dest_type = "ivr"
                            elif dest_type_raw == "hangup":
                                dest_label = "Colgar"
                                dest_type = "hangup"
                            else:
                                dest_label = f"{dest_type_raw} → {dest_data}"
                                dest_type = dest_type_raw
                        else:
                            dest_label = dest
                    else:
                        dest_label = dest
                except Exception as e:
                    dest_label = f"Error: {str(e)}"
            
            # 4. Obtener estadísticas (asumiendo que dst en cdr es "ivr_name-selection")
            stats_count = 0
            try:
                stats_query = text("""
                    SELECT COUNT(*)
                    FROM asteriskcdrdb.cdr
                    WHERE dst = :ivr_option
                    AND calldate >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                """)
                stats_result = db.execute(stats_query, {
                    "ivr_option": f"{ivr_name}-{selection}"
                }).fetchone()
                stats_count = stats_result[0] if stats_result else 0
            except:
                stats_count = 0  # Si falla, sigue sin estadísticas
            
            options_list.append({
                "option": selection,
                "dest_type": dest_type,
                "dest_label": dest_label,
                "calls_last_30_days": stats_count
            })
        
        result.append({
            "id": ivr_id,
            "name": ivr_name,
            "announcement_id": announcement_id,
            "options": options_list
        })
    
    return result