// src/app/dashboard/dashboard.component.ts
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../core/api.service';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css'],
  providers: [DatePipe]
})
export class DashboardComponent implements OnInit {
  calls: any[] = [];
  loading = true;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
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
}