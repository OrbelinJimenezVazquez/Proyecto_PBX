import { Component, OnInit } from '@angular/core';
import { ApiService } from '../core/api.service';

@Component({
  selector: 'app-ivr',
  templateUrl: './ivr.html',
  styleUrls: ['./ivr.css']
})
export class IvrComponent implements OnInit {
  ivrs: any[] = [];
  loading = false;

  constructor(private api: ApiService) {}

  loadIvrs() {
    this.loading = true;
    this.api.getIvrs().subscribe({
      next: (data) => {
        this.ivrs = data || [];
        this.loading = false;
      },
      error: (err) => {
        console.error('Error al cargar IVRs', err);
        this.loading = false;
      }
    });
  }

  ngOnInit(): void {
    this.loadIvrs();
  }
}