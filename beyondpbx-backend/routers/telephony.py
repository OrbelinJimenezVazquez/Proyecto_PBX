from fastapi import APIRouter, Depends, HTTPException, Query 
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



# Endpoint para Obtener estadísticas avanzadas para el dashboard
@router.get("/dashboard/advanced-stats")
def get_advanced_dashboard_stats(db: Session = Depends(get_db)):
    now = datetime.now()
    
    # Fechas
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Métricas generales
    today_stats = db.execute(text("""
        SELECT 
            COUNT(*), 
            AVG(duration), 
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END),
            SUM(CASE WHEN disposition = 'NO ANSWER' THEN 1 ELSE 0 END),
            SUM(CASE WHEN disposition = 'FAILED' THEN 1 ELSE 0 END)
        FROM asteriskcdrdb.cdr 
        WHERE calldate >= :start_date
    """), {"start_date": today_start}).fetchone()
    
    week_stats = db.execute(text("""
        SELECT 
            COUNT(*),
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END)
        FROM asteriskcdrdb.cdr 
        WHERE calldate >= :start_date
    """), {"start_date": week_start}).fetchone()
    
    month_stats = db.execute(text("""
        SELECT 
            COUNT(*),
            AVG(duration),
            AVG(duration - billsec) as avg_wait_time
        FROM asteriskcdrdb.cdr 
        WHERE calldate >= :start_date
    """), {"start_date": month_start}).fetchone()
    
    # 2. Llamadas contestadas vs no contestadas (últimos 7 días)
    answered_stats = db.execute(text("""
        SELECT 
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered,
            SUM(CASE WHEN disposition = 'NO ANSWER' THEN 1 ELSE 0 END) as no_answer,
            SUM(CASE WHEN disposition = 'FAILED' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN disposition = 'BUSY' THEN 1 ELSE 0 END) as busy
        FROM asteriskcdrdb.cdr
        WHERE calldate >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)).fetchone()
    
    # 3. Tiempos de espera promedio por extensión (últimos 7 días)
    wait_time_stats = db.execute(text("""
        SELECT 
            dst as extension,
            COUNT(*) as total_calls,
            AVG(duration - billsec) as avg_wait_time
        FROM asteriskcdrdb.cdr
        WHERE calldate >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND duration > billsec
        GROUP BY dst
        ORDER BY avg_wait_time DESC
        LIMIT 10
    """)).fetchall()
    
    wait_data = [
        {
            "extension": r[0],
            "avg_wait_time": round(r[2] or 0, 1),
            "total_calls": r[1]
        }
        for r in wait_time_stats
    ]
    
    # 4. Top agentes por llamadas contestadas
    agent_stats = db.execute(text("""
        SELECT 
            dst as extension,
            u.name as agent_name,
            COUNT(*) as total_calls,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered_calls
        FROM asteriskcdrdb.cdr c
        LEFT JOIN asterisk.users u ON c.dst = u.extension
        WHERE calldate >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY dst
        HAVING answered_calls > 0
        ORDER BY answered_calls DESC
        LIMIT 10
    """)).fetchall()
    
    agent_data = [
        {
            "extension": r[0],
            "name": r[1] or r[0],
            "total_calls": r[2],
            "answered_calls": r[3]
        }
        for r in agent_stats
    ]
    
    # 5. Tendencia de llamadas por día
    daily_trend = db.execute(text("""
        SELECT 
            DATE(calldate) as date,
            COUNT(*) as total,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered
        FROM asteriskcdrdb.cdr
        WHERE calldate >= DATE_SUB(NOW(), INTERVAL 14 DAY)
        GROUP BY DATE(calldate)
        ORDER BY date
    """)).fetchall()
    
    daily_data = [
        {
            "date": r[0].strftime('%Y-%m-%d'),
            "total": r[1],
            "answered": r[2] or 0
        }
        for r in daily_trend
    ]
    
    # 6. Distribución por tipo de destino
    dest_distribution = db.execute(text("""
        SELECT 
            CASE 
                WHEN dst REGEXP '^[0-9]{3,4}$' THEN 'Extensión'
                WHEN dst LIKE '%queue%' THEN 'Cola'
                WHEN dst LIKE '%ivr%' THEN 'IVR'
                WHEN dst LIKE '%s%' THEN 'Entrada'
                ELSE 'Otro'
            END as destination_type,
            COUNT(*) as calls
        FROM asteriskcdrdb.cdr
        WHERE calldate >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY destination_type
        ORDER BY calls DESC
    """)).fetchall()
    
    dest_data = [
        {
            "type": r[0],
            "calls": r[1]
        }
        for r in dest_distribution
    ]
    
    # Extensiones activas
    active_extensions = db.execute(text("""
        SELECT COUNT(*)
        FROM asterisk.users u
        LEFT JOIN asterisk.sip s_host 
          ON u.extension = s_host.id AND s_host.keyword = 'host'
        WHERE s_host.data IS NOT NULL 
          AND (s_host.data = 'dynamic' OR s_host.data REGEXP '^[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}\\\\.[0-9]{1,3}$')
    """)).fetchone()
    
    return {
        "general": {
            "calls_today": today_stats[0] or 0,
            "calls_this_week": week_stats[0] or 0,
            "calls_this_month": month_stats[0] or 0,
            "avg_duration": round(today_stats[1] or 0, 1),
            "answered_calls_today": today_stats[2] or 0,
            "no_answer_calls_today": today_stats[3] or 0,
            "failed_calls_today": today_stats[4] or 0,
            "answer_rate": round(((today_stats[2] or 0) / (today_stats[0] or 1) * 100), 1),
            "active_extensions": active_extensions[0] or 0
        },
        "call_status": {
            "answered": answered_stats[0] or 0,
            "no_answer": answered_stats[1] or 0,
            "failed": answered_stats[2] or 0,
            "busy": answered_stats[3] or 0
        },
        "wait_times": wait_data,
        "top_agents": agent_data,
        "daily_trends": daily_data,
        "destination_distribution": dest_data
    }

# Endpoint para Obtener datos para gráficos avanzados del dashboard
@router.get("/dashboard/advanced-charts")
def get_advanced_charts_data(db: Session = Depends(get_db)):
    now = datetime.now()
    
    # 1. Heatmap: llamadas por hora y día de la semana
    heatmap_query = text("""
        SELECT 
            HOUR(calldate) as hour,
            DAYOFWEEK(calldate) as day_of_week,
            COUNT(*) as calls
        FROM asteriskcdrdb.cdr
        WHERE calldate >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY HOUR(calldate), DAYOFWEEK(calldate)
    """)
    heatmap_data = db.execute(heatmap_query).fetchall()
    
    # Convertir a formato para heatmap (Chart.js necesita arrays)
    hours = list(range(24))  # 0-23
    days = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
    
    # Crear matriz de datos
    matrix_data = []
    for hour in hours:
        for day_idx, day_name in enumerate(days):
            # Buscar si hay datos para esta combinación
            value = 0
            for row in heatmap_data:
                if row[0] == hour and row[1] == (day_idx + 1):  # DAYOFWEEK es 1-7
                    value = row[2]
                    break
            matrix_data.append({
                'x': hour,
                'y': day_name,
                'v': value
            })
    
    # 2. Comparativas mes vs mes (últimos 6 meses)
    monthly_comparison = db.execute(text("""
        SELECT 
            DATE_FORMAT(calldate, '%Y-%m') as month,
            COUNT(*) as total_calls,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered_calls,
            AVG(duration) as avg_duration
        FROM asteriskcdrdb.cdr
        WHERE calldate >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(calldate, '%Y-%m')
        ORDER BY month
    """)).fetchall()
    
    monthly_data = [
        {
            "month": row[0],
            "total_calls": row[1],
            "answered_calls": row[2] or 0,
            "avg_duration": round(row[3] or 0, 1)
        }
        for row in monthly_comparison
    ]
    
    return {
        "heatmap": matrix_data,
        "monthly_comparison": monthly_data
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

# Endpoint para Obtener lista de rutas entrantes con detalles y estadísticas
@router.get("/incoming-routes")
def list_incoming_routes(db: Session = Depends(get_db)):
    query = text(
        """
        SELECT 
            cidnum,
            extension,
            destination,
            description,
            alertinfo
        FROM asterisk.incoming
        ORDER BY cidnum
        """
    )

    routes = []
    for row in db.execute(query).fetchall():
        cidnum = row[0]
        extension = row[1]
        destination = row[2] or ""
        description = row[3]
        alertinfo = row[4]

        dest_type = "desconocido"
        dest_data = destination
        dest_label = destination

        if destination:
            parts = destination.split('/', 1)
            if len(parts) == 2:
                dest_type = parts[0]
                dest_data = parts[1]

                if dest_type == "from-did-direct":
                    dest_label = f"Extensión → {dest_data}"
                elif dest_type == "app-ivr":
                    dest_label = f"IVR → {dest_data}"
                elif dest_type == "app-queue":
                    dest_label = f"Cola → {dest_data}"
                else:
                    dest_label = f"{dest_type} → {dest_data}"

        routes.append(
            {
                "numero": cidnum,
                "extension": extension,
                "destino_tipo": dest_type,
                "destino_dato": dest_data,
                "destino_label": dest_label,
                "descripcion": description,
                "alertinfo": alertinfo,
            }
        )

    return routes

# Endpoint para Obtener detalle de una ruta entrante específica
@router.get("/incoming-routes/{route_number}")
def get_incoming_route_detail(route_number: str, db: Session = Depends(get_db)):
    # 1. Obtener información básica de la ruta
    route_query = text("""
        SELECT 
            cidnum,
            extension,
            destination,
            description,
            alertinfo
        FROM asterisk.incoming
        WHERE cidnum = :route_number
        LIMIT 1
    """)
    route = db.execute(route_query, {"route_number": route_number}).fetchone()
    
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    # Parsear destino (como hicimos antes)
    destination = route[2] or ""
    dest_type = "desconocido"
    dest_data = destination
    dest_label = destination
    
    if destination:
        parts = destination.split('/', 1)
        if len(parts) == 2:
            dest_type = parts[0]
            dest_data = parts[1]
            
            if dest_type == "from-did-direct":
                dest_label = f"Extensión → {dest_data}"
            elif dest_type == "app-ivr":
                dest_label = f"IVR → {dest_data}"
            elif dest_type == "app-queue":
                dest_label = f"Cola → {dest_data}"
            else:
                dest_label = f"{dest_type} → {dest_data}"
    
    # 2. Estadísticas de las últimas 30 llamadas
    stats_query = text("""
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered_calls,
            AVG(billsec) as avg_duration,
            MIN(calldate) as first_call,
            MAX(calldate) as last_call
        FROM asteriskcdrdb.cdr
        WHERE dst = :destination
        AND calldate >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    stats = db.execute(stats_query, {"destination": destination}).fetchone()
    
    total_calls = stats[0] or 0
    answered_calls = stats[1] or 0
    avg_duration = round(stats[2] or 0, 1)
    first_call = stats[3]
    last_call = stats[4]
    
    answer_rate = round((answered_calls / total_calls * 100), 1) if total_calls > 0 else 0
    
    # 3. Llamadas por día (últimos 7 días)
    daily_query = text("""
        SELECT 
            DATE(calldate) as date,
            COUNT(*) as calls,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered
        FROM asteriskcdrdb.cdr
        WHERE dst = :destination
        AND calldate >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(calldate)
        ORDER BY date DESC
    """)
    daily_stats = db.execute(daily_query, {"destination": destination}).fetchall()
    
    daily_calls = [
        {
            "date": row[0].strftime('%Y-%m-%d'),
            "calls": row[1],
            "answered": row[2]
        }
        for row in daily_stats
    ]
    
    return {
        "route": {
            "numero": route[0],
            "extension": route[1],
            "destino_tipo": dest_type,
            "destino_dato": dest_data,
            "destino_label": dest_label,
            "descripcion": route[3],
            "alertinfo": route[4]
        },
        "estadisticas": {
            "total_llamadas_30dias": total_calls,
            "llamadas_contestadas": answered_calls,
            "tasa_respuesta": answer_rate,
            "duracion_promedio_seg": avg_duration,
            "primera_llamada": first_call,
            "ultima_llamada": last_call
        },
        "detalle_diario": daily_calls
    }