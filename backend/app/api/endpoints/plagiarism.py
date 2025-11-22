from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.models import PlagiarismDetection, Submission
from app.schemas.schemas import PlagiarismDetectionResponse
from app.services.evaluation_pipeline import EvaluationPipeline

router = APIRouter()

@router.post("/detect")
async def detect_plagiarism(
    assignment_id: int,
    submission_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """Detectar plagio entre entregas de una tarea"""
    pipeline = EvaluationPipeline(db)
    
    try:
        detections = await pipeline.detect_plagiarism(
            assignment_id=assignment_id,
            submission_ids=submission_ids
        )
        
        return {
            "message": f"Plagiarism detection completed",
            "detections_found": len(detections),
            "detections": detections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[PlagiarismDetectionResponse])
def list_plagiarism_detections(
    assignment_id: Optional[int] = None,
    status: Optional[str] = None,
    min_similarity: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Listar detecciones de plagio"""
    query = db.query(PlagiarismDetection)
    
    if assignment_id:
        # Filtrar por assignment_id de las submissions
        query = query.join(
            Submission,
            Submission.submission_id == PlagiarismDetection.submission_id_1
        ).filter(Submission.assignment_id == assignment_id)
    
    if status:
        query = query.filter(PlagiarismDetection.status == status)
    
    if min_similarity:
        query = query.filter(
            PlagiarismDetection.similarity_score >= min_similarity
        )
    
    return query.offset(skip).limit(limit).all()

@router.get("/{detection_id}", response_model=PlagiarismDetectionResponse)
def get_plagiarism_detection(detection_id: int, db: Session = Depends(get_db)):
    """Obtener una detección de plagio por ID"""
    detection = db.query(PlagiarismDetection).filter(
        PlagiarismDetection.detection_id == detection_id
    ).first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    return detection

@router.put("/{detection_id}/review")
def review_plagiarism(
    detection_id: int,
    status: str,
    reviewed_by: int,
    db: Session = Depends(get_db)
):
    """Marcar una detección de plagio como revisada"""
    detection = db.query(PlagiarismDetection).filter(
        PlagiarismDetection.detection_id == detection_id
    ).first()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    detection.status = status
    detection.reviewed_by = reviewed_by
    
    db.commit()
    return {"message": "Detection reviewed successfully"}