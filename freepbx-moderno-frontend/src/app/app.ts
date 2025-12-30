// src/app/app.ts
import { Component } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router'
import { PdfService } from './core/pdf.service'; // Importa el servicio PDF
import { ApiService } from './core/api.service'; //Importas el servicio API
import { DatePipe } from '@angular/common'; // Importar  el DatePipe 
import { CallsComponent } from './calls/calls';
import { DashboardComponent } from './dashboard/dashboard';
import { ExtensionsComponent } from './extensions/extensions';
import { TrunksComponent } from './trunks/trunks';
import { IvrComponent } from './ivr/ivr';
import { IncomingRoutesComponent } from './incoming-routes/incoming-routes';


@Component({
  selector: 'app-root',
  standalone: true,
  providers: [PdfService, ApiService, DatePipe], 
  imports: [RouterOutlet, RouterLink],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {}