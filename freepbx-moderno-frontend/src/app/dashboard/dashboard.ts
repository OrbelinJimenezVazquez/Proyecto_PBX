import { Component, OnInit, ViewChild, ElementRef, AfterViewInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';
import { PdfService } from '../core/pdf.service';
import { DecimalPipe } from '@angular/common';
import Chart from 'chart.js/auto';
import { MatrixController, MatrixElement } from 'chartjs-chart-matrix';

// Registrar el controlador de matriz
Chart.register(MatrixController, MatrixElement);

declare var window: any;

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  stats: any = {};
  advancedCharts: any = {};
  loading = false;
  loadingAdvanced = false;

  @ViewChild('dashboardContainer') dashboardContainer!: ElementRef;
  @ViewChild('statusChart') statusChartRef!: ElementRef;
  @ViewChild('waitChart') waitChartRef!: ElementRef;
  @ViewChild('agentChart') agentChartRef!: ElementRef;
  @ViewChild('trendChart') trendChartRef!: ElementRef;
  @ViewChild('destChart') destChartRef!: ElementRef;
  @ViewChild('heatmapChart') heatmapChartRef!: ElementRef;
  @ViewChild('monthlyChart') monthlyChartRef!: ElementRef;

  // Gráficos - Declaración de propiedades
  statusChart: any;
  waitChart: any;
  agentChart: any;
  trendChart: any;
  destChart: any;
  heatmapChart: any;
  monthlyChart: any;

  constructor(
    private api: ApiService,
    private pdfService: PdfService,
    private cdr: ChangeDetectorRef
  ) {}

  loadStats() {
    this.loading = true;
    this.api.getAdvancedDashboardStats().subscribe({
      next: (data) => {
        this.stats = data;
        this.loading = false;
        this.cdr.detectChanges();
        setTimeout(() => {
          this.createCharts();
        }, 100);
      },
      error: (err) => {
        console.error('Error:', err);
        this.loading = false;

      }
    });
  }

  loadAdvancedCharts() {
    this.loadingAdvanced = true;
    this.api.getAdvancedChartsData().subscribe({
      next: (data) => {
        this.advancedCharts = data;
        this.loadingAdvanced = false;
        this.cdr.detectChanges();
        setTimeout(() => {
          this.createAdvancedCharts();
        }, 100);
      },
      error: (err) => {
        console.error('Error en gráficos avanzados:', err);
        this.loadingAdvanced = false;
      }
    });
  }

  createCharts() {
    // 1. Gráfico de estado de llamadas (pastel)
    if (this.statusChartRef && this.stats.call_status) {
      const ctx1 = this.statusChartRef.nativeElement.getContext('2d');
      this.statusChart = new Chart(ctx1, {
        type: 'doughnut',
        data: {
          labels: ['Contestadas', 'No contestadas', 'Fallidas', 'Ocupadas'],
          datasets: [{
            data: [
              this.stats.call_status.answered,
              this.stats.call_status.no_answer,
              this.stats.call_status.failed,
              this.stats.call_status.busy
            ],
            backgroundColor: [
              '#10b981', '#ef4444', '#f59e0b', '#8b5cf6'
            ]
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }

    // 2. Tiempos de espera promedio (barras)
    if (this.waitChartRef && this.stats.wait_times && this.stats.wait_times.length > 0) {
      const ctx2 = this.waitChartRef.nativeElement.getContext('2d');
      this.waitChart = new Chart(ctx2, {
        type: 'bar',
        data: {
          labels: this.stats.wait_times.map((w: any) => w.extension),
          datasets: [{
            label: 'Tiempo de espera (seg)',
            data: this.stats.wait_times.map((w: any) => w.avg_wait_time),
            backgroundColor: 'rgba(59, 130, 246, 0.6)',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }

    // 3. Top agentes (barras horizontales)
    if (this.agentChartRef && this.stats.top_agents && this.stats.top_agents.length > 0) {
      const ctx3 = this.agentChartRef.nativeElement.getContext('2d');
      this.agentChart = new Chart(ctx3, {
        type: 'bar',
        data: {
          labels: this.stats.top_agents.map((a: any) => `${a.name} (${a.extension})`),
          datasets: [{
            label: 'Llamadas contestadas',
            data: this.stats.top_agents.map((a: any) => a.answered_calls),
            backgroundColor: 'rgba(16, 185, 129, 0.6)',
            borderColor: 'rgba(16, 185, 129, 1)',
            borderWidth: 1
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          scales: {
            x: { beginAtZero: true }
          }
        }
      });
    }

    // 4. Tendencia de llamadas (línea)
    if (this.trendChartRef && this.stats.daily_trends && this.stats.daily_trends.length > 0) {
      const ctx4 = this.trendChartRef.nativeElement.getContext('2d');
      this.trendChart = new Chart(ctx4, {
        type: 'line',
        data: {
          labels: this.stats.daily_trends.map((d: any) => d.date),
          datasets: [
            {
              label: 'Total',
              data: this.stats.daily_trends.map((d: any) => d.total),
              borderColor: 'rgba(59, 130, 246, 1)',
              tension: 0.1
            },
            {
              label: 'Contestadas',
              data: this.stats.daily_trends.map((d: any) => d.answered),
              borderColor: 'rgba(16, 185, 129, 1)',
              tension: 0.1
            }
          ]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }

    // 5. Distribución por tipo (pastel)
    if (this.destChartRef && this.stats.destination_distribution && this.stats.destination_distribution.length > 0) {
      const ctx5 = this.destChartRef.nativeElement.getContext('2d');
      this.destChart = new Chart(ctx5, {
        type: 'pie',
        data: {
          labels: this.stats.destination_distribution.map((d: any) => d.type),
          datasets: [{
            data: this.stats.destination_distribution.map((d: any) => d.calls),
            backgroundColor: [
              '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
              '#ec4899', '#06b6d4', '#f97316', '#64748b', '#14b8a6'
            ]
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
    }
  }

  createAdvancedCharts() {
    // 1. Heatmap de llamadas (hora vs día de la semana)
    if (this.heatmapChartRef && this.advancedCharts.heatmap) {
      const ctx1 = this.heatmapChartRef.nativeElement.getContext('2d');
      
      // Destruir gráfico anterior si existe
      const existingChart = Chart.getChart(ctx1);
      if (existingChart) {
        existingChart.destroy();
      }

      this.heatmapChart = new Chart(ctx1, {
        type: 'matrix' as any,
        data: {
          datasets: [{
            label: 'Heatmap de llamadas',
            data: this.advancedCharts.heatmap,
            backgroundColor: (context: any) => {
              const value = context.dataset.data[context.dataIndex]?.v || 0;
              const intensity = Math.min(value / 10, 1);
              return `rgba(255, 99, 132, ${intensity})`;
            },
            borderWidth: 1,
            borderColor: '#999'
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              display: true
            }
          },
          scales: {
            x: {
              type: 'category',
              labels: Array.from({length: 24}, (_, i) => `${i}:00`)
            },
            y: {
              type: 'category',
              labels: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
            }
          }
        } as any
      });
    }

    // 2. Comparativa mensual
    if (this.monthlyChartRef && this.advancedCharts.monthly_comparison && this.advancedCharts.monthly_comparison.length > 0) {
      const ctx2 = this.monthlyChartRef.nativeElement.getContext('2d');
      this.monthlyChart = new Chart(ctx2, {
        type: 'bar',
        data: {
          labels: this.advancedCharts.monthly_comparison.map((m: any) => m.month),
          datasets: [
            {
              label: 'Total Llamadas',
              data: this.advancedCharts.monthly_comparison.map((m: any) => m.total_calls),
              backgroundColor: 'rgba(59, 130, 246, 0.6)',
              borderColor: 'rgba(59, 130, 246, 1)',
              borderWidth: 1
            },
            {
              label: 'Llamadas Contestadas',
              data: this.advancedCharts.monthly_comparison.map((m: any) => m.answered_calls),
              backgroundColor: 'rgba(16, 185, 129, 0.6)',
              borderColor: 'rgba(16, 185, 129, 1)',
              borderWidth: 1
            }
          ]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }
  }

  async downloadPdf() {
    if (this.dashboardContainer) {
      try {
        await this.pdfService.generateDashboardPdf(
          this.dashboardContainer.nativeElement,
          this.stats
        );
      } catch (error) {
        console.error('Error al generar PDF:', error);
        alert('No se pudo generar el PDF. Revisa la consola.');
      }
    }
  }

  ngOnInit(): void {
    this.loadStats();
    this.loadAdvancedCharts();
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      if (this.stats && Object.keys(this.stats).length > 0) {
        this.createCharts();
      }
      if (this.advancedCharts && Object.keys(this.advancedCharts).length > 0) {
        this.createAdvancedCharts();
      }
    }, 100);
  }

  ngOnDestroy(): void {
    [this.statusChart, this.waitChart, this.agentChart, this.trendChart, this.destChart, this.heatmapChart, this.monthlyChart]
      .filter((chart: any) => chart)
      .forEach((chart: any) => chart.destroy());
  }

  printDashboard() {
  window.print();
}
}