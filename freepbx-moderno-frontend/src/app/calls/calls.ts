// src/app/calls/calls.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-calls',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './calls.html',
  styleUrls: ['./calls.css']
})
export class CallsComponent implements OnInit {
  calls: any[] = [];
  loading = false;
  currentPeriod: 'today' | 'week' | 'month' | 'year' = 'month';
  
  // Paginación
  currentPage = 1;
  totalPages = 1;
  totalCalls = 0;
  pageSize = 50;

constructor(
  private api: ApiService,
  private cdr: ChangeDetectorRef
) {}

  loadCalls(page: number = 1) {
    this.loading = true;
    this.currentPage = page;
    
    this.api.getDetailedCalls(this.currentPeriod, page, this.pageSize).subscribe({
      next: (response) => {
        this.calls = response.items || [];
        this.totalCalls = response.total;
        this.totalPages = response.pages;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error al cargar llamadas', err);
        this.loading = false;
        alert('Error al cargar llamadas. Revisa la consola.');
      }
    });
  }

  changePeriod(period: 'today' | 'week' | 'month' | 'year') {
    this.currentPeriod = period;
    this.currentPage = 1;
    this.loadCalls(1);
  }

  // Navegación de paginación
  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.loadCalls(page);
    }
  }

  ngOnInit(): void {
    this.loadCalls(1);
  }

  viewDetails(call: any) {
    console.log('Detalles:', call);
    // Implementar modal o página de detalle
  }
}