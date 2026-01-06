// src/app/core/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = '/api';

  constructor(private http: HttpClient) {}

  // ENDPOINTS EXISTENTES
  getExtensions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/extensions`);
  }

  getDetailedCalls(
    period: 'today' | 'week' | 'month' | 'year' = 'month',
    page: number = 1,
    size: number = 50
  ): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/calls/detailed?period=${period}&page=${page}&size=${size}`);
  }

  getCallsByPeriod(
    period: 'today' | 'week' | 'month' | 'year' = 'month',
    page: number = 1,
    size: number = 100
  ): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/calls?period=${period}&page=${page}&size=${size}`);
  }
  
  getRecentCalls(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/calls/recent`);
  }

  getTrunks(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/trunks`);
  }

  // NUEVOS ENDPOINTS CON FILTROS
  getAdvancedDashboardStats(filters?: {
    period?: 'today' | 'week' | 'month' | 'year';
    startDate?: string;
    endDate?: string;
  }): Observable<any> {
    let params = new HttpParams();
    
    if (filters?.period) {
      params = params.set('period', filters.period);
    }
    if (filters?.startDate) {
      params = params.set('start_date', filters.startDate);
    }
    if (filters?.endDate) {
      params = params.set('end_date', filters.endDate);
    }

    return this.http.get<any>(`${this.baseUrl}/dashboard/advanced-stats`, { params });
  }

  getAdvancedChartsData(filters?: {
    period?: 'today' | 'week' | 'month' | 'year';
    chartType?: 'trend' | 'status' | 'agents' | 'destinations' | 'heatmap';
  }): Observable<any> {
    let params = new HttpParams();
    
    if (filters?.period) {
      params = params.set('period', filters.period);
    }
    if (filters?.chartType) {
      params = params.set('chart_type', filters.chartType);
    }

    return this.http.get<any>(`${this.baseUrl}/dashboard/advanced-charts`, { params });
  }

  getIvrs(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/ivrs`);
  }

  getIncomingRoutes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/incoming-routes`);
  }

  getRouteDetail(routeNumber: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/incoming-routes/${routeNumber}`);
  }

  generateDashboardPdf(): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/dashboard/report/pdf`, { responseType: 'blob' });
  }

  // NUEVOS ENDPOINTS PARA MÉTRICAS DE COLAS
  getQueueMetrics(period: 'today' | 'week' | 'month' | 'year' = 'today'): Observable<any> {
    // Si es 'year', usamos 'month' en el backend (30 días es suficiente)
    const backendPeriod = period === 'year' ? 'month' : period;
    return this.http.get<any>(`${this.baseUrl}/dashboard/queue-metrics?period=${backendPeriod}`);
  }

  getQueueSLA(period: 'today' | 'week' | 'month' | 'year' = 'today', slaThreshold: number = 30): Observable<any> {
    // Si es 'year', usamos 'month' en el backend (30 días es suficiente)
    const backendPeriod = period === 'year' ? 'month' : period;
    return this.http.get<any>(`${this.baseUrl}/dashboard/queue-sla?period=${backendPeriod}&sla_threshold=${slaThreshold}`);
  }

  getActiveCalls(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/dashboard/active-calls`);
  }

  getQueueSummary(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/dashboard/queue-summary`);
  }

  // ENDPOINTS PARA MONITOR DE AGENTES
  getAgentsRealtimeStatus(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/asternic/agents/realtime-status`);
  }

  getAgentDetails(extension: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/asternic/agents/${extension}/details`);
  }

  getAgentsSessions(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/asternic/agents/sessions`);
  }

  getAgentsPauses(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/asternic/agents/pauses`);
  }

  // ENDPOINTS PARA GESTIÓN DE COLAS
  getQueues(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/queues`);
  }

  createQueue(queue: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/queues`, queue);
  }

  updateQueue(id: number, queue: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/queues/${id}`, queue);
  }

  deleteQueue(id: number): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/queues/${id}`);
  }
}