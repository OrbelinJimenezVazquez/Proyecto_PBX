import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../core/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class DashboardComponent implements OnInit {
  stats: any = {};
  loading = false;

  constructor(
  private api: ApiService,
  private cdr: ChangeDetectorRef
) {}

  loadStats() {
    this.loading = true;
    this.api.getDashboardStats().subscribe({
      next: (data) => {
        this.stats = data;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error:', err);
        this.loading = false;
      }
    });
  }

  ngOnInit(): void {
    this.loadStats();
  }
}