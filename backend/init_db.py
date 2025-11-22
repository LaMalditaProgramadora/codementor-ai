#!/usr/bin/env python3
"""
Script to initialize database with tables
"""
from app.db.session import engine, Base
from app.models.models import (
    Student, Instructor, Section, Assignment,
    Submission, Grade, Feedback, PlagiarismDetection,
    TeamParticipation, SimpleLog
)

def init_db():
    """
    Create all tables
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
