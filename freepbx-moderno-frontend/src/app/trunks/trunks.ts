// src/app/trunks/trunks.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';

//Estos imports son para las notificiaciones y modales
import { ToastService } from '../core/toast.service'; // Notificaciones
import { ConfirmationService } from '../core/confirmation.service'; //Modales
import { ExportService } from '../core/export.service'; //Exportar datos

@Component({
  selector: 'app-trunks',
  standalone: true,
  templateUrl: './trunks.html',
  styleUrls: ['./trunks.css']
})
export class TrunksComponent implements OnInit {
  trunks: any[] = [];
  loading = false;

  constructor(
  private api: ApiService,
  private cdr: ChangeDetectorRef,
  private toast: ToastService, // Notificaciones
  private confirmation: ConfirmationService, //Modales
  private exportService: ExportService //Exportar datos
) {}

  loadTrunks() {
    console.log('loadTrunks ejecutado');
    this.loading = true;
    this.api.getTrunks().subscribe({
      next: (data) => {
        console.log('Troncales actualizadas:', data);
        this.trunks = data || [];
        this.loading = false;
        this.cdr.detectChanges();
        this.toast.success(`${this.trunks.length} troncales cargadas correctamente`); // Notificación de éxito
      },
      error: (err) => {
        console.error('Error:', err);
        this.loading = false;
        this.toast.error('Error al cargar troncales. Por favor, intenta de nuevo.'); // Notificación de error
        // alert('Error al cargar troncales. Revisa la consola.'); // Mensaje de alerta simple
        this.toast.info('Si el problema persiste, contacta al soporte técnico.'); // Mensaje de información adicional
      }
    });
  }


  ngOnInit(): void {
    this.loadTrunks(); // Cargar troncales al iniciar el componente
  }

// Agregar método:
exportTrunks() {
  if (this.trunks.length === 0) {
    alert('No hay troncales para exportar');
    return;
  }

  const headers = ['Canal ID', 'Nombre', 'Tecnología'];
  
  const data = this.trunks.map(trunk => [
    trunk.channelid,
    trunk.name,
    trunk.tech
  ]);

  this.exportService.exportToCSV(
    data,
    `troncales_${new Date().toISOString().split('T')[0]}`,
    headers
  );
}

}
