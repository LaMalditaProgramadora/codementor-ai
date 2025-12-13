from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.models import Feedback
from pydantic import BaseModel

router = APIRouter()

# Schema de respuesta
class FeedbackResponse(BaseModel):
    feedback_id: int
    grade_id: int
    submission_id: int
    comprehension_comments: str = None
    design_comments: str = None
    implementation_comments: str = None
    functionality_comments: str = None
    general_comments: str = None
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[FeedbackResponse])
def get_feedback(
    grade_id: int = None,
    submission_id: int = None,
    db: Session = Depends(get_db)
):
    """Get feedback by grade_id or submission_id"""
    query = db.query(Feedback)
    
    if grade_id:
        query = query.filter(Feedback.grade_id == grade_id)
    elif submission_id:
        query = query.filter(Feedback.submission_id == submission_id)
    else:
        raise HTTPException(status_code=400, detail="Provide grade_id or submission_id")
    
    feedback = query.all()
    return feedback

@router.get("/{feedback_id}", response_model=FeedbackResponse)
def get_feedback_by_id(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """Get feedback by ID"""
    feedback = db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return feedback