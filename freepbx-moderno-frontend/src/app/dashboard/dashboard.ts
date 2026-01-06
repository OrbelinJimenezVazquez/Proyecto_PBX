// src/app/dashboard/dashboard.ts
import { Component, OnInit, ViewChild, ElementRef, AfterViewInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';
import { PdfService } from '../core/pdf.service';
import { ChartService } from '../core/chart.service';
import { DecimalPipe, CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart, registerables } from 'chart.js';
import { ToastService } from '../core/toast.service';
import { ConfirmationService } from '../core/confirmation.service';
import { catchError, finalize } from 'rxjs/operators';
import { of } from 'rxjs';

Chart.register(...registerables);

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [DecimalPipe, CommonModule, FormsModule],
  templateUrl: `./dashboard.html`,
  styleUrls: [`./dashboard.css`]
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  stats: any = {
    general: {},
    call_status: {},
    daily_trends: [],
    top_agents: [],
    destination_distribution: [],
    hourly_distribution: []
  };
  
  loading = false;
  error = false;
  errorMessage = '';
  
  // Filtros
  selectedPeriod: 'today' | 'week' | 'month' | 'year' = 'week';
  selectedChartType: 'line' | 'bar' | 'area' = 'line';
  showComparison = false;

  @ViewChild('dashboardContainer') dashboardContainer!: ElementRef;
  @ViewChild('statusChart') statusChartRef!: ElementRef;
  @ViewChild('trendChart') trendChartRef!: ElementRef;
  @ViewChild('agentChart') agentChartRef!: ElementRef;
  @ViewChild('destChart') destChartRef!: ElementRef;
  @ViewChild('hourlyChart') hourlyChartRef!: ElementRef;

  private statusChart: Chart | null = null;
  private trendChart: Chart | null = null;
  private agentChart: Chart | null = null;
  private destChart: Chart | null = null;
  private hourlyChart: Chart | null = null;

  constructor(
    private api: ApiService,
    private pdfService: PdfService,
    private chartService: ChartService,
    private cdr: ChangeDetectorRef, 
    private toast: ToastService,
    private confirmation: ConfirmationService
  ) {}

  ngOnInit(): void {
    this.loadStats();
  }

  ngAfterViewInit(): void {
    // Los gráficos se crearán después de cargar los datos
  }

  ngOnDestroy(): void {
    this.destroyAllCharts();
  }

  /**
   * Carga las estadísticas del dashboard con manejo de errores
   */
  loadStats(): void {
    this.loading = true;
    this.error = false;
    this.errorMessage = '';
    
    this.api.getAdvancedDashboardStats({ period: this.selectedPeriod }).pipe(
      catchError((err) => {
        console.error('Error cargando estadísticas:', err);
        this.error = true;
        this.errorMessage = err?.error?.detail || 'Error al cargar estadísticas del dashboard';
        this.toast.error(this.errorMessage);
        return of(null);
      }),
      finalize(() => {
        this.loading = false;
        this.cdr.detectChanges();
      })
    ).subscribe({
      next: (data) => {
        if (data) {
          this.stats = data;
          setTimeout(() => this.createAllCharts(), 100);
          this.toast.success('Dashboard actualizado correctamente');
        }
      }
    });
  }

  changePeriod(period: 'today' | 'week' | 'month' | 'year'): void {
    if (this.selectedPeriod === period) return;
    this.selectedPeriod = period;
    this.loadStats();
  }

  changeChartType(type: 'line' | 'bar' | 'area'): void {
    if (this.selectedChartType === type) return;
    this.selectedChartType = type;
    this.createTrendChart();
  }

  toggleComparison(): void {
    this.showComparison = !this.showComparison;
    this.createTrendChart();
  }

  /**
   * Crea todas las gráficas del dashboard
   */
  private createAllCharts(): void {
    if (this.error) return;

    setTimeout(() => {
      try {
        this.createStatusChart();
        this.createTrendChart();
        this.createAgentChart();
        this.createDestChart();
        this.createHourlyChart();
      } catch (error) {
        console.error('Error creando gráficas:', error);
        this.toast.error('Error al crear gráficas');
      }
    }, 50);
  }

  /**
   * Destruye todas las gráficas de manera segura
   */
  private destroyAllCharts(): void {
    this.chartService.destroyChart(this.statusChart);
    this.chartService.destroyChart(this.trendChart);
    this.chartService.destroyChart(this.agentChart);
    this.chartService.destroyChart(this.destChart);
    this.chartService.destroyChart(this.hourlyChart);
    
    this.statusChart = null;
    this.trendChart = null;
    this.agentChart = null;
    this.destChart = null;
    this.hourlyChart = null;
  }

  /**
   * Crea gráfica de estado de llamadas usando el servicio
   */
  private createStatusChart(): void {
    if (!this.statusChartRef?.nativeElement || !this.stats.call_status) return;
    
    this.chartService.destroyChart(this.statusChart);
    this.statusChart = this.chartService.createStatusChart(
      this.statusChartRef.nativeElement,
      this.stats.call_status
    );
  }

  /**
   * Crea gráfica de tendencias con soporte para comparación
   */
  private createTrendChart(): void {
    if (!this.trendChartRef?.nativeElement || !this.stats.daily_trends?.length) return;
    
    this.chartService.destroyChart(this.trendChart);
    this.trendChart = this.chartService.createTrendChart(
      this.trendChartRef.nativeElement,
      this.stats.daily_trends,
      this.selectedChartType,
      this.showComparison
    );
  }

  /**
   * Crea gráfica de mejores agentes
   */
  private createAgentChart(): void {
    if (!this.agentChartRef?.nativeElement || !this.stats.top_agents?.length) return;
    
    this.chartService.destroyChart(this.agentChart);
    this.agentChart = this.chartService.createAgentChart(
      this.agentChartRef.nativeElement,
      this.stats.top_agents
    );
  }

  /**
   * Crea gráfica de distribución de destinos
   */
  private createDestChart(): void {
    if (!this.destChartRef?.nativeElement || !this.stats.destination_distribution?.length) return;
    
    this.chartService.destroyChart(this.destChart);
    this.destChart = this.chartService.createDestinationChart(
      this.destChartRef.nativeElement,
      this.stats.destination_distribution
    );
  }

  /**
   * Crea gráfica de distribución por hora
   */
  private createHourlyChart(): void {
    if (!this.hourlyChartRef?.nativeElement) return;
    
    this.chartService.destroyChart(this.hourlyChart);
    this.hourlyChart = this.chartService.createHourlyChart(
      this.hourlyChartRef.nativeElement,
      this.stats.hourly_distribution || [],
      this.showComparison
    );
  }

  /**
   * Exporta el dashboard a PDF con manejo de errores
   */
  async downloadPdf(): Promise<void> {
    if (!this.dashboardContainer) {
      this.toast.error('No se puede exportar: contenedor no disponible');
      return;
    }

    try {
      await this.pdfService.generateDashboardPdf(
        this.dashboardContainer.nativeElement,
        this.stats
      );
      this.toast.success('PDF exportado correctamente');
    } catch (error) {
      console.error('Error al generar PDF:', error);
      this.toast.error('No se pudo generar el PDF');
    }
  }
}