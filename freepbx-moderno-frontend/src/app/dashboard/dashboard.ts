//src/app/dashboard/dashboard.ts
import { Component, OnInit, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';

// Importar Chart.js
declare var Chart: any;

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css'],
  imports: []
})
export class DashboardComponent implements OnInit {
  stats: any = {};
  loading = false;

  @ViewChild('hourlyChart') hourlyChartRef!: ElementRef;
  @ViewChild('dailyChart') dailyChartRef!: ElementRef;
  @ViewChild('destChart') destChartRef!: ElementRef;

  hourlyChart: any;
  dailyChart: any;
  destChart: any;

constructor(
  private api: ApiService,
  private cdr: ChangeDetectorRef
) {}

  loadStats() {
    this.loading = true;
    this.api.getAdvancedDashboardStats().subscribe({
      next: (data) => {
        this.stats = data;
        this.loading = false;
        this.cdr.detectChanges();
        // Crear los gráficos después de un pequeño retraso para asegurar que las vistas estén listas
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

  createCharts() {
    // Gráfico de llamadas por hora
    if (this.hourlyChartRef) {
      const ctx1 = this.hourlyChartRef.nativeElement.getContext('2d');
      this.hourlyChart = new Chart(ctx1, {
        type: 'bar',
        data: {
          labels: this.stats.hourly_calls.map((h: any) => `${h.hour}:00`),
          datasets: [{
            label: 'Llamadas por hora',
            data: this.stats.hourly_calls.map((h: any) => h.calls),
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

    // Gráfico de tendencias diarias
    if (this.dailyChartRef) {
      const ctx2 = this.dailyChartRef.nativeElement.getContext('2d');
      this.dailyChart = new Chart(ctx2, {
        type: 'line',
        data: {
          labels: this.stats.daily_trends.map((d: any) => d.date),
          datasets: [
            {
              label: 'Total',
              data: this.stats.daily_trends.map((d: any) => d.total),
              borderColor: 'rgba(34, 197, 94, 1)',
              tension: 0.1
            },
            {
              label: 'Contestadas',
              data: this.stats.daily_trends.map((d: any) => d.answered),
              borderColor: 'rgba(59, 130, 246, 1)',
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

    // Gráfico de distribución de destinos
    if (this.destChartRef) {
      const ctx3 = this.destChartRef.nativeElement.getContext('2d');
      this.destChart = new Chart(ctx3, {
        type: 'doughnut',
        data: {
          labels: this.stats.destination_distribution.map((d: any) => d.destination),
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

  downloadPdf() {
    // Lógica para descargar el dashboard como PDF
    alert('Funcionalidad de descarga de PDF no implementada aún.');
  }

  ngOnInit(): void {
    this.loadStats();
  }

  ngOnDestroy() {
    if (this.hourlyChart) this.hourlyChart.destroy();
    if (this.dailyChart) this.dailyChart.destroy();
    if (this.destChart) this.destChart.destroy();
  }
}