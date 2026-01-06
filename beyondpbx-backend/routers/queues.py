# routers/queues.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import QueueName
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/queues", tags=["queues"])

# Schemas
class QueueBase(BaseModel):
    qname: int
    queue: str
    descr: str

class QueueCreate(QueueBase):
    pass

class QueueUpdate(QueueBase):
    pass

class QueueResponse(QueueBase):
    id: int

    class Config:
        from_attributes = True

# CRUD Endpoints
@router.get("", response_model=list[QueueResponse])
def get_queues(db: Session = Depends(get_db)):
    """Obtener todas las colas"""
    try:
        queues = db.query(QueueName).order_by(QueueName.qname).all()
        return queues
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener colas: {str(e)}")

@router.get("/{queue_id}", response_model=QueueResponse)
def get_queue(queue_id: int, db: Session = Depends(get_db)):
    """Obtener una cola por ID"""
    queue = db.query(QueueName).filter(QueueName.id == queue_id).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Cola no encontrada")
    return queue

@router.post("", response_model=QueueResponse, status_code=201)
def create_queue(queue_data: QueueCreate, db: Session = Depends(get_db)):
    """Crear una nueva cola"""
    try:
        # Verificar si ya existe una cola con el mismo qname o nombre
        existing = db.query(QueueName).filter(
            (QueueName.qname == queue_data.qname) | 
            (QueueName.queue == queue_data.queue)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe una cola con ese QName o nombre"
            )
        
        # Crear nueva cola
        new_queue = QueueName(
            qname=queue_data.qname,
            queue=queue_data.queue,
            descr=queue_data.descr
        )
        
        db.add(new_queue)
        db.commit()
        db.refresh(new_queue)
        
        return new_queue
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear cola: {str(e)}")

@router.put("/{queue_id}", response_model=QueueResponse)
def update_queue(queue_id: int, queue_data: QueueUpdate, db: Session = Depends(get_db)):
    """Actualizar una cola existente"""
    try:
        # Buscar la cola
        queue = db.query(QueueName).filter(QueueName.id == queue_id).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Cola no encontrada")
        
        # Verificar si el nuevo qname o nombre ya existe en otra cola
        existing = db.query(QueueName).filter(
            QueueName.id != queue_id,
            (QueueName.qname == queue_data.qname) | 
            (QueueName.queue == queue_data.queue)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe otra cola con ese QName o nombre"
            )
        
        # Actualizar campos
        queue.qname = queue_data.qname
        queue.queue = queue_data.queue
        queue.descr = queue_data.descr
        
        db.commit()
        db.refresh(queue)
        
        return queue
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar cola: {str(e)}")

@router.delete("/{queue_id}")
def delete_queue(queue_id: int, db: Session = Depends(get_db)):
    """Eliminar una cola"""
    try:
        queue = db.query(QueueName).filter(QueueName.id == queue_id).first()
        if not queue:
            raise HTTPException(status_code=404, detail="Cola no encontrada")
        
        db.delete(queue)
        db.commit()
        
        return {"message": "Cola eliminada exitosamente", "id": queue_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar cola: {str(e)}")
