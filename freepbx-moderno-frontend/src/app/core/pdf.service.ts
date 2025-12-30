// src/app/core/pdf.service.ts
import { Injectable } from '@angular/core';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

@Injectable({
  providedIn: 'root'
})
export class PdfService {
  async generateDashboardPdf(dashboardElement: HTMLElement, stats: any): Promise<void> {
    try {
      // Capturar el dashboard como imagen
      const canvas = await html2canvas(dashboardElement, {
        scale: 2,       // Mejor calidad
        useCORS: true,  // Para imágenes externas
        allowTaint: true,
        backgroundColor: '#ffffff' // Fondo blanco
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgWidth = 210; // Ancho A4 en mm
      const pageHeight = 295; // Alto A4 en mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      // Añadir título
      pdf.setFontSize(20);
      pdf.text('Informe de Llamadas - Dashboard', 105, 15, { align: 'center' });
      
      // Añadir fecha
      pdf.setFontSize(10);
      pdf.text(`Fecha: ${new Date().toLocaleDateString()}`, 10, 25);

      // Añadir imagen del dashboard
      pdf.addImage(imgData, 'PNG', 0, 30, imgWidth, imgHeight);
      heightLeft -= imgHeight;

      // Si hay más contenido, añadir páginas
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      // Guardar
      pdf.save(`dashboard_${new Date().toISOString().split('T')[0]}.pdf`);
    } catch (error) {
      console.error('Error al generar PDF:', error);
      throw new Error('No se pudo generar el PDF');
    }
  }
}