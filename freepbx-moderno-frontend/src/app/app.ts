// src/app/app.ts
import { Component } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router'
import { PdfService } from './core/pdf.service'; // Importa el servicio PDF
import { ApiService } from './core/api.service'; //Importas el servicio API
import { DatePipe } from '@angular/common'; // Importar  el DatePipe 

@Component({
  selector: 'app-root',
  standalone: true,
  providers: [PdfService, ApiService, DatePipe], 
  imports: [RouterOutlet, RouterLink],
  template: `
    <div class="flex h-screen overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-64 bg-sidebar-dark text-gray-400 flex flex-col transition-all duration-300 hidden md:flex shrink-0">
        <div class="h-16 flex items-center justify-center border-b border-gray-700 bg-sidebar-dark">
          <div class="flex flex-col items-center">
            <span class="text-2xl font-serif text-white tracking-widest">BEYOND</span>
            <div class="h-0.5 w-12 bg-gray-500 mt-1"></div>
          </div>
        </div>
        
        <nav class="flex-1 overflow-y-auto py-4 custom-scrollbar">
          <ul class="space-y-1">
            <li>
              <a routerLink="/" class="flex items-center px-6 py-3 hover:bg-gray-800 hover:text-white transition-colors group">
                <span class="material-icons-outlined text-sm mr-3">home</span>
                <span class="text-sm font-medium">Inicio</span>
              </a>
            </li>
            <li>
              <a routerLink="/extensions" class="flex items-center px-6 py-3 hover:bg-gray-800 hover:text-white transition-colors group">
                <span class="material-icons-outlined text-sm mr-3">phone</span>
                <span class="text-sm font-medium">Extensiones</span>
              </a>
            </li>
            <li>
              <a routerLink="/calls" class="flex items-center px-6 py-3 hover:bg-gray-800 hover:text-white transition-colors group">
                <span class="material-icons-outlined text-sm mr-3">call</span>
                <span class="text-sm font-medium">Llamadas</span>
              </a>
            </li>
            <li>
              <a routerLink="/trunks" class="flex items-center px-6 py-3 hover:bg-gray-800 hover:text-white transition-colors group">
                <span class="material-icons-outlined text-sm mr-3">router</span>
                <span class="text-sm font-medium">Troncales</span>
              </a>
            </li>
            <li>
              <a routerLink="/ivr" class="flex items-center px-6 py-3 hover:bg-gray-800 hover:text-white transition-colors group">
                <span class="material-icons-outlined text-sm mr-3">record_voice_over</span>
                <span class="text-sm font-medium">IVR</span>
              </a>
            </li>
            <li>
              <a routerLink="/incoming-routes" class="flex items-center px-6 py-3 hover:bg-gray-800 hover:text-white transition-colors group">
                <span class="material-icons-outlined text-sm mr-3">call_received</span>
                <span class="text-sm font-medium">Rutas Entrantes</span>
              </a>
            </li>
            <li>
              <a routerLink="/monitoring" class="flex items-center px-6 py-3 hover:bg-gray-800 hover:text-white transition-colors group">
                <span class="material-icons-outlined text-sm mr-3">dashboard</span>
                <span class="text-sm font-medium">Monitoreo</span>
              </a>
            </li>
          </ul>
        </nav>
      </aside>

      <main class="flex-1 flex flex-col overflow-hidden">
        <!-- Header -->
        <header class="h-16 bg-white dark:bg-card-dark shadow-sm flex items-center justify-between px-6 z-10 transition-colors duration-200">
          <div class="flex items-center w-1/3">
            <div class="relative w-full max-w-md">
              <span class="absolute inset-y-0 left-0 pl-3 flex items-center">
                <span class="material-icons-outlined text-gray-400 text-lg">search</span>
              </span>
              <input 
                class="w-full pl-10 pr-4 py-2 rounded-full border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent dark:text-white transition-colors" 
                placeholder="Buscar..." 
                type="text"/>
            </div>
          </div>
          
          <div class="flex items-center space-x-4">
            <button 
              class="p-2 text-gray-400 hover:text-primary transition-colors rounded-full hover:bg-gray-100 dark:hover:bg-gray-700" 
              (click)="toggleDarkMode()">
              <span class="material-icons-outlined text-xl">dark_mode</span>
            </button>
            
            <button class="relative p-2 text-gray-400 hover:text-primary transition-colors">
              <span class="material-icons-outlined text-xl">notifications</span>
              <span class="absolute top-1 right-1 h-4 w-4 bg-primary text-white text-[10px] font-bold flex items-center justify-center rounded-full">3</span>
            </button>
            
            <div class="flex items-center pl-4 border-l border-gray-200 dark:border-gray-700">
              <div class="h-9 w-9 rounded-full bg-purple-700 text-white flex items-center justify-center font-bold text-sm">
                JD
              </div>
              <div class="ml-3 hidden lg:block">
                <p class="text-sm font-medium text-gray-800 dark:text-white">Francisco</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">Administrator</p>
              </div>
            </div>
          </div>
        </header>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6 lg:p-8 custom-scrollbar">
          <router-outlet></router-outlet>
        </div>
      </main>
    </div>
  `,
  styleUrl: './app.css',

})
export class App {
  toggleDarkMode() {
    document.documentElement.classList.toggle('dark');
  }
}