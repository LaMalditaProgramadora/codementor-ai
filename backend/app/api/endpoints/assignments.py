from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.models import Assignment
from app.schemas.schemas import AssignmentCreate, AssignmentResponse

router = APIRouter()

@router.post("", response_model=AssignmentResponse)
def create_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db)):
    """Crear una nueva tarea"""
    try:
        db_assignment = Assignment(**assignment.dict())
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        return db_assignment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[AssignmentResponse])
def list_assignments(
    section_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Listar todas las tareas"""
    query = db.query(Assignment)
    if section_id:
        query = query.filter(Assignment.section_id == section_id)
    return query.offset(skip).limit(limit).all()

@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Obtener una tarea por ID"""
    assignment = db.query(Assignment).filter(
        Assignment.assignment_id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    assignment: AssignmentCreate,
    db: Session = Depends(get_db)
):
    """Actualizar una tarea"""
    db_assignment = db.query(Assignment).filter(
        Assignment.assignment_id == assignment_id
    ).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    for key, value in assignment.dict().items():
        setattr(db_assignment, key, value)
    
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Eliminar una tarea"""
    assignment = db.query(Assignment).filter(
        Assignment.assignment_id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(assignment)
    db.commit()
    return {"message": "Assignment deleted successfully"}