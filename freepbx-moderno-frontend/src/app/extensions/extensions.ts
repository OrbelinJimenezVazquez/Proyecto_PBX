// src/app/extensions/extensions.component.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';

@Component({
  selector: 'app-extensions',
  standalone: true,
  templateUrl: './extensions.html',
  styleUrls: ['./extensions.css']
})
export class ExtensionsComponent implements OnInit {
  extensions: any[] = [];
  loading = false;

  loadExtensions() {
  this.api.getExtensions().subscribe({
    next: (data) => {
      console.log('Datos recibidos:', data);
      this.extensions = data || [];
      this.loading = false; 
    },
    error: (err) => {
      console.error('Error en API:', err);
      this.loading = false;
      alert('No se pudieron cargar las extensiones. Revisa la consola.');
    }
  });
}

  constructor(
  private api: ApiService,
  private cdr: ChangeDetectorRef,
) {}

  ngOnInit(): void {
    this.api.getExtensions().subscribe({
      next: (data) => {
        this.loadExtensions();
        console.log('Extensiones recibidas:', data);
        this.extensions = data;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error al cargar extensiones', err);
        this.loading = false;
      }
    });
  }
}