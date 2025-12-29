// src/app/route-detail/route-detail.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { ApiService } from '../core/api.service';

@Component({
  selector: 'app-route-detail',
  templateUrl: './route-detail.html',
  styleUrls: ['./route-detail.css']
})
export class RouteDetailComponent {
  @Input() routeNumber: string = '';
  @Output() close = new EventEmitter<void>();
  
  routeDetail: any = null;
  loading = false;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadDetail();
  }

  loadDetail() {
    if (!this.routeNumber) return;
    
    this.loading = true;
    this.error = '';
    
    this.api.getRouteDetail(this.routeNumber).subscribe({
      next: (data) => {
        this.routeDetail = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error:', err);
        this.error = 'No se pudo cargar el detalle de la ruta.';
        this.loading = false;
      }
    });
  }

  closeModal() {
    this.close.emit();
  }
}