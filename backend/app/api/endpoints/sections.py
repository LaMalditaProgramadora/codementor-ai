from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.models import Section
from app.schemas.schemas import SectionCreate, SectionResponse

router = APIRouter()

@router.post("", response_model=SectionResponse)
def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    """Crear una nueva sección"""
    db_section = Section(**section.dict())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

@router.get("", response_model=List[SectionResponse])
def list_sections(db: Session = Depends(get_db)):
    """Listar todas las secciones"""
    return db.query(Section).all()

@router.get("/{section_id}", response_model=SectionResponse)
def get_section(section_id: str, db: Session = Depends(get_db)):
    """Obtener una sección por ID"""
    section = db.query(Section).filter(Section.section_id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section