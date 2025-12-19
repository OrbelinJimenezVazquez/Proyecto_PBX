// src/app/calls/calls.component.ts
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../core/api.service';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-calls',
  standalone: true,
  templateUrl: './calls.html',
  styleUrls: ['./calls.css'],
  imports: [DatePipe]
})
export class CallsComponent implements OnInit {
  calls: any[] = [];
  loading = false;

  constructor(private api: ApiService) {}

  loadCalls() {
    this.api.getRecentCalls().subscribe({
      next: (data) => {
        this.calls = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error al cargar llamadas', err);
        this.loading = false;
      }
    });
  }

ngOnInit(): void {
    this.api.getRecentCalls().subscribe({
      next: (data) => {
        this.loadCalls();
        this.calls = data;
        this.loading = true;
      },
      error: (err) => {
        console.error('Error al cargar llamadas', err);
        this.loading = false;
      }
    });
  }
}
