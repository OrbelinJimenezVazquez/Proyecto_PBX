// src/app/agents-monitor/agents-monitor.ts
import { Component, OnInit, OnDestroy, ChangeDetectorRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../core/api.service';
import { ToastService } from '../core/toast.service';
import { ChartService } from '../core/chart.service';
import { QueueStatsService, QueueRealtimeStats } from '../core/queue-stats.service';
import { Chart } from 'chart.js';
import { catchError } from 'rxjs/operators';
import { of, Subscription, interval } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-agents-monitor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agents-monitor.html',
  styleUrls: ['./agents-monitor.css']
})
export class AgentsMonitorComponent implements OnInit, OnDestroy, AfterViewInit {
  agents: any[] = [];
  agentsByQueues: any[] = [];
  sessions: any[] = [];
  pauses: any[] = [];
  queueStats: QueueRealtimeStats | null = null;
  viewMode: 'agents' | 'queues' = 'agents';
  summary: any = {
    total: 0,
    available: 0,
    busy: 0,
    paused: 0,
    offline: 0,
    ringing: 0
  };
  
  loading = false;
  lastUpdate?: Date;
  
  // Filtros
  selectedStatus: string = 'all';
  selectedQueue: string = 'all';
  queues: Array<{id: string, name: string}> = [];
  
  // Modal de detalles
  showModal = false;
  selectedAgent: any = null;
  agentDetails: any = null;
  loadingDetails = false;
  
  // Gráficas
  private callsChart: Chart | null = null;
  private performanceChart: Chart | null = null;
  
  // Alertas
  private readonly PAUSE_ALERT_THRESHOLD = 900; // 15 minutos en segundos
  private alertedAgents = new Set<string>();
  
  private updateSubscription?: Subscription;
  private counterSubscription?: Subscription;
  refreshInterval = 10; // segundos - ahora público para el template

  constructor(
    private api: ApiService,
    private toast: ToastService,
    private chartService: ChartService,
    private queueStatsService: QueueStatsService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadData();
    this.startAutoRefresh();
    this.startCounterUpdate();
  }

  ngAfterViewInit(): void {
    // Las gráficas se crean cuando se abre el modal
  }

  /**
   * Inicia actualización de contadores cada segundo
   */
  startCounterUpdate(): void {
    this.counterSubscription = interval(1000).subscribe(() => {
      this.updateCounters();
    });
  }

  /**
   * Detiene actualización de contadores
   */
  stopCounterUpdate(): void {
    if (this.counterSubscription) {
      this.counterSubscription.unsubscribe();
    }
  }

  /**
   * Actualiza contadores de duración en tiempo real
   */
  updateCounters(): void {
    const now = new Date();
    this.agents = this.agents.map(agent => {
      if (agent.lastActivity) {
        const lastActivityDate = new Date(agent.lastActivity);
        const elapsed = Math.floor((now.getTime() - lastActivityDate.getTime()) / 1000);
        return {
          ...agent,
          timeInState: elapsed,
          duration: this.formatDuration(elapsed)
        };
      }
      return agent;
    });
    this.cdr.detectChanges();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
    this.stopCounterUpdate();
    this.destroyCharts();
  }

  /**
   * Carga todos los datos (agentes y estadísticas de colas)
   */
  loadData(): void {
    this.loading = true;
    
    // Cargar solo agentes primero para que sea más rápido
    this.api.getAgentsRealtimeStatus().pipe(
      catchError((err) => {
        console.error('Error cargando datos:', err);
        this.toast.error('Error al cargar datos');
        return of(null);
      })
    ).subscribe({
      next: (data) => {
        // Procesar datos de agentes
        if (data) {
          this.agents = data.agents || [];
          this.agentsByQueues = data.queues || [];
          this.summary = data.summary || this.summary;
          this.lastUpdate = new Date();
          
          // Extraer colas únicas
          const uniqueQueues = new Map();
          this.agents.forEach(a => {
            if (a.queue) {
              uniqueQueues.set(a.queue, a.queueName || a.queue);
            }
          });
          this.queues = Array.from(uniqueQueues.entries()).map(([id, name]) => ({ id, name }));
          
          // Verificar alertas
          this.checkPauseAlerts();
        }
        
        this.loading = false;
        this.cdr.detectChanges();
        
        // Cargar estadísticas de colas después (no bloquea la vista principal)
        this.loadQueueStats();
      }
    });
  }

  /**
   * Carga estadísticas de colas en segundo plano
   */
  loadQueueStats(): void {
    this.queueStatsService.getRealtimeStats().pipe(
      catchError((err) => {
        console.error('Error cargando estadísticas de colas:', err);
        return of(null);
      })
    ).subscribe({
      next: (data) => {
        if (data) {
          this.queueStats = data;
          this.cdr.detectChanges();
        }
      }
    });
  }

