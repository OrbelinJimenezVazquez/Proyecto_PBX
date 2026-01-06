// src/app/core/asternic.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, interval, switchMap, catchError, of } from 'rxjs';
import { map } from 'rxjs/operators';

export interface AgentStatus {
  extension: string;
  name: string;
  queue: string;
  status: 'available' | 'busy' | 'paused' | 'ringing' | 'offline';
  statusText: string;
  pauseReason?: string;
  lastCall?: Date;
  callsAnswered: number;
  callsMissed: number;
  avgTalkTime: number;
  loginTime?: Date;
  totalPauseTime: number;
}

export interface QueueStatus {
  name: string;
  waiting: number;
  answered: number;
  abandoned: number;
  agentsLoggedIn: number;
  agentsAvailable: number;
  longestWait: number;
}

@Injectable({
  providedIn: 'root'
})
export class AsternicService {
  // Configuración de Asternic
  private asternicUrl = 'http://10.10.16.9/stats';
  private username = 'adminbeyond';
  private password = 'adminbeyond';

  constructor(private http: HttpClient) {}

  /**
   * Obtiene el estado en tiempo real de todos los agentes
   */
  getAgentsStatus(): Observable<AgentStatus[]> {
    // Usar el proxy backend en lugar de llamar directamente a Asternic
    return this.http.get<any>('/api/asternic/agents/status').pipe(
      map(response => this.parseAgentsResponse(response)),
      catchError(err => {
        console.error('Error obteniendo estado de agentes:', err);
        return of([]);
      })
    );
  }

  /**
   * Obtiene el estado de las colas en tiempo real
   */
  getQueuesStatus(): Observable<QueueStatus[]> {
    // Usar el proxy backend
    return this.http.get<any>('/api/asternic/queues/status').pipe(
      map(response => this.parseQueuesResponse(response)),
      catchError(err => {
        console.error('Error obteniendo estado de colas:', err);
        return of([]);
      })
    );
  }

  /**
   * Obtiene estado de un agente específico
   */
  getAgentStatus(extension: string): Observable<AgentStatus | null> {
    return this.getAgentsStatus().pipe(
      map(agents => agents.find(a => a.extension === extension) || null)
    );
  }

  /**
   * Polling automático cada X segundos (útil para dashboard en tiempo real)
   */
  getAgentsStatusPolling(intervalSeconds: number = 5): Observable<AgentStatus[]> {
    return interval(intervalSeconds * 1000).pipe(
      switchMap(() => this.getAgentsStatus())
    );
  }

  /**
   * Obtiene agentes que están actualmente en llamada
   */
  getAgentsOnCall(): Observable<AgentStatus[]> {
    return this.getAgentsStatus().pipe(
      map(agents => agents.filter(a => a.status === 'busy'))
    );
  }

  /**
   * Obtiene agentes disponibles para recibir llamadas
   */
  getAvailableAgents(): Observable<AgentStatus[]> {
    return this.getAgentsStatus().pipe(
      map(agents => agents.filter(a => a.status === 'available'))
    );
  }

  /**
   * Obtiene agentes en pausa
   */
  getPausedAgents(): Observable<AgentStatus[]> {
    return this.getAgentsStatus().pipe(
      map(agents => agents.filter(a => a.status === 'paused'))
    );
  }

  /**
   * Parser de respuesta de agentes (ajusta según formato de tu Asternic)
   */
  private parseAgentsResponse(response: any): AgentStatus[] {
    if (!response || !response.agents) {
      return [];
    }

    return response.agents.map((agent: any) => ({
      extension: agent.extension || agent.agent,
      name: agent.name || `Agente ${agent.extension}`,
      queue: agent.queue || 'General',
      status: this.mapStatus(agent.status),
      statusText: agent.statustext || agent.status,
      pauseReason: agent.pausereason,
      lastCall: agent.lastcall ? new Date(agent.lastcall) : undefined,
      callsAnswered: parseInt(agent.callsanswered) || 0,
      callsMissed: parseInt(agent.callsmissed) || 0,
      avgTalkTime: parseInt(agent.avgtalktime) || 0,
      loginTime: agent.logintime ? new Date(agent.logintime) : undefined,
      totalPauseTime: parseInt(agent.pausetime) || 0
    }));
  }

  /**
   * Parser de respuesta de colas
   */
  private parseQueuesResponse(response: any): QueueStatus[] {
    if (!response || !response.queues) {
      return [];
    }

    return response.queues.map((queue: any) => ({
      name: queue.name,
      waiting: parseInt(queue.waiting) || 0,
      answered: parseInt(queue.answered) || 0,
      abandoned: parseInt(queue.abandoned) || 0,
      agentsLoggedIn: parseInt(queue.agentsloggedin) || 0,
      agentsAvailable: parseInt(queue.agentsavailable) || 0,
      longestWait: parseInt(queue.longestwait) || 0
    }));
  }

  /**
   * Mapea el estado de Asternic a nuestro formato
   */
  private mapStatus(status: string): 'available' | 'busy' | 'paused' | 'ringing' | 'offline' {
    const statusLower = status?.toLowerCase() || '';
    
    if (statusLower.includes('available') || statusLower.includes('idle') || statusLower.includes('ready')) {
      return 'available';
    } else if (statusLower.includes('busy') || statusLower.includes('incall') || statusLower.includes('oncall')) {
      return 'busy';
    } else if (statusLower.includes('pause') || statusLower.includes('break')) {
      return 'paused';
    } else if (statusLower.includes('ring')) {
      return 'ringing';
    } else {
      return 'offline';
    }
  }

  /**
   * Obtiene estadísticas de rendimiento de un agente
   */
  getAgentStatistics(extension: string, startDate?: Date, endDate?: Date): Observable<any> {
    const headers = new HttpHeaders({
      'Authorization': 'Basic ' + btoa(`${this.username}:${this.password}`)
    });

    const params: any = {
      agent: extension
    };

    if (startDate) {
      params.start = startDate.toISOString();
    }
    if (endDate) {
      params.end = endDate.toISOString();
    }

    return this.http.get(`${this.asternicUrl}/api/agent-stats`, { 
      headers, 
      params 
    }).pipe(
      catchError(err => {
        console.error('Error obteniendo estadísticas de agente:', err);
        return of(null);
      })
    );
  }
}