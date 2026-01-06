// src/app/queues/queues.ts
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../core/api.service';
import { ToastService } from '../core/toast.service';
import { ConfirmationService } from '../core/confirmation.service';

interface Queue {
  id?: number;
  qname: number;
  queue: string;
  descr: string;
}

@Component({
  selector: 'app-queues',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './queues.html',
  styleUrls: ['./queues.css']
})
export class QueuesComponent implements OnInit {
  queues: Queue[] = [];
  filteredQueues: Queue[] = [];
  loading = false;
  searchTerm = '';
  
  // Modal de edición/creación
  showModal = false;
  modalTitle = '';
  editingQueue: Queue | null = null;
  formQueue: Queue = {
    qname: 0,
    queue: '',
    descr: ''
  };

  constructor(
    private api: ApiService,
    private toast: ToastService,
    private confirmation: ConfirmationService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadQueues();
  }

  /**
   * Carga todas las colas
   */
  loadQueues(): void {
    this.loading = true;
    this.api.getQueues().subscribe({
      next: (data: any) => {
        this.queues = data.queues || [];
        this.filteredQueues = [...this.queues];
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando colas:', err);
        this.toast.error('Error al cargar colas');
        this.loading = false;
      }
    });
  }

  /**
   * Filtra colas por término de búsqueda
   */
  filterQueues(): void {
    if (!this.searchTerm.trim()) {
      this.filteredQueues = [...this.queues];
      return;
    }

    const term = this.searchTerm.toLowerCase();
    this.filteredQueues = this.queues.filter(q =>
      q.queue.toLowerCase().includes(term) ||
      q.descr.toLowerCase().includes(term) ||
      q.qname.toString().includes(term)
    );
  }

  /**
   * Abre modal para crear nueva cola
   */
  openCreateModal(): void {
    this.modalTitle = 'Crear Nueva Cola';
    this.editingQueue = null;
    this.formQueue = {
      qname: this.getNextQname(),
      queue: '',
      descr: ''
    };
    this.showModal = true;
  }

  /**
   * Abre modal para editar cola existente
   */
  openEditModal(queue: Queue): void {
    this.modalTitle = 'Editar Cola';
    this.editingQueue = queue;
    this.formQueue = { ...queue };
    this.showModal = true;
  }

  /**
   * Cierra el modal
   */
  closeModal(): void {
    this.showModal = false;
    this.editingQueue = null;
    this.formQueue = {
      qname: 0,
      queue: '',
      descr: ''
    };
  }

  /**
   * Guarda la cola (crear o actualizar)
   */
  saveQueue(): void {
    if (!this.formQueue.queue.trim()) {
      this.toast.error('El nombre de la cola es requerido');
      return;
    }

    if (this.editingQueue) {
      this.updateQueue();
    } else {
      this.createQueue();
    }
  }

  /**
   * Crea una nueva cola
   */
  private createQueue(): void {
    this.api.createQueue(this.formQueue).subscribe({
      next: () => {
        this.toast.success('Cola creada exitosamente');
        this.loadQueues();
        this.closeModal();
      },
      error: (err) => {
        console.error('Error creando cola:', err);
        this.toast.error('Error al crear la cola');
      }
    });
  }

  /**
   * Actualiza una cola existente
   */
  private updateQueue(): void {
    if (!this.editingQueue?.id) return;

    this.api.updateQueue(this.editingQueue.id, this.formQueue).subscribe({
      next: () => {
        this.toast.success('Cola actualizada exitosamente');
        this.loadQueues();
        this.closeModal();
      },
      error: (err) => {
        console.error('Error actualizando cola:', err);
        this.toast.error('Error al actualizar la cola');
      }
    });
  }

  /**
   * Elimina una cola
   */
  async deleteQueue(queue: Queue): Promise<void> {
    const confirmed = await this.confirmation.confirm({
      title: '¿Estás seguro?',
      message: `¿Deseas eliminar la cola "${queue.queue}" (${queue.descr})?`,
      type: 'danger',
      confirmText: 'Eliminar',
      cancelText: 'Cancelar'
    });

    if (confirmed && queue.id) {
      this.api.deleteQueue(queue.id).subscribe({
        next: () => {
          this.toast.success('Cola eliminada exitosamente');
          this.loadQueues();
        },
        error: (err) => {
          console.error('Error eliminando cola:', err);
          this.toast.error('Error al eliminar la cola');
        }
      });
    }
  }

  /**
   * Obtiene el siguiente qname disponible
   */
  private getNextQname(): number {
    if (this.queues.length === 0) return 1;
    const maxQname = Math.max(...this.queues.map(q => q.qname));
    return maxQname + 1;
  }
}
