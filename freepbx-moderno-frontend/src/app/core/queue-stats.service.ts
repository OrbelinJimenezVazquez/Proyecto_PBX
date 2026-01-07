// src/app/core/queue-stats.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface QueueRealtimeStats {
  queues: Array<{
    session_id: string;
    last_update: string;
    metrics: {
      calls: {
        received: number;
        answered: number;
        answered_sla: number;
        unanswered: number;
        unanswered_sla: number;
        abandoned: number;
        abandoned_sla: number;
        transferred: number;
      };
      times: {
        total_wait: number;
        total_talk: number;
        avg_wait: number;
        avg_talk: number;
        max_wait: number;
      };
      sla: {
        percentage: number;
        threshold: number;
      };
      agents: {
        logged_in: number;
        available: number;
        busy: number;
        paused: number;
      };
      current: {
        calls_waiting: number;
        longest_wait: number;
      };
    };
  }>;
  totals: any;
  timestamp: string;
}

export interface QueueSummary {
  period: string;
  daily_stats: Array<{
    date: string;
    total_calls: number;
    answered_calls: number;
    abandoned_calls: number;
    timeout_calls: number;
    avg_wait_time: number;
    max_wait_time: number;
  }>;
  timestamp: string;
}

export interface QueueEvent {
  timestamp: string;
  call_id: string;
  queue: string;
  queue_name: string;
  agent: string;
  event: string;
  data: {
    data1: string;
    data2: string;
    data3: string;
  };
}

export interface EventType {
  id: number;
  name: string;
  description: string;
}

export interface AgentActivity {
  id: number;
  timestamp: string;
  queue: string;
  queue_name: string;
  agent: string;
  event: string;
  event_description: string;
  data: string;
  duration: number;
  uniqueid: string;
  computed: number;
}

@Injectable({
  providedIn: 'root'
})
export class QueueStatsService {
  private readonly apiUrl = '/api/queues';
  private readonly asternicUrl = '/api/asternic';

  constructor(private http: HttpClient) {}

  /**
   * Obtiene estadísticas en tiempo real de todas las colas
   */
  getRealtimeStats(): Observable<QueueRealtimeStats> {
    return this.http.get<QueueRealtimeStats>(`${this.apiUrl}/stats/realtime`);
  }

  /**
   * Obtiene resumen de estadísticas de colas
   * @param hours - Horas hacia atrás (default: 24)
   */
  getSummary(hours: number = 24): Observable<QueueSummary> {
    return this.http.get<QueueSummary>(`${this.apiUrl}/stats/summary`, {
      params: { hours: hours.toString() }
    });
  }

  /**
   * Obtiene eventos recientes de colas
   * @param limit - Número máximo de eventos
   * @param eventType - Filtrar por tipo de evento (opcional)
   */
  getEvents(limit: number = 100, eventType?: string): Observable<{events: QueueEvent[], count: number, timestamp: string}> {
    let params: any = { limit: limit.toString() };
    if (eventType) {
      params.event_type = eventType;
    }
    return this.http.get<{events: QueueEvent[], count: number, timestamp: string}>(
      `${this.apiUrl}/events`,
      { params }
    );
  }

  /**
   * Obtiene catálogo de tipos de eventos
   */
  getEventTypes(): Observable<{events: EventType[], total: number}> {
    return this.http.get<{events: EventType[], total: number}>(`${this.apiUrl}/types/events`);
  }

  /**
   * Obtiene miembros de una cola específica
   * @param queueId - ID de la cola
   */
  getQueueMembers(queueId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/${queueId}/members`);
  }

  /**
   * Obtiene actividad detallada de agentes
   * @param hours - Horas hacia atrás (default: 24)
   * @param agent - Filtrar por agente específico (opcional)
   */
  getAgentsActivityDetailed(hours: number = 24, agent?: string): Observable<{
    activities: AgentActivity[],
    agent_summaries: any[],
    total_activities: number,
    period: string,
    timestamp: string
  }> {
    let params: any = { hours: hours.toString() };
    if (agent) {
      params.agent = agent;
    }
    return this.http.get<any>(
      `${this.asternicUrl}/agents/activity-detailed`,
      { params }
    );
  }

  /**
   * Obtiene todos los tipos de eventos de qevent
   */
  getAllEventTypes(): Observable<{events: EventType[], total: number, timestamp: string}> {
    return this.http.get<any>(`${this.asternicUrl}/events/types`);
  }
}
