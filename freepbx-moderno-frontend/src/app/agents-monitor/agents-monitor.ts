// src/app/agents-monitor/agents-monitor.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AsternicService, AgentStatus, QueueStatus } from '../core/asternic.service';
import { Subscription, interval } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-agents-monitor',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './agents-monitor.html',
  styleUrls: ['./agents-monitor.css']
})
export class AgentsMonitorComponent implements OnInit, OnDestroy {
  agents: AgentStatus[] = [];
  queues: QueueStatus[] = [];
  loading = false;
  lastUpdate?: Date;
  
  // Contadores rápidos
  totalAgents = 0;
  availableAgents = 0;
  busyAgents = 0;
  pausedAgents = 0;
  offlineAgents = 0;

  private updateSubscription?: Subscription;
  private refreshInterval = 5; // segundos

  constructor(private asternicService: AsternicService) {}

  ngOnInit(): void {
    this.loadData();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  /**
   * Carga datos iniciales
   */
  loadData(): void {
    this.loading = true;
    
    // Cargar agentes
    this.asternicService.getAgentsStatus().subscribe({
      next: (agents) => {
        this.agents = agents;
        this.updateCounters();
        this.lastUpdate = new Date();
        this.loading = false;
      },
      error: (err) => {
        console.error('Error cargando agentes:', err);
        this.loading = false;
      }
    });

    // Cargar colas
    this.asternicService.getQueuesStatus().subscribe({
      next: (queues) => {
        this.queues = queues;
      },
      error: (err) => {
        console.error('Error cargando colas:', err);
      }
    });
  }

  /**
   * Inicia actualización automática
   */
  startAutoRefresh(): void {
    this.updateSubscription = interval(this.refreshInterval * 1000)
      .pipe(
        switchMap(() => this.asternicService.getAgentsStatus())
      )
      .subscribe({
        next: (agents) => {
          this.agents = agents;
          this.updateCounters();
          this.lastUpdate = new Date();
        },
        error: (err) => {
          console.error('Error en auto-refresh:', err);
        }
      });
  }

  /**
   * Detiene actualización automática
   */
  stopAutoRefresh(): void {
    if (this.updateSubscription) {
      this.updateSubscription.unsubscribe();
    }
  }

  /**
   * Actualiza contadores de estado
   */
  private updateCounters(): void {
    this.totalAgents = this.agents.length;
    this.availableAgents = this.agents.filter(a => a.status === 'available').length;
    this.busyAgents = this.agents.filter(a => a.status === 'busy').length;
    this.pausedAgents = this.agents.filter(a => a.status === 'paused').length;
    this.offlineAgents = this.agents.filter(a => a.status === 'offline').length;
  }

  /**
   * Obtiene color según estado
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'available': return '#10b981';
      case 'busy': return '#ef4444';
      case 'paused': return '#f59e0b';
      case 'ringing': return '#3b82f6';
      case 'offline': return '#6b7280';
      default: return '#9ca3af';
    }
  }

  /**
   * Obtiene icono según estado
   */
  getStatusIcon(status: string): string {
    switch (status) {
      case 'available': return 'check_circle';
      case 'busy': return 'call';
      case 'paused': return 'pause_circle';
      case 'ringing': return 'phone_in_talk';
      case 'offline': return 'cancel';
      default: return 'help';
    }
  }

  /**
   * Formatea tiempo en segundos a minutos
   */
  formatTime(seconds: number): string {
    if (!seconds) return '0m';
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return minutes > 0 ? `${minutes}m ${secs}s` : `${secs}s`;
  }

  /**
   * Formatea duración desde una fecha
   */
  formatDuration(date?: Date): string {
    if (!date) return '-';
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
    return this.formatTime(diff);
  }

  /**
   * Filtra agentes por estado
   */
  filterByStatus(status: string): AgentStatus[] {
    return this.agents.filter(a => a.status === status);
  }

  /**
   * Obtiene agentes ordenados por rendimiento
   */
  getTopPerformers(): AgentStatus[] {
    return [...this.agents]
      .filter(a => a.callsAnswered > 0)
      .sort((a, b) => b.callsAnswered - a.callsAnswered)
      .slice(0, 5);
  }

  /**
   * Cambia intervalo de actualización
   */
  changeRefreshInterval(seconds: number): void {
    this.refreshInterval = seconds;
    this.stopAutoRefresh();
    this.startAutoRefresh();
  }
}