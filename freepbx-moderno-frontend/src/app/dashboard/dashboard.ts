import { Component, OnInit, ViewChild, ElementRef, AfterViewInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';
import { PdfService } from '../core/pdf.service';
import { DecimalPipe } from '@angular/common';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DecimalPipe, ],
  template: `
    <div #dashboardContainer class="space-y-6">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between mb-8">
        <div class="flex items-center mb-4 md:mb-0">
          <span class="material-icons-outlined text-primary text-3xl mr-3">help_outline</span>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        </div>
        <div class="flex space-x-3">
          <button 
            (click)="downloadPdf()" 
            [disabled]="loading"
            class="flex items-center px-4 py-2 border border-primary text-primary dark:text-indigo-400 dark:border-indigo-400 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors text-sm font-medium">
            <span class="material-icons-outlined text-lg mr-2">download</span>
            Exportar PDF
          </button>
          <button 
            (click)="loadStats()" 
            [disabled]="loading"
            class="flex items-center px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg shadow-md transition-colors text-sm font-medium">
            <span class="material-icons-outlined text-lg mr-2">refresh</span>
            {{ loading ? 'Cargando...' : 'Actualizar' }}
          </button>
        </div>
      </div>

      <!-- Stats Grid -->
      @if (!loading) {
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
          <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm p-6 border-l-[6px] border-purple-600 relative overflow-hidden transition-all duration-300 hover:shadow-md">
            <div class="flex justify-between items-start">
              <div>
                <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-1">{{ stats.general?.calls_today || 0 }}</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Llamadas Hoy</p>
              </div>
              <div class="h-10 w-10 rounded-lg bg-purple-600 text-white flex items-center justify-center shadow-lg shadow-purple-200 dark:shadow-none">
                <span class="material-icons-outlined">call</span>
              </div>
            </div>
          </div>

          <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm p-6 border-l-[6px] border-sky-400 relative overflow-hidden transition-all duration-300 hover:shadow-md">
            <div class="flex justify-between items-start">
              <div>
                <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-1">{{ stats.general?.calls_this_week || 0 }}</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Llamadas Esta Semana</p>
              </div>
              <div class="h-10 w-10 rounded-lg bg-sky-400 text-white flex items-center justify-center shadow-lg shadow-sky-200 dark:shadow-none">
                <span class="material-icons-outlined">calendar_today</span>
              </div>
            </div>
          </div>

          <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm p-6 border-l-[6px] border-emerald-400 relative overflow-hidden transition-all duration-300 hover:shadow-md">
            <div class="flex justify-between items-start">
              <div>
                <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-1">{{ stats.general?.calls_this_month || 0 }}</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Llamadas Este Mes</p>
              </div>
              <div class="h-10 w-10 rounded-lg bg-emerald-400 text-white flex items-center justify-center shadow-lg shadow-emerald-200 dark:shadow-none">
                <span class="material-icons-outlined">calendar_month</span>
              </div>
            </div>
          </div>

          <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm p-6 border-l-[6px] border-orange-400 relative overflow-hidden transition-all duration-300 hover:shadow-md">
            <div class="flex justify-between items-start">
              <div>
                <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-1">{{ stats.general?.answer_rate || 0 }}%</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">Tasa de Respuesta</p>
              </div>
              <div class="h-10 w-10 rounded-lg bg-orange-400 text-white flex items-center justify-center shadow-lg shadow-orange-200 dark:shadow-none">
                <span class="material-icons-outlined">trending_up</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Charts Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm p-6">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">Estado de Llamadas</h3>
            <canvas #statusChart class="w-full h-64"></canvas>
          </div>

          <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm p-6">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">Tendencia de Llamadas</h3>
            <canvas #trendChart class="w-full h-64"></canvas>
          </div>

          <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm p-6">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">Top Agentes</h3>
            <canvas #agentChart class="w-full h-64"></canvas>
          </div>

          <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm p-6">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">Distribución por Tipo</h3>
            <canvas #destChart class="w-full h-64"></canvas>
          </div>
        </div>

        <!-- Top Agents Table -->
        <div class="bg-card-light dark:bg-card-dark rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div class="p-6 border-b border-gray-100 dark:border-gray-700 flex flex-col sm:flex-row justify-between items-center gap-4">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white">Top Agentes (últimos 7 días)</h3>
            <button class="text-primary hover:text-primary-hover font-medium text-sm px-4 py-2 border border-primary/30 rounded-lg hover:bg-primary/5 transition-colors w-full sm:w-auto text-center">
              Ver Todos
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-gray-50 dark:bg-gray-800/50 text-xs uppercase text-gray-500 dark:text-gray-400 font-semibold tracking-wider">
                  <th class="px-6 py-4">Agente</th>
                  <th class="px-6 py-4">Extensión</th>
                  <th class="px-6 py-4">Total Llamadas</th>
                  <th class="px-6 py-4">Contestadas</th>
                  <th class="px-6 py-4">Tasa de Respuesta</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100 dark:divide-gray-700 text-sm">
                @for (agent of stats.top_agents || []; track agent.extension) {
                  <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                    <td class="px-6 py-4 font-medium text-gray-600 dark:text-gray-300">{{ agent.name }}</td>
                    <td class="px-6 py-4 text-gray-800 dark:text-white">{{ agent.extension }}</td>
                    <td class="px-6 py-4 text-gray-500 dark:text-gray-400">{{ agent.total_calls }}</td>
                    <td class="px-6 py-4 text-gray-800 dark:text-white font-medium">{{ agent.answered_calls }}</td>
                    <td class="px-6 py-4">
                      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300">
                        {{ agent.answered_calls > 0 ? (agent.answered_calls / agent.total_calls * 100 | number:'1.1-1') : 0 }}%
                      </span>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      } @else {
        <div class="flex justify-center items-center h-64">
          <p class="text-gray-500 dark:text-gray-400">Cargando métricas...</p>
        </div>
      }
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
  `]
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  stats: any = {
    general: {},
    call_status: {},
    daily_trends: [],
    top_agents: [],
    destination_distribution: []
  };
  loading = false;

  @ViewChild('dashboardContainer') dashboardContainer!: ElementRef;
  @ViewChild('statusChart') statusChartRef!: ElementRef;
  @ViewChild('trendChart') trendChartRef!: ElementRef;
  @ViewChild('agentChart') agentChartRef!: ElementRef;
  @ViewChild('destChart') destChartRef!: ElementRef;

  // Propiedades para guardar instancias de gráficos
  private statusChart: Chart | null = null;
  private trendChart: Chart | null = null;
  private agentChart: Chart | null = null;
  private destChart: Chart | null = null;

  constructor(
    private api: ApiService,
    private pdfService: PdfService,
    private cdr: ChangeDetectorRef
  ) {}
  
  loadStats(): void {
    this.loading = true;
    this.api.getAdvancedDashboardStats().subscribe({
      next: (data) => {
        this.stats = data;
        this.loading = false;
        setTimeout(() => {
          this.createCharts();
          this.cdr.detectChanges();
        }, 100);
      },
      error: (err) => {
        console.error('Error cargando estadísticas:', err);
        this.loading = false;
      }
    });
  }

  private createCharts(): void {
    this.createStatusChart();
    this.createTrendChart();
    this.createAgentChart();
    this.createDestChart();
  }

  private createStatusChart(): void {
    if (!this.statusChartRef || !this.stats.call_status) {
      return;
    }

    this.destroyChart(this.statusChart);
    
    const ctx = this.statusChartRef.nativeElement.getContext('2d');
    this.statusChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Contestadas', 'No contestadas', 'Fallidas', 'Ocupadas'],
        datasets: [{
          data: [
            this.stats.call_status.answered || 0,
            this.stats.call_status.no_answer || 0,
            this.stats.call_status.failed || 0,
            this.stats.call_status.busy || 0
          ],
          backgroundColor: [
            '#10b981', '#ef4444', '#f59e0b', '#8b5cf6'
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    });
  }

  private createTrendChart(): void {
    if (!this.trendChartRef || !this.stats.daily_trends || this.stats.daily_trends.length === 0) {
      return;
    }

    this.destroyChart(this.trendChart);
    
    const ctx = this.trendChartRef.nativeElement.getContext('2d');
    this.trendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: this.stats.daily_trends.map((d: any) => d.date),
        datasets: [
          {
            label: 'Total',
            data: this.stats.daily_trends.map((d: any) => d.total || 0),
            borderColor: 'rgba(59, 130, 246, 1)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.1
          },
          {
            label: 'Contestadas',
            data: this.stats.daily_trends.map((d: any) => d.answered || 0),
            borderColor: 'rgba(16, 185, 129, 1)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }

  private createAgentChart(): void {
    if (!this.agentChartRef || !this.stats.top_agents || this.stats.top_agents.length === 0) {
      return;
    }

    this.destroyChart(this.agentChart);
    
    const ctx = this.agentChartRef.nativeElement.getContext('2d');
    this.agentChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: this.stats.top_agents.map((a: any) => `${a.name} (${a.extension})`),
        datasets: [{
          label: 'Llamadas contestadas',
          data: this.stats.top_agents.map((a: any) => a.answered_calls || 0),
          backgroundColor: 'rgba(16, 185, 129, 0.6)',
          borderColor: 'rgba(16, 185, 129, 1)',
          borderWidth: 1
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { beginAtZero: true }
        }
      }
    });
  }

  private createDestChart(): void {
    if (!this.destChartRef || !this.stats.destination_distribution || this.stats.destination_distribution.length === 0) {
      return;
    }

    this.destroyChart(this.destChart);
    
    const ctx = this.destChartRef.nativeElement.getContext('2d');
    this.destChart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: this.stats.destination_distribution.map((d: any) => d.type),
        datasets: [{
          data: this.stats.destination_distribution.map((d: any) => d.calls || 0),
          backgroundColor: [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
            '#ec4899', '#06b6d4', '#f97316', '#64748b', '#14b8a6'
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          }
        }
      }
    });
  }

  private destroyChart(chart: Chart | null): void {
    if (chart) {
      chart.destroy();
    }
  }

  async downloadPdf(): Promise<void> {
    if (!this.dashboardContainer) {
      alert('No se puede exportar: contenedor no disponible');
      return;
    }

    try {
      await this.pdfService.generateDashboardPdf(
        this.dashboardContainer.nativeElement,
        this.stats
      );
    } catch (error) {
      console.error('Error al generar PDF:', error);
      alert('No se pudo generar el PDF. Revisa la consola para más detalles.');
    }
  }

  ngOnInit(): void {
    this.loadStats();
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      if (this.stats && Object.keys(this.stats).length > 0) {
        this.createCharts();
      }
    }, 100);
  }

  ngOnDestroy(): void {
    this.destroyChart(this.statusChart);
    this.destroyChart(this.trendChart);
    this.destroyChart(this.agentChart);
    this.destroyChart(this.destChart);
  }
}