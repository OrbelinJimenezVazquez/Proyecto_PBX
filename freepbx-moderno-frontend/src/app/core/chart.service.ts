// src/app/core/chart.service.ts
import { Injectable } from '@angular/core';
import { Chart, ChartConfiguration, ChartType } from 'chart.js';

export interface ChartColors {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  danger: string;
  info: string;
  purple: string;
  gradient: {
    primary: string[];
    success: string[];
    danger: string[];
    info: string[];
  };
}

@Injectable({
  providedIn: 'root'
})
export class ChartService {
  private readonly colors: ChartColors = {
    primary: '#2E86AB',
    secondary: '#56cfe1',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#3b82f6',
    purple: '#8b5cf6',
    gradient: {
      primary: ['#2E86AB', '#56cfe1'],
      success: ['#10b981', '#34d399'],
      danger: ['#ef4444', '#f87171'],
      info: ['#3b82f6', '#60a5fa']
    }
  };

  private readonly fontFamily = 'Inter, sans-serif';

  /**
   * Destruye un gráfico de manera segura
   */
  destroyChart(chart: Chart | null): void {
    if (chart) {
      try {
        chart.destroy();
      } catch (error) {
        console.warn('Error al destruir gráfico:', error);
      }
    }
  }

  /**
   * Crea un gradiente para gráficos
   */
  createGradient(ctx: any, colors: string[], horizontal: boolean = false): CanvasGradient {
    const gradient = horizontal
      ? ctx.createLinearGradient(0, 0, ctx.canvas.width, 0)
      : ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    
    gradient.addColorStop(0, colors[0]);
    gradient.addColorStop(1, colors[1]);
    
    return gradient;
  }

  /**
   * Crea gráfica de dona para estado de llamadas
   */
  createStatusChart(canvas: HTMLCanvasElement, data: any): Chart | null {
    if (!canvas || !data) return null;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const config: ChartConfiguration<'doughnut'> = {
      type: 'doughnut',
      data: {
        labels: ['Contestadas', 'No contestadas', 'Fallidas', 'Ocupadas'],
        datasets: [{
          data: [
            data.answered || 0,
            data.no_answer || 0,
            data.failed || 0,
            data.busy || 0
          ],
          backgroundColor: [
            this.colors.success,
            this.colors.danger,
            this.colors.warning,
            this.colors.purple
          ],
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
              font: { size: 12, family: this.fontFamily },
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            callbacks: {
              label: (context) => {
                const label = context.label || '';
                const value = context.parsed || 0;
                const total = context.dataset.data.reduce((a: number, b: any) => a + (b || 0), 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    };

    return new Chart(ctx, config);
  }

  /**
   * Crea gráfica de tendencias
   */
  createTrendChart(
    canvas: HTMLCanvasElement, 
    data: any[], 
    chartType: 'line' | 'bar' | 'area' = 'line',
    showComparison: boolean = false
  ): Chart | null {
    if (!canvas || !data || data.length === 0) return null;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const labels = data.map((d: any) => {
      const date = new Date(d.date);
      return date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' });
    });

    const type = chartType === 'area' ? 'line' : chartType;
    const fill = chartType === 'area';

    // Dataset principal
    const datasets: any[] = [{
      label: 'Total de llamadas',
      data: data.map((d: any) => d.total || 0),
      backgroundColor: fill ? this.createGradient(ctx, this.colors.gradient.primary) : this.colors.primary,
      borderColor: this.colors.primary,
      borderWidth: 3,
      fill,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: '#ffffff',
      pointBorderWidth: 2,
      pointHoverBorderWidth: 3
    }];

    // Agregar dataset de comparación si está activado
    if (showComparison) {
      datasets.push({
        label: 'Llamadas contestadas',
        data: data.map((d: any) => d.answered || 0),
        backgroundColor: fill ? this.createGradient(ctx, this.colors.gradient.success) : this.colors.success,
        borderColor: this.colors.success,
        borderWidth: 3,
        fill,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#ffffff',
        pointBorderWidth: 2,
        pointHoverBorderWidth: 3
      });
    }

    const config: ChartConfiguration = {
      type: type as ChartType,
      data: {
        labels,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: { 
            display: showComparison,
            position: 'top',
            labels: {
              padding: 15,
              font: { size: 12, family: this.fontFamily, weight: 500 },
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 13 },
            borderColor: this.colors.primary,
            borderWidth: 1,
            displayColors: true
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            border: { display: false },
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
            ticks: {
              font: { size: 11, family: this.fontFamily },
              padding: 8
            }
          },
          x: {
            border: { display: false },
            grid: { display: false },
            ticks: {
              font: { size: 11, family: this.fontFamily },
              padding: 8
            }
          }
        },
        animation: {
          duration: 1000,
          easing: 'easeInOutQuart'
        }
      }
    };

    return new Chart(ctx, config);
  }

  /**
   * Crea gráfica de barras horizontales para agentes
   */
  createAgentChart(canvas: HTMLCanvasElement, data: any[]): Chart | null {
    if (!canvas || !data || data.length === 0) return null;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    // Mostrar todos los agentes disponibles
    const topAgents = data;

    const config: ChartConfiguration<'bar'> = {
      type: 'bar',
      data: {
        labels: topAgents.map((a: any) => a.name || a.extension),
        datasets: [{
          label: 'Llamadas contestadas',
          data: topAgents.map((a: any) => a.answered_calls || 0),
          backgroundColor: this.createGradient(ctx, this.colors.gradient.success, true),
          borderColor: this.colors.success,
          borderWidth: 2,
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: 'rgba(0, 0, 0, 0.05)' }
          },
          y: {
            grid: { display: false }
          }
        }
      }
    };

    return new Chart(ctx, config);
  }

  /**
   * Crea gráfica de dona para distribución de destinos
   */
  createDestinationChart(canvas: HTMLCanvasElement, data: any[]): Chart | null {
    if (!canvas || !data || data.length === 0) return null;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const config: ChartConfiguration<'doughnut'> = {
      type: 'doughnut',
      data: {
        labels: data.map((d: any) => d.type),
        datasets: [{
          data: data.map((d: any) => d.calls || 0),
          backgroundColor: [
            this.colors.primary,
            this.colors.success,
            this.colors.warning,
            this.colors.info,
            this.colors.purple
          ],
          borderWidth: 3,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 12,
              font: { size: 11, family: this.fontFamily }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12
          }
        }
      }
    };

    return new Chart(ctx, config);
  }

  /**
   * Crea gráfica de barras para distribución por hora
   */
  createHourlyChart(canvas: HTMLCanvasElement, data: any[], showComparison: boolean = false): Chart | null {
    if (!canvas) return null;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    // Crear array de 24 horas con valores
    const hours = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);
    const callsByHour = Array.from({ length: 24 }, (_, i) => {
      const hourData = data?.find((h: any) => h.hour === i);
      return hourData ? hourData.calls : 0;
    });

    // Dataset principal
    const datasets: any[] = [{
      label: 'Total de llamadas',
      data: callsByHour,
      backgroundColor: this.createGradient(ctx, this.colors.gradient.info, false),
      borderColor: this.colors.info,
      borderWidth: 2,
      borderRadius: 6
    }];

    // Agregar dataset de comparación si está activado
    if (showComparison) {
      const answeredByHour = Array.from({ length: 24 }, (_, i) => {
        const hourData = data?.find((h: any) => h.hour === i);
        return hourData ? (hourData.answered || 0) : 0;
      });

      datasets.push({
        label: 'Llamadas contestadas',
        data: answeredByHour,
        backgroundColor: this.createGradient(ctx, this.colors.gradient.success, false),
        borderColor: this.colors.success,
        borderWidth: 2,
        borderRadius: 6
      });
    }

    const config: ChartConfiguration<'bar'> = {
      type: 'bar',
      data: {
        labels: hours,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { 
            display: showComparison,
            position: 'top',
            labels: {
              padding: 15,
              font: { size: 12, family: this.fontFamily, weight: 500 },
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            callbacks: {
              label: (context) => `${context.dataset.label}: ${context.parsed.y}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
            ticks: { 
              precision: 0,
              font: { size: 11, family: this.fontFamily }
            }
          },
          x: {
            grid: { display: false },
            ticks: {
              font: { size: 10, family: this.fontFamily }
            }
          }
        }
      }
    };

    return new Chart(ctx, config);
  }
}
