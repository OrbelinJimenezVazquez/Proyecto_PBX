# utils/php_parser.py
"""
Utilidades para parsear datos serializados de PHP
"""
import re
from typing import Any, Dict


def unserialize_php(data: str) -> Dict[str, Any]:
    """
    Parsea datos serializados en formato PHP
    Soporta arrays asociativos básicos
    
    Ejemplo de entrada PHP serializada:
    a:3:{s:14:"TOTAL_RECEIVED";i:11;s:14:"TOTAL_ANSWERED";i:11;s:15:"TOTAL_ABANDONED";i:0;}
    
    Retorna un diccionario Python
    """
    if not data or not isinstance(data, str):
        return {}
    
    result = {}
    
    try:
        # Patrón para encontrar pares clave-valor
        # s:longitud:"clave";i:valor;
        # s:longitud:"clave";s:longitud:"valor";
        pattern = r's:(\d+):"([^"]+)";(?:i:(\d+)|s:(\d+):"([^"]*)")'
        
        matches = re.findall(pattern, data)
        
        for match in matches:
            key_len, key, int_val, str_len, str_val = match
            
            # Validar longitud de clave
            if len(key) != int(key_len):
                continue
            
            # Determinar si es entero o string
            if int_val:
                result[key] = int(int_val)
            elif str_val is not None:
                if str_len and len(str_val) != int(str_len):
                    continue
                result[key] = str_val
        
        return result
        
    except Exception as e:
        print(f"Error parseando datos PHP: {str(e)}")
        return {}


def parse_sqlrealtime_data(php_data: str) -> Dict[str, Any]:
    """
    Parsea y estructura datos de sqlrealtime en un formato más usable
    
    Retorna diccionario con métricas organizadas
    """
    raw_data = unserialize_php(php_data)
    
    if not raw_data:
        return {}
    
    # Organizar métricas en categorías
    metrics = {
        "calls": {
            "received": raw_data.get("TOTAL_RECEIVED", 0),
            "answered": raw_data.get("TOTAL_ANSWERED", 0),
            "answered_sla": raw_data.get("TOTAL_ANSWERED_SLA", 0),
            "unanswered": raw_data.get("TOTAL_UNANSWERED", 0),
            "unanswered_sla": raw_data.get("TOTAL_UNANSWERED_SLA", 0),
            "abandoned": raw_data.get("TOTAL_ABANDONED", 0),
            "abandoned_sla": raw_data.get("TOTAL_ABANDONED_SLA", 0),
            "transferred": raw_data.get("TOTAL_TRANSFERRED", 0),
        },
        "times": {
            "total_wait": raw_data.get("TOTAL_WAIT", 0),
            "total_talk": raw_data.get("TOTAL_TALK", 0),
            "avg_wait": raw_data.get("AVG_WAIT", 0),
            "avg_talk": raw_data.get("AVG_TALK", 0),
            "max_wait": raw_data.get("MAX_WAIT", 0),
        },
        "sla": {
            "percentage": calculate_sla_percentage(raw_data),
            "threshold": raw_data.get("SLA_THRESHOLD", 60),
        },
        "agents": {
            "logged_in": raw_data.get("AGENTS_LOGGED_IN", 0),
            "available": raw_data.get("AGENTS_AVAILABLE", 0),
            "busy": raw_data.get("AGENTS_BUSY", 0),
            "paused": raw_data.get("AGENTS_PAUSED", 0),
        },
        "current": {
            "calls_waiting": raw_data.get("CALLS_WAITING", 0),
            "longest_wait": raw_data.get("LONGEST_WAIT", 0),
        }
    }
    
    return metrics


def calculate_sla_percentage(data: Dict[str, Any]) -> float:
    """
    Calcula el porcentaje de SLA basado en llamadas atendidas y abandonadas
    """
    try:
        answered_sla = data.get("TOTAL_ANSWERED_SLA", 0)
        total_received = data.get("TOTAL_RECEIVED", 0)
        
        if total_received == 0:
            return 0.0
        
        return round((answered_sla / total_received) * 100, 2)
        
    except Exception:
        return 0.0
