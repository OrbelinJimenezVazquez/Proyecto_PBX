// src/app/core/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  //private baseUrl = 'http://localhost:8000/api';
  private baseUrl = '/api';  // sin dominio ni puerto por el proxy.conf.json
  constructor(private http: HttpClient) {}

  // ENDOPOINTS
    // Endpoint para obtener extensiones
  getExtensions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/extensions`);
  }

  // Llamadas detalladas (sin paginación, pero con más datos)
  getDetailedCalls(
    period: 'today' | 'week' | 'month' | 'year' = 'month',
    page: number = 1,
    size: number = 50
  ): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/calls/detailed?period=${period}&page=${page}&size=${size}`);
  }

  // Endpoint para obtener llamadas por medio del periodo
  getCallsByPeriod(
    period: 'today' | 'week' | 'month' | 'year' = 'month',
    page: number = 1,
    size: number = 100
  ): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/calls?period=${period}&page=${page}&size=${size}`);
  }
  
  // Endpoint para obtner las llamadas recientes
  getRecentCalls(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/calls/recent`);
  }

  // Endpoint para obtener los troncales, Que son los toncales(trunks) estos son las lineas que conectan el PBx con la red telefonica.
  getTrunks(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/trunks`);
  }

  // Endpoint para obtener las estadisticas avanzadas del dashboard
  getAdvancedDashboardStats(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/dashboard/advanced-stats`);
  }

  // Endpoint para obtener los IVRs, que son los sistemas de respuesta de voz interactiva.
  getIvrs(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/ivrs`);
  }
  // Endpoint para obtener las rutas entrantes
  getIncomingRoutes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/incoming-routes`);
  }

  // Endpoint para obtener detalles de una ruta entrante específica
  getRouteDetail(routeNumber: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/incoming-routes/${routeNumber}`);
  }

  // Endpoint para generar el reporte del dashboard en PDF
  generateDashboardPdf(): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/dashboard/report/pdf`, { responseType: 'blob' });
  }

  // Endpoint para obtener datos para gráficos avanzados
  getAdvancedChartsData(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/dashboard/advanced-charts`);
  }
}