from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, BigInteger, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"
    
    student_id = Column(String(20), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    section_id = Column(String(20), ForeignKey("sections.section_id"), nullable=False)
    group_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    section = relationship("Section", back_populates="students")
    submissions = relationship("Submission", back_populates="student")
    team_participations = relationship("TeamParticipation", back_populates="student")
    grades = relationship("Grade", back_populates="student")


class Instructor(Base):
    __tablename__ = "instructors"
    
    instructor_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    role = Column(String(50))
    
    # Relationships
    sections = relationship("Section", back_populates="instructor")
    grades = relationship("Grade", back_populates="reviewer")


class Section(Base):
    __tablename__ = "sections"
    
    section_id = Column(String(20), primary_key=True)
    section_code = Column(String(50), nullable=False)
    semester = Column(String(20), nullable=False)
    year = Column(Integer, nullable=False)
    instructor_id = Column(Integer, ForeignKey("instructors.instructor_id"), nullable=False)
    
    # Relationships
    instructor = relationship("Instructor", back_populates="sections")
    students = relationship("Student", back_populates="section")
    assignments = relationship("Assignment", back_populates="section")


class Assignment(Base):
    __tablename__ = "assignments"
    
    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime, nullable=False)
    max_score = Column(Integer, nullable=False)
    requirements = Column(Text)
    section_id = Column(String(20), ForeignKey("sections.section_id"), nullable=False)
    
    # Relationships
    section = relationship("Section", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")
    plagiarism_detections = relationship("PlagiarismDetection", back_populates="assignment")


class Submission(Base):
    __tablename__ = "submissions"
    
    submission_id = Column(BigInteger, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.assignment_id"), nullable=False)
    section_id = Column(String(20), ForeignKey("sections.section_id"), nullable=False)
    group_number = Column(Integer, nullable=False)
    submitted_by = Column(String(20), ForeignKey("students.student_id"), nullable=False)
    submission_date = Column(DateTime, server_default=func.now())
    project_path = Column(String(500), nullable=True)
    video_url = Column(String(500))
    participation_report_path = Column(String(500))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    section = relationship("Section")
    student = relationship("Student", back_populates="submissions")
    grades = relationship("Grade", back_populates="submission")
    feedback = relationship("Feedback", back_populates="submission", uselist=False)
    team_participations = relationship("TeamParticipation", back_populates="submission")
    simple_logs = relationship("SimpleLog", back_populates="submission")
    plagiarism_detections_1 = relationship(
        "PlagiarismDetection",
        foreign_keys="[PlagiarismDetection.submission_id_1]",
        back_populates="submission_1"
    )
    plagiarism_detections_2 = relationship(
        "PlagiarismDetection",
        foreign_keys="[PlagiarismDetection.submission_id_2]",
        back_populates="submission_2"
    )

class PlagiarismDetection(Base):
    __tablename__ = "plagiarism_detections"
    
    detection_id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.assignment_id"), nullable=False)
    submission_id_1 = Column(Integer, ForeignKey("submissions.submission_id"), nullable=False)
    submission_id_2 = Column(Integer, ForeignKey("submissions.submission_id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    semantic_similarity = Column(Float)
    structural_similarity = Column(Float)
    detection_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    reviewed_by = Column(Integer, ForeignKey("instructors.instructor_id"), nullable=True)
    
    # Relaciones
    assignment = relationship("Assignment", back_populates="plagiarism_detections")
    submission_1 = relationship(
        "Submission",
        foreign_keys=[submission_id_1],
        back_populates="plagiarism_detections_1"
    )
    submission_2 = relationship(
        "Submission",
        foreign_keys=[submission_id_2],
        back_populates="plagiarism_detections_2"
    )


class Grade(Base):
    __tablename__ = "grades"
    
    grade_id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(BigInteger, ForeignKey("submissions.submission_id"), nullable=False)
    student_id = Column(String(20), ForeignKey("students.student_id"))
    
    # AI Scores
    ai_comprehension_score = Column(DECIMAL(5, 2))
    ai_design_score = Column(DECIMAL(5, 2))
    ai_implementation_score = Column(DECIMAL(5, 2))
    ai_functionality_score = Column(DECIMAL(5, 2))
    ai_total_score = Column(DECIMAL(5, 2))
    
    # Final Scores (after instructor review)
    final_comprehension_score = Column(DECIMAL(5, 2))
    final_design_score = Column(DECIMAL(5, 2))
    final_implementation_score = Column(DECIMAL(5, 2))
    final_functionality_score = Column(DECIMAL(5, 2))
    final_total_score = Column(DECIMAL(5, 2))
    
    # Participation
    participation_percentage = Column(DECIMAL(5, 2))
    adjusted_final_score = Column(DECIMAL(5, 2))
    
    status = Column(String(50), default="pending")
    reviewed_by = Column(Integer, ForeignKey("instructors.instructor_id"))
    reviewed_at = Column(DateTime)
    instructor_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    published_at = Column(DateTime)
    
    # Relationships
    submission = relationship("Submission", back_populates="grades")
    student = relationship("Student", back_populates="grades")
    reviewer = relationship("Instructor", back_populates="grades")


class TeamParticipation(Base):
    __tablename__ = "team_participation"
    
    participation_id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(BigInteger, ForeignKey("submissions.submission_id"), nullable=False)
    student_id = Column(String(20), ForeignKey("students.student_id"), nullable=False)
    participation_percentage = Column(DECIMAL(5, 2), nullable=False)
    
    # Relationships
    submission = relationship("Submission", back_populates="team_participations")
    student = relationship("Student", back_populates="team_participations")


class Feedback(Base):
    __tablename__ = "feedback"
    
    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    grade_id = Column(Integer, ForeignKey("grades.grade_id"), nullable=False)
    submission_id = Column(BigInteger, ForeignKey("submissions.submission_id"), nullable=False)
    
    comprehension_comments = Column(Text)
    design_comments = Column(Text)
    implementation_comments = Column(Text)
    functionality_comments = Column(Text)
    general_comments = Column(Text)
    
    generated_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    submission = relationship("Submission", back_populates="feedback")


class SimpleLog(Base):
    __tablename__ = "simple_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(BigInteger, ForeignKey("submissions.submission_id"))
    step = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    message = Column(Text)
    details = Column(JSON)
    
    # Relationships
    submission = relationship("Submission", back_populates="simple_logs")