  /**
   * Carga estado de agentes en tiempo real
   */
  loadAgents(): void {
    this.loading = true;
    
    this.api.getAgentsRealtimeStatus().pipe(
      catchError((err) => {
        console.error('Error cargando agentes:', err);
        this.toast.error('Error al cargar estado de agentes');
        return of(null);
      })
    ).subscribe({
      next: (data: any) => {
        if (data) {
          this.agents = data.agents || [];
          this.summary = data.summary || this.summary;
          this.lastUpdate = new Date();
          
          console.log('Loaded agents:', this.agents);
          console.log('First agent structure:', this.agents[0]);
          
          // Extraer colas únicas con nombres legibles
          const uniqueQueues = new Map();
          this.agents.forEach(a => {
            if (a.queue) {
              uniqueQueues.set(a.queue, a.queueName || a.queue);
            }
          });
          this.queues = Array.from(uniqueQueues.entries()).map(([id, name]) => ({ id, name }));
          
          // Verificar alertas de pausa prolongada
          this.checkPauseAlerts();
        }
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  /**
   * Carga sesiones activas
   */
  loadSessions(): void {
    this.api.getAgentsSessions().pipe(
      catchError((err) => {
        console.error('Error cargando sesiones:', err);
        return of(null);
      })
    ).subscribe({
      next: (data: any) => {
        if (data) {
          this.sessions = data.sessions || [];
        }
      }
    });
  }

  /**
   * Carga agentes en pausa
   */
  loadPauses(): void {
    this.api.getAgentsPauses().pipe(
      catchError((err) => {
        console.error('Error cargando pausas:', err);
        return of(null);
      })
    ).subscribe({
      next: (data: any) => {
        if (data) {
          this.pauses = data.pauses || [];
        }
      }
    });
  }

  /**
   * Obtiene detalles de un agente y abre el modal
   */
  getAgentDetails(extension: string): void {
    console.log('getAgentDetails called with extension:', extension);
    console.log('Available agents:', this.agents);
    console.log('Agent extensions:', this.agents.map(a => a.extension));
    
    if (!extension) {
      console.error('Extension is undefined or null');
      this.toast.error('No se pudo identificar el agente');
      return;
    }
    
    this.loadingDetails = true;
    this.selectedAgent = this.agents.find(a => String(a.extension) === String(extension));
    console.log('Selected agent:', this.selectedAgent);
    
    if (!this.selectedAgent) {
      console.error('Agent not found with extension:', extension);
      this.toast.error('Agente no encontrado');
      this.loadingDetails = false;
      return;
    }
    
    this.showModal = true;
    
    this.api.getAgentDetails(extension).pipe(
      catchError((err) => {
        console.error('Error cargando detalles:', err);
        this.toast.error('Error al cargar detalles del agente');
        this.loadingDetails = false;
        return of(null);
      })
    ).subscribe({
      next: (data: any) => {
        if (data) {
          this.agentDetails = data;
          this.loadingDetails = false;
          
          // Crear gráficas después de que se rendericen los canvas
          setTimeout(() => {
            this.createAgentCharts();
          }, 100);
        }
      }
    });
  }

  /**
   * Auto-refresh cada 10 segundos
   */
  startAutoRefresh(): void {
    this.updateSubscription = interval(this.refreshInterval * 1000)
      .pipe(
        switchMap(() => this.api.getAgentsRealtimeStatus())
      )
      .subscribe({
        next: (data) => {
          if (data) {
            this.agents = data.agents || [];
            this.agentsByQueues = data.queues || [];
            this.summary = data.summary || this.summary;
            this.lastUpdate = new Date();
            this.cdr.detectChanges();
          }
        },
        error: (err) => {
          console.error('Error en auto-refresh:', err);
        }
      });
  }

  stopAutoRefresh(): void {
    if (this.updateSubscription) {
      this.updateSubscription.unsubscribe();
    }
  }

  /**
   * Refresh manual
   */
  refresh(): void {
    this.loadData();
    this.loadSessions();
    this.loadPauses();
    this.toast.success('Datos actualizados');
  }

  /**
   * Filtrar agentes
   */
  get filteredAgents(): any[] {
    return this.agents.filter(agent => {
      const statusMatch = this.selectedStatus === 'all' || agent.status === this.selectedStatus;
      const queueMatch = this.selectedQueue === 'all' || agent.queue === this.selectedQueue;
      return statusMatch && queueMatch;
    });
  }

  /**
   * Cambiar filtro de estado
   */
  filterByStatus(status: string): void {
    this.selectedStatus = status;
  }

  /**
   * Cambiar filtro de cola
   */
  filterByQueue(queue: string): void {
    this.selectedQueue = queue;
  }

  /**
   * Formatear tiempo en formato legible
   */
  formatTime(seconds: number): string {
    if (!seconds || seconds < 0) return '0s';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  /**
   * Obtener clase CSS según estado
   */
  formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  getStatusClass(status: string): string {
    const classes: any = {
      'available': 'bg-green-100 text-green-800 border-green-200',
      'busy': 'bg-red-100 text-red-800 border-red-200',
      'paused': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'ringing': 'bg-blue-100 text-blue-800 border-blue-200',
      'offline': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return classes[status] || classes['offline'];
  }

  /**
   * Obtener icono según estado
   */
  getStatusIcon(status: string): string {
    const icons: any = {
      'available': 'check_circle',
      'busy': 'phone_in_talk',
      'paused': 'pause_circle',
      'ringing': 'ring_volume',
      'offline': 'cancel'
    };
    return icons[status] || 'help';
  }

  /**
   * Cambia intervalo de actualización
   */
  changeRefreshInterval(seconds: number): void {
    this.refreshInterval = seconds;
    this.stopAutoRefresh();
    this.startAutoRefresh();
  }

  /**
   * Cierra el modal de detalles
   */
  closeModal(): void {
    this.showModal = false;
    this.selectedAgent = null;
    this.agentDetails = null;
    this.destroyCharts();
  }

  /**
   * Crea gráficas de rendimiento del agente
   */
  private createAgentCharts(): void {
    this.destroyCharts();

    if (!this.agentDetails) return;

    // Gráfica de llamadas (atendidas vs pausas)
    const callsCanvas = document.getElementById('callsChart') as HTMLCanvasElement;
    if (callsCanvas) {
      const dailyStats = this.agentDetails.dailyStats || {};
      const answered = dailyStats.callsAnswered || 0;
      const pauseCount = dailyStats.pauseCount || 0;
      
      const ctx = callsCanvas.getContext('2d');
      if (ctx) {
        this.callsChart = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: ['Llamadas Atendidas', 'Pausas'],
            datasets: [{
              data: [answered, pauseCount],
              backgroundColor: ['#10b981', '#f59e0b'],
              borderWidth: 3,
              borderColor: '#ffffff',
              hoverOffset: 10
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  padding: 15,
                  font: { size: 12 },
                  usePointStyle: true
                }
              },
              tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12
              }
            }
          }
        });
      }
    }

    // Gráfica de tiempos
    const performanceCanvas = document.getElementById('performanceChart') as HTMLCanvasElement;
    if (performanceCanvas) {
      const stats = this.agentDetails.dailyStats || {};
      const ctx = performanceCanvas.getContext('2d');
      if (ctx) {
        this.performanceChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: ['Tiempo en llamada', 'Tiempo en pausa'],
            datasets: [{
              label: 'Minutos',
              data: [
                Math.floor((stats.totalTalkTime || 0) / 60),
                Math.floor((stats.totalPauseTime || 0) / 60)
              ],
              backgroundColor: ['#2E86AB', '#f59e0b'],
              borderWidth: 0,
              borderRadius: 8
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                grid: {
                  color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                  font: { size: 11 }
                }
              },
              x: {
                grid: {
                  display: false
                },
                ticks: {
                  font: { size: 11 }
                }
              }
            },
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                callbacks: {
                  label: (context) => `${context.parsed.y} minutos`
                }
              }
            }
          }
        });
      }
    }
  }

  /**
   * Destruye las gráficas
   */
  private destroyCharts(): void {
    if (this.callsChart) {
      this.chartService.destroyChart(this.callsChart);
      this.callsChart = null;
    }
    if (this.performanceChart) {
      this.chartService.destroyChart(this.performanceChart);
      this.performanceChart = null;
    }
  }

  /**
   * Verifica alertas de agentes en pausa prolongada
   */
  private checkPauseAlerts(): void {
    this.agents.forEach(agent => {
      if (agent.status === 'paused' && agent.timeInState > this.PAUSE_ALERT_THRESHOLD) {
        const agentId = agent.extension;
        
        // Solo alertar una vez por agente
        if (!this.alertedAgents.has(agentId)) {
          this.toast.warning(
            `⚠️ Agente ${agent.name} (Ext. ${agent.extension}) lleva más de 15 minutos en pausa`,
            5000
          );
          this.alertedAgents.add(agentId);
        }
      } else {
        // Si el agente ya no está en pausa prolongada, remover de alertados
        const agentId = agent.extension;
        if (this.alertedAgents.has(agentId) && agent.status !== 'paused') {
          this.alertedAgents.delete(agentId);
        }
      }
    });
  }

  /**
   * Verifica si un agente está en pausa prolongada
   */
  isLongPause(agent: any): boolean {
    return agent.status === 'paused' && agent.timeInState > this.PAUSE_ALERT_THRESHOLD;
  }

  /**
   * Obtiene el badge de alerta para un agente
   */
  getAlertBadge(agent: any): string {
    if (this.isLongPause(agent)) {
      return '⚠️ Pausa prolongada';
    }
    return '';
  }
}