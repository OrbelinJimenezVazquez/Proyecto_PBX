//src/app/incoming-routes/incoming-routes.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';
import { RouteDetailComponent } from '../route-detail/route-detail';

@Component({
  selector: 'app-incoming-routes',
  templateUrl: './incoming-routes.html',
  styleUrls: ['./incoming-routes.css'],
  imports: [
    RouteDetailComponent,
  ],
})
export class IncomingRoutesComponent implements OnInit {
  routes: any[] = [];
  loading = false;
  
  // Para el modal
  selectedRouteNumber: string | null = null;
  showDetailModal = false;

  constructor(
  private api: ApiService,
  private cdr: ChangeDetectorRef
) {}

  loadRoutes() {
    this.loading = true;
    this.api.getIncomingRoutes().subscribe({
      next: (data) => {
        this.routes = data || [];
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error al cargar rutas entrantes', err);
        this.loading = false;
        alert('Error al cargar rutas entrantes. Revisa la consola.');
      }
    });
  }

  viewDetails(route: any) {
    this.selectedRouteNumber = route.extension ?? route.numero ?? '';
    this.showDetailModal = true;
  }

  closeModal() {
    this.showDetailModal = false;
    this.selectedRouteNumber = null;
  }

  ngOnInit(): void {
    this.loadRoutes();
  }
}