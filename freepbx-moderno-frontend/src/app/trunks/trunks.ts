// src/app/trunks/trunks.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';

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
      },
      error: (err) => {
        console.error('Error:', err);
        this.loading = false;
        alert('Error al cargar troncales');
      }
    });
  }
  

  ngOnInit(): void {
    this.loadTrunks(); // solo llama, no define
  }
  
}