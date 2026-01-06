from fastapi import APIRouter, Depends, HTTPException, Query 
from sqlalchemy.orm import Session
from sqlalchemy import text, func, case
from database import get_db
from models import CDR, User, SIP, Trunk, IVRDetail, IVREntry, IncomingRoute
from datetime import datetime, timedelta

# Definición del router
router = APIRouter(prefix="/api", tags=["Telephony"])

# Endpoint para Obtener lista de extensiones con su estado
@router.get("/extensions")
def get_extensions(db: Session = Depends(get_db)):
    # Usar ORM con joins para prevenir SQL injection
    # Subquery para obtener el host de cada extensión
    host_subquery = (
        db.query(
            SIP.id,
            SIP.data
        )
        .filter(SIP.keyword == 'host')
        .subquery()
    )
    
    # Definir el status basado en el valor del host
    status_case = case(
        (host_subquery.c.data == None, 'offline'),
        (host_subquery.c.data == 'dynamic', 'online'),
        (host_subquery.c.data.regexp_match(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'), 'online'),
        else_='offline'
    )
    
    # Query principal con left join
    results = (
        db.query(
            User.extension,
            User.name,
            status_case.label('status')
        )
        .outerjoin(host_subquery, User.extension == host_subquery.c.id)
        .order_by(User.extension)
        .all()
    )
    
    return [
        {"extension": row.extension, "name": row.name, "status": row.status}
        for row in results
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
    # Usar ORM para prevenir SQL injection
    trunks = (
        db.query(Trunk)
        .filter(Trunk.disabled != '1')  # Filtrar troncales deshabilitadas
        .order_by(Trunk.name)
        .all()
    )
    
    return [
        {
            "name": trunk.name,
            "tech": trunk.tech,
            "channelid": trunk.channelid
        }
        for trunk in trunks
    ]

# Endpoint para Obtener estadísticas avanzadas para el dashboard CON FILTROS
@router.get("/dashboard/advanced-stats")
def get_advanced_dashboard_stats(
    period: str = Query("week", enum=["today", "week", "month", "year"]),
    db: Session = Depends(get_db)
):
    now = datetime.now()
    
    # Calcular fechas según el período seleccionado
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        days_for_trend = 1
    elif period == "week":
        start_date = now - timedelta(days=7)
        days_for_trend = 7
    elif period == "month":
        start_date = now - timedelta(days=30)
        days_for_trend = 30
    else:  # year
        start_date = now - timedelta(days=365)
        days_for_trend = 365
    
    end_date = now
    
    # 1. Métricas generales del período seleccionado
    general_stats = db.execute(text("""
        SELECT 
            COUNT(*) as total_calls,
            AVG(duration) as avg_duration,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered_calls,
            SUM(CASE WHEN disposition = 'NO ANSWER' THEN 1 ELSE 0 END) as no_answer_calls,
            SUM(CASE WHEN disposition = 'FAILED' THEN 1 ELSE 0 END) as failed_calls,
            AVG(billsec) as avg_billsec
        FROM asteriskcdrdb.cdr 
        WHERE calldate >= :start_date AND calldate <= :end_date
    """), {"start_date": start_date, "end_date": end_date}).fetchone()
    
    total_calls = general_stats[0] or 0
    answered = general_stats[2] or 0
    answer_rate = round((answered / total_calls * 100), 1) if total_calls > 0 else 0
    
    # 2. Estado de llamadas (para gráfica de dona) del período seleccionado
    call_status = db.execute(text("""
        SELECT 
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered,
            SUM(CASE WHEN disposition = 'NO ANSWER' THEN 1 ELSE 0 END) as no_answer,
            SUM(CASE WHEN disposition = 'FAILED' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN disposition = 'BUSY' THEN 1 ELSE 0 END) as busy
        FROM asteriskcdrdb.cdr
        WHERE calldate >= :start_date AND calldate <= :end_date
    """), {"start_date": start_date, "end_date": end_date}).fetchone()
    
    # 3. Tendencia diaria (ajustada al período)
    daily_trend = db.execute(text("""
        SELECT 
            DATE(calldate) as date,
            COUNT(*) as total,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered
        FROM asteriskcdrdb.cdr
        WHERE calldate >= :start_date AND calldate <= :end_date
        GROUP BY DATE(calldate)
        ORDER BY date
    """), {"start_date": start_date, "end_date": end_date}).fetchall()
    
    daily_data = [
        {
            "date": r[0].strftime('%Y-%m-%d'),
            "total": r[1],
            "answered": r[2] or 0
        }
        for r in daily_trend
    ]
    
    # 4. Top agentes del período seleccionado
    agent_stats = db.execute(text("""
        SELECT 
            dst as extension,
            u.name as agent_name,
            COUNT(*) as total_calls,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered_calls
        FROM asteriskcdrdb.cdr c
        LEFT JOIN asterisk.users u ON c.dst = u.extension
        WHERE calldate >= :start_date AND calldate <= :end_date
        GROUP BY dst
        HAVING answered_calls > 0
        ORDER BY answered_calls DESC
        LIMIT 10
    """), {"start_date": start_date, "end_date": end_date}).fetchall()
    
    agent_data = [
        {
            "extension": r[0],
            "name": r[1] or r[0],
            "total_calls": r[2],
            "answered_calls": r[3]
        }
        for r in agent_stats
    ]
    
    # 5. Distribución por tipo de destino del período seleccionado
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
        WHERE calldate >= :start_date AND calldate <= :end_date
        GROUP BY destination_type
        ORDER BY calls DESC
    """), {"start_date": start_date, "end_date": end_date}).fetchall()
    
    dest_data = [
        {
            "type": r[0],
            "calls": r[1]
        }
        for r in dest_distribution
    ]
    
    # 6. Distribución por hora del día (para nuevo gráfico) del período seleccionado
    hourly_distribution = db.execute(text("""
        SELECT 
            HOUR(calldate) as hour,
            COUNT(*) as calls,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered
        FROM asteriskcdrdb.cdr
        WHERE calldate >= :start_date AND calldate <= :end_date
        GROUP BY HOUR(calldate)
        ORDER BY hour
    """), {"start_date": start_date, "end_date": end_date}).fetchall()
    
    hourly_data = [
        {
            "hour": r[0],
            "calls": r[1],
            "answered": r[2]
        }
        for r in hourly_distribution
    ]
    
    # Extensiones activas (esto no depende del período)
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
            "calls_today": total_calls if period == "today" else general_stats[0],
            "calls_this_week": total_calls if period == "week" else general_stats[0],
            "calls_this_month": total_calls if period == "month" else general_stats[0],
            "avg_duration": round(general_stats[1] or 0, 1),
            "answered_calls_today": answered if period == "today" else answered,
            "no_answer_calls_today": general_stats[3] or 0,
            "failed_calls_today": general_stats[4] or 0,
            "answer_rate": answer_rate,
            "active_extensions": active_extensions[0] or 0
        },
        "call_status": {
            "answered": call_status[0] or 0,
            "no_answer": call_status[1] or 0,
            "failed": call_status[2] or 0,
            "busy": call_status[3] or 0
        },
        "daily_trends": daily_data,
        "top_agents": agent_data,
        "destination_distribution": dest_data,
        "hourly_distribution": hourly_data
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
    days = [ 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
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
    #esta grafica muestra la comparación mensual de llamadas en los últimos 6 meses
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
    try:
        # Usar ORM para obtener IVRs
        ivrs = db.query(IVRDetail).order_by(IVRDetail.name).all()
        
        result = []
        
        for ivr in ivrs:
            try:
                ivr_name = ivr.name or f"IVR_{ivr.id}"
                
                # Obtener opciones del IVR usando ORM
                options = (
                    db.query(IVREntry)
                    .filter(IVREntry.ivr_id == ivr.id)
                    .order_by(IVREntry.selection)
                    .all()
                )
                
                options_list = []
                for opt in options:
                    try:
                        selection = opt.selection
                        dest = opt.dest
                        
                        # Parsear el destino (FreePBX guarda como JSON-like string)
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
                        
                        options_list.append({
                            "option": selection,
                            "dest_type": dest_type,
                            "dest_label": dest_label,
                            "calls_last_30_days": 0
                        })
                    except Exception as opt_error:
                        print(f"Error procesando opción: {opt_error}")
                        continue
                
                result.append({
                    "id": ivr.id,
                    "name": ivr_name,
                    "announcement_id": ivr.announcement,
                    "options": options_list
                })
            except Exception as ivr_error:
                print(f"Error procesando IVR {ivr.id}: {ivr_error}")
                continue
        
        return result
    except Exception as e:
        print(f"Error en get_ivrs_with_stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# Endpoint para Obtener lista de rutas entrantes con detalles y estadísticas
@router.get("/incoming-routes")
def list_incoming_routes(db: Session = Depends(get_db)):
    # Usar ORM para prevenir SQL injection
    routes_query = (
        db.query(IncomingRoute)
        .order_by(IncomingRoute.cidnum)
        .all()
    )

    routes = []
    for route in routes_query:
        destination = route.destination or ""
        
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
                "numero": route.cidnum,
                "extension": route.extension,
                "destino_tipo": dest_type,
                "destino_dato": dest_data,
                "destino_label": dest_label,
                "descripcion": route.description,
                "alertinfo": route.alertinfo,
            }
        )

    return routes

# Endpoint para Obtener detalle de una ruta entrante específica
@router.get("/incoming-routes/{route_number}")
def get_incoming_route_detail(route_number: str, db: Session = Depends(get_db)):
    # Obtener información básica de la ruta usando ORM
    route = (
        db.query(IncomingRoute)
        .filter(IncomingRoute.cidnum == route_number)
        .first()
    )
    
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    # Parsear destino (como hicimos antes)
    destination = route.destination or ""
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
    
    # Estadísticas de las últimas 30 llamadas usando ORM
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    stats = (
        db.query(
            func.count(CDR.id).label('total_calls'),
            func.sum(case((CDR.disposition == 'ANSWERED', 1), else_=0)).label('answered_calls'),
            func.avg(CDR.billsec).label('avg_duration'),
            func.min(CDR.calldate).label('first_call'),
            func.max(CDR.calldate).label('last_call')
        )
        .filter(
            CDR.dst == destination,
            CDR.calldate >= thirty_days_ago
        )
        .first()
    )
    
    total_calls = stats.total_calls or 0
    answered_calls = stats.answered_calls or 0
    avg_duration = round(stats.avg_duration or 0, 1)
    first_call = stats.first_call
    last_call = stats.last_call
    
    answer_rate = round((answered_calls / total_calls * 100), 1) if total_calls > 0 else 0
    
    # Llamadas por día (últimos 7 días) usando ORM
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    daily_stats = (
        db.query(
            func.date(CDR.calldate).label('date'),
            func.count(CDR.id).label('calls'),
            func.sum(case((CDR.disposition == 'ANSWERED', 1), else_=0)).label('answered')
        )
        .filter(
            CDR.dst == destination,
            CDR.calldate >= seven_days_ago
        )
        .group_by(func.date(CDR.calldate))
        .order_by(func.date(CDR.calldate).desc())
        .all()
    )
    
    daily_calls = [
        {
            "date": row.date.strftime('%Y-%m-%d'),
            "calls": row.calls,
            "answered": row.answered
        }
        for row in daily_stats
    ]
    
    return {
        "route": {
            "numero": route.cidnum,
            "extension": route.extension,
            "destino_tipo": dest_type,
            "destino_dato": dest_data,
            "destino_label": dest_label,
            "descripcion": route.description,
            "alertinfo": route.alertinfo
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