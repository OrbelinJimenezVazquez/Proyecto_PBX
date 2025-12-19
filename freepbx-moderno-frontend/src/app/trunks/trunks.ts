// src/app/trunks/trunks.ts
import { Component, OnInit } from '@angular/core';
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

  constructor(private api: ApiService) {}

  loadTrunks() {
    this.loading = true;
    this.api.getTrunks().subscribe({
      next: (data) => {
        console.log('Troncales recibidas:', data);
        this.trunks = data || [];
        this.loading = false;
      },
      error: (err) => {
        console.error('Error al cargar troncales', err);
        this.loading = false;
        alert('No se pudieron cargar las troncales.');
      }
    });
  }

  ngOnInit(): void {
    this.loadTrunks();
  }
}