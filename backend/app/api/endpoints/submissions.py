from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.models import Submission, Assignment
from app.schemas.schemas import SubmissionResponse, SubmissionCreate
from app.services.minio_service import minio_service
from app.services.evaluation_pipeline import EvaluationPipeline
from datetime import datetime

router = APIRouter()

@router.post("", response_model=SubmissionResponse)
async def create_submission(
    assignment_id: int = Form(...),
    section_id: str = Form(...),
    group_number: int = Form(...),
    submitted_by: str = Form(...),
    project_file: UploadFile = File(...),
    video_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Crear nueva submission con file uploads"""
    # Verificar que el assignment existe
    assignment = db.query(Assignment).filter(
        Assignment.assignment_id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # 1. PRIMERO: Crear el submission SIN hacer flush
    submission = Submission(
        assignment_id=assignment_id,
        section_id=section_id,
        group_number=group_number,
        submitted_by=submitted_by,
        status="uploaded"
    )
    db.add(submission)
    db.flush()
    
    # 2. SEGUNDO: Subir archivos a MinIO
    try:
        # Subir proyecto
        project_filename = f"{submission.submission_id}_{project_file.filename}"
        project_content = await project_file.read()
        
        project_path = minio_service.upload_submission(
            submission.submission_id,
            project_content,
            project_filename,
            project_file.content_type or "application/zip"
        )
        submission.project_path = project_path 
        
        # Subir video (opcional)
        if video_file:
            video_filename = f"{submission.submission_id}_{video_file.filename}"
            video_content = await video_file.read()
            
            video_path = minio_service.upload_video(
                submission.submission_id,
                video_content,
                video_filename,
                video_file.content_type or "video/mp4"
            )
            submission.video_url = video_path
        
        # 3. TERCERO: Commit todo
        db.commit()
        db.refresh(submission)
        
        return submission
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")

@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    """Get submission by ID"""
    submission = db.query(Submission).filter(
        Submission.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission

@router.get("", response_model=List[SubmissionResponse])
def list_submissions(
    assignment_id: Optional[int] = None,
    section_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List submissions with filters"""
    query = db.query(Submission)
    
    if assignment_id:
        query = query.filter(Submission.assignment_id == assignment_id)
    if section_id:
        query = query.filter(Submission.section_id == section_id)
    if status:
        query = query.filter(Submission.status == status)
    
    submissions = query.offset(skip).limit(limit).all()
    return submissions

@router.post("/{submission_id}/evaluate")
async def evaluate_submission(
    submission_id: int,
    db: Session = Depends(get_db)
):
    """Trigger evaluation for a submission"""
    submission = db.query(Submission).filter(
        Submission.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    assignment = db.query(Assignment).filter(
        Assignment.assignment_id == submission.assignment_id
    ).first()
    
    rubric = {
        "comprehension": {"max_score": 25, "criteria": "Understanding of requirements"},
        "design": {"max_score": 25, "criteria": "Code architecture and design patterns"},
        "implementation": {"max_score": 25, "criteria": "Code quality and best practices"},
        "functionality": {"max_score": 25, "criteria": "Features work as expected"}
    }
    
    pipeline = EvaluationPipeline(db)
    result = await pipeline.evaluate_submission_complete(
        submission_id,
        assignment.requirements or "No specific requirements",
        rubric
    )
    
    return {
        "message": "Evaluation completed",
        "submission_id": submission_id,
        "result": result
    }

@router.get("/{submission_id}/download/project")
def download_project(submission_id: int, db: Session = Depends(get_db)):
    """Get presigned URL to download project file"""
    submission = db.query(Submission).filter(
        Submission.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    bucket, object_name = submission.project_path.split('/', 1)
    url = minio_service.get_file_url(object_name, bucket)
    
    return {"download_url": url}

@router.get("/{submission_id}/download/video")
def download_video(submission_id: int, db: Session = Depends(get_db)):
    """Get presigned URL to download video file"""
    submission = db.query(Submission).filter(
        Submission.submission_id == submission_id
    ).first()
    
    if not submission or not submission.video_url:
        raise HTTPException(status_code=404, detail="Video not found")
    
    bucket, object_name = submission.video_url.split('/', 1)
    url = minio_service.get_file_url(object_name, bucket)
    
    return {"download_url": url}

@router.delete("/{submission_id}")
def delete_submission(submission_id: int, db: Session = Depends(get_db)):
    """Delete submission (soft delete - updates status)"""
    submission = db.query(Submission).filter(
        Submission.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    submission.status = "deleted"
    db.commit()
    
    return {"message": "Submission deleted successfully"}