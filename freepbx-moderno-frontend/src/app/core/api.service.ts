// src/app/core/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  //private baseUrl = 'http://localhost:8000/api';
  private baseUrl = '/api';  // sin dominio ni puerto por el proxy.conf.json
  constructor(private http: HttpClient) {}

  // ENDOPOINTS
    // Endpoint to get extensions
  getExtensions(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/extensions`);
  }

  // Llamadas detalladas (sin paginación, pero con más datos)
  getDetailedCalls(
    period: 'today' | 'week' | 'month' | 'year' = 'month',
    page: number = 1,
    size: number = 50
  ): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/calls/detailed?period=${period}&page=${page}&size=${size}`);
  }

    // Endpoint to get all calls
  getCallsByPeriod(
    period: 'today' | 'week' | 'month' | 'year' = 'month',
    page: number = 1,
    size: number = 100
  ): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/calls?period=${period}&page=${page}&size=${size}`);
  }
    // Endpoint to get recent calls
  getRecentCalls(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/calls/recent`);
  }

    // Endpoint to get trunks
  getTrunks(): Observable<any[]> {
  return this.http.get<any[]>(`${this.baseUrl}/trunks`);
  }

  // Endpoint to get dashboard stats
  getDashboardStats(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/dashboard/stats`); 
  }

  // Endpoint to get IVRs
  getIvrs(): Observable<any[]> {
  return this.http.get<any[]>(`${this.baseUrl}/ivrs`);
}
}