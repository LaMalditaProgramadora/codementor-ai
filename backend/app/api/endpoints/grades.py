from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.models import Grade, Feedback
from app.schemas.schemas import GradeResponse, GradeCreate, FeedbackResponse

router = APIRouter()

@router.get("", response_model=List[GradeResponse])
def list_grades(
    submission_id: Optional[int] = None,
    student_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Listar calificaciones"""
    query = db.query(Grade)
    
    if submission_id:
        query = query.filter(Grade.submission_id == submission_id)
    if student_id:
        query = query.filter(Grade.student_id == student_id)
    
    grades = query.offset(skip).limit(limit).all()
    
    # Incluir feedback en cada grade
    for grade in grades:
        grade.feedback = db.query(Feedback).filter(
            Feedback.grade_id == grade.grade_id
        ).first()
    
    return grades

@router.get("/{grade_id}", response_model=GradeResponse)
def get_grade(grade_id: int, db: Session = Depends(get_db)):
    """Obtener una calificación por ID"""
    grade = db.query(Grade).filter(Grade.grade_id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    # Incluir feedback
    grade.feedback = db.query(Feedback).filter(
        Feedback.grade_id == grade.grade_id
    ).first()
    
    return grade

@router.put("/{grade_id}", response_model=GradeResponse)
def update_grade(
    grade_id: int,
    final_comprehension_score: Optional[float] = None,
    final_design_score: Optional[float] = None,
    final_implementation_score: Optional[float] = None,
    final_functionality_score: Optional[float] = None,
    instructor_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Actualizar calificación (revisión manual del docente)"""
    grade = db.query(Grade).filter(Grade.grade_id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    if final_comprehension_score is not None:
        grade.final_comprehension_score = final_comprehension_score
    if final_design_score is not None:
        grade.final_design_score = final_design_score
    if final_implementation_score is not None:
        grade.final_implementation_score = final_implementation_score
    if final_functionality_score is not None:
        grade.final_functionality_score = final_functionality_score
    if instructor_notes is not None:
        grade.instructor_notes = instructor_notes
    
    # Calcular total score
    if all([
        grade.final_comprehension_score,
        grade.final_design_score,
        grade.final_implementation_score,
        grade.final_functionality_score
    ]):
        grade.final_total_score = (
            grade.final_comprehension_score +
            grade.final_design_score +
            grade.final_implementation_score +
            grade.final_functionality_score
        ) / 4
    
    grade.status = "reviewed"
    
    db.commit()
    db.refresh(grade)
    return grade

@router.post("/{grade_id}/publish")
def publish_grade(grade_id: int, db: Session = Depends(get_db)):
    """Publicar calificación para que el estudiante la vea"""
    from datetime import datetime
    
    grade = db.query(Grade).filter(Grade.grade_id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    grade.status = "published"
    grade.published_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Grade published successfully"}