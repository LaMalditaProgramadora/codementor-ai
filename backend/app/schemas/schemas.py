from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


# Student Schemas
class StudentBase(BaseModel):
    student_id: str = Field(..., max_length=20)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    section_id: str = Field(..., max_length=20)
    group_number: int


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    created_at: datetime
    
    class Config:
        from_attributes = True


# Instructor Schemas
class InstructorBase(BaseModel):
    name: str = Field(..., max_length=255)
    email: EmailStr
    role: Optional[str] = Field(None, max_length=50)


class InstructorCreate(InstructorBase):
    pass


class InstructorResponse(InstructorBase):
    instructor_id: int
    
    class Config:
        from_attributes = True


# Section Schemas
class SectionBase(BaseModel):
    section_id: str = Field(..., max_length=20)
    section_code: str = Field(..., max_length=50)
    semester: str = Field(..., max_length=20)
    year: int
    instructor_id: int


class SectionCreate(SectionBase):
    pass


class SectionResponse(SectionBase):
    class Config:
        from_attributes = True


# Assignment Schemas
class AssignmentBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    due_date: datetime
    max_score: int
    requirements: Optional[str] = None
    section_id: str = Field(..., max_length=20)


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentResponse(AssignmentBase):
    assignment_id: int
    
    class Config:
        from_attributes = True


# Submission Schemas
class SubmissionBase(BaseModel):
    assignment_id: int
    section_id: str
    group_number: int
    submitted_by: str


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionResponse(SubmissionBase):
    submission_id: int
    submission_date: datetime
    project_path: str
    video_url: Optional[str] = None
    participation_report_path: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Grade Schemas
class GradeBase(BaseModel):
    submission_id: int
    student_id: Optional[str] = None


class AIGradeScores(BaseModel):
    ai_comprehension_score: Optional[Decimal] = None
    ai_design_score: Optional[Decimal] = None
    ai_implementation_score: Optional[Decimal] = None
    ai_functionality_score: Optional[Decimal] = None
    ai_total_score: Optional[Decimal] = None


class FinalGradeScores(BaseModel):
    final_comprehension_score: Optional[Decimal] = None
    final_design_score: Optional[Decimal] = None
    final_implementation_score: Optional[Decimal] = None
    final_functionality_score: Optional[Decimal] = None
    final_total_score: Optional[Decimal] = None
    participation_percentage: Optional[Decimal] = None
    adjusted_final_score: Optional[Decimal] = None


class GradeCreate(GradeBase):
    pass


class GradeResponse(GradeBase, AIGradeScores, FinalGradeScores):
    grade_id: int
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    instructor_notes: Optional[str] = None
    created_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Feedback Schemas
class FeedbackBase(BaseModel):
    grade_id: int
    submission_id: int
    comprehension_comments: Optional[str] = None
    design_comments: Optional[str] = None
    implementation_comments: Optional[str] = None
    functionality_comments: Optional[str] = None
    general_comments: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackResponse(FeedbackBase):
    feedback_id: int
    generated_at: datetime
    
    class Config:
        from_attributes = True


# Plagiarism Detection Schemas
class PlagiarismDetectionBase(BaseModel):
    submission_id_1: int
    submission_id_2: int
    similarity_score: Decimal
    semantic_similarity: Optional[Decimal] = None
    structural_similarity: Optional[Decimal] = None


class PlagiarismDetectionCreate(PlagiarismDetectionBase):
    matching_details: Optional[dict] = None


class PlagiarismDetectionResponse(PlagiarismDetectionBase):
    detection_id: int
    matching_details: Optional[dict] = None
    detection_date: datetime
    status: str
    reviewed_by: Optional[int] = None
    
    class Config:
        from_attributes = True


# Team Participation Schemas
class TeamParticipationBase(BaseModel):
    submission_id: int
    student_id: str
    participation_percentage: Decimal


class TeamParticipationCreate(TeamParticipationBase):
    pass


class TeamParticipationResponse(TeamParticipationBase):
    participation_id: int
    
    class Config:
        from_attributes = True


# Log Schemas
class SimpleLogBase(BaseModel):
    submission_id: Optional[int] = None
    step: str
    status: str
    message: Optional[str] = None
    details: Optional[dict] = None


class SimpleLogCreate(SimpleLogBase):
    pass


class SimpleLogResponse(SimpleLogBase):
    log_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Analysis Result Schema (for AI processing)
class AnalysisResult(BaseModel):
    submission_id: int
    comprehension_score: float
    design_score: float
    implementation_score: float
    functionality_score: float
    total_score: float
    comprehension_feedback: str
    design_feedback: str
    implementation_feedback: str
    functionality_feedback: str
    general_feedback: str


# Video Analysis Result
class VideoAnalysisResult(BaseModel):
    submission_id: int
    transcription: str
    analysis: str
    participation_insights: Optional[dict] = None
