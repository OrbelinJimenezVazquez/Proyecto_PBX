// src/app/route-detail/route-detail.ts
import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';

@Component({
  selector: 'app-route-detail',
  standalone: true,
  templateUrl: './route-detail.html',
  styleUrls: ['./route-detail.css']
})
export class RouteDetailComponent implements OnInit, OnChanges {
  @Input() routeNumber!: string;
  @Output() close = new EventEmitter<void>();

  loading = false;
  detail: any = null;
  error: string | null = null;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    if (this.routeNumber) {
      this.fetchDetail();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['routeNumber'] && !changes['routeNumber'].firstChange) {
      this.fetchDetail();
    }
  }

  fetchDetail() {
    this.loading = true;
    this.error = null;
    this.api.getRouteDetail(this.routeNumber).subscribe({
      next: (data) => {
        this.detail = data;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error al cargar detalle de ruta', err);
        this.error = 'No se pudo cargar el detalle.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  onClose() {
    this.close.emit();
  }
}