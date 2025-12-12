from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
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
    video_url: Optional[str] = Form(None),  # ✅ Cambiar a video_url
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
        
        # ✅ Guardar URL de video (opcional)
        if video_url:
            submission.video_url = video_url
        
        # 3. TERCERO: Commit todo
        db.commit()
        db.refresh(submission)
        
        return submission
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")

async def run_evaluation_background(submission_id: int):
    """Run evaluation in background"""
    from app.db.session import SessionLocal
    from app.models.models import Assignment
    from app.services.evaluation_pipeline import EvaluationPipeline
    
    db = SessionLocal()
    
    try:
        print(f"🔄 Background evaluation started for submission {submission_id}")
        
        submission = db.query(Submission).filter(
            Submission.submission_id == submission_id
        ).first()
        
        if not submission:
            print(f"❌ Submission {submission_id} not found")
            return
        
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
        
        # Actualizar estado
        submission.status = "evaluated"
        db.commit()
        
        print(f"✅ Background evaluation completed for submission {submission_id}")
        
    except Exception as e:
        print(f"❌ Background evaluation failed: {str(e)}")
        submission = db.query(Submission).filter(
            Submission.submission_id == submission_id
        ).first()
        if submission:
            submission.status = "failed"
            db.commit()
    finally:
        db.close()

@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    """Get submission by ID"""
    submission = db.query(Submission).filter(
        Submission.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission

@router.post("/{submission_id}/evaluate")
async def evaluate_submission(
    submission_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger evaluation for a submission (async)"""
    submission = db.query(Submission).filter(
        Submission.submission_id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Cambiar estado a "evaluating"
    submission.status = "evaluating"
    db.commit()
    
    # Ejecutar evaluación en background
    background_tasks.add_task(
        run_evaluation_background,
        submission_id
    )
    
    return {
        "message": "Evaluation started in background",
        "submission_id": submission_id,
        "status": "evaluating"
    }

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