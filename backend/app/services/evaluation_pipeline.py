import zipfile
import os
import tempfile
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.models import Submission, Grade, Feedback, SimpleLog, PlagiarismDetection
from app.services.ollama_service import ollama_service
from app.services.codebert_service import codebert_service
from app.services.whisper_service import whisper_service
from app.services.minio_service import minio_service
from datetime import datetime


class EvaluationPipeline:
    """
    Main pipeline for evaluating code submissions
    Integrates Ollama, CodeBERT, and Whisper services
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def _log(self, submission_id: int, step: str, status: str, message: str, details: dict = None):
        """
        Create log entry
        """
        log = SimpleLog(
            submission_id=submission_id,
            step=step,
            status=status,
            message=message,
            details=details
        )
        self.db.add(log)
        self.db.commit()
    
    def extract_code_from_zip(self, zip_path: str, temp_dir: str) -> Dict[str, str]:
        """
        Extract code files from ZIP submission
        """
        code_files = {}
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
            # Find all code files
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(('.cs', '.py', '.java', '.cpp', '.c', '.js', '.ts')):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            code_files[file] = f.read()
        
        return code_files
    
    async def evaluate_code(
        self,
        submission_id: int,
        requirements: str,
        rubric: Dict
    ) -> Dict:
        """
        Evaluate code submission using Ollama LLM
        """
        self._log(submission_id, "code_evaluation", "started", "Starting code evaluation")
        
        try:
            # Get submission
            submission = self.db.query(Submission).filter(
                Submission.submission_id == submission_id
            ).first()
            
            if not submission:
                raise Exception("Submission not found")
            
            # Download submission from MinIO
            bucket, object_name = submission.project_path.split('/', 1)
            file_data = minio_service.download_file(object_name, bucket)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_file.write(file_data)
                zip_path = tmp_file.name
            
            # Extract code
            temp_dir = tempfile.mkdtemp()
            code_files = self.extract_code_from_zip(zip_path, temp_dir)
            
            # Combine all code
            combined_code = "\n\n".join([
                f"// File: {filename}\n{content}"
                for filename, content in code_files.items()
            ])
            
            # Analyze with Ollama
            self._log(submission_id, "llm_analysis", "started", "Analyzing with LLM")
            analysis_result = await ollama_service.analyze_code(
                combined_code,
                requirements,
                rubric
            )
            
            # Calculate total score
            total_score = (
                analysis_result['comprehension']['score'] +
                analysis_result['design']['score'] +
                analysis_result['implementation']['score'] +
                analysis_result['functionality']['score']
            ) / 4
            
            # Create grade record
            grade = Grade(
                submission_id=submission_id,
                ai_comprehension_score=analysis_result['comprehension']['score'],
                ai_design_score=analysis_result['design']['score'],
                ai_implementation_score=analysis_result['implementation']['score'],
                ai_functionality_score=analysis_result['functionality']['score'],
                ai_total_score=total_score,
                status="ai_evaluated"
            )
            self.db.add(grade)
            self.db.flush()
            
            # Create feedback
            feedback = Feedback(
                grade_id=grade.grade_id,
                submission_id=submission_id,
                comprehension_comments=analysis_result['comprehension']['comments'],
                design_comments=analysis_result['design']['comments'],
                implementation_comments=analysis_result['implementation']['comments'],
                functionality_comments=analysis_result['functionality']['comments'],
                general_comments=analysis_result['general_comments']
            )
            self.db.add(feedback)
            
            # Update submission status
            submission.status = "evaluated"
            
            self.db.commit()
            
            # Cleanup
            os.unlink(zip_path)
            
            self._log(
                submission_id,
                "code_evaluation",
                "completed",
                "Code evaluation completed",
                {"total_score": float(total_score)}
            )
            
            return {
                "grade_id": grade.grade_id,
                "total_score": float(total_score),
                "comprehension": analysis_result['comprehension']['score'],
                "design": analysis_result['design']['score'],
                "implementation": analysis_result['implementation']['score'],
                "functionality": analysis_result['functionality']['score']
            }
        
        except Exception as e:
            self._log(
                submission_id,
                "code_evaluation",
                "failed",
                f"Error: {str(e)}"
            )
            raise
    
    async def detect_plagiarism(
        self,
        assignment_id: int,
        submission_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Detect plagiarism among submissions using CodeBERT
        """
        # Get all submissions for assignment
        query = self.db.query(Submission).filter(
            Submission.assignment_id == assignment_id
        )
        
        if submission_ids:
            query = query.filter(Submission.submission_id.in_(submission_ids))
        
        submissions = query.all()
        
        # Extract code from each submission
        submission_codes = []
        for submission in submissions:
            try:
                bucket, object_name = submission.project_path.split('/', 1)
                file_data = minio_service.download_file(object_name, bucket)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                    tmp_file.write(file_data)
                    zip_path = tmp_file.name
                
                temp_dir = tempfile.mkdtemp()
                code_files = self.extract_code_from_zip(zip_path, temp_dir)
                
                combined_code = "\n".join(code_files.values())
                
                submission_codes.append({
                    'id': submission.submission_id,
                    'code': combined_code
                })
                
                os.unlink(zip_path)
            
            except Exception as e:
                print(f"Error processing submission {submission.submission_id}: {e}")
                continue
        
        # Detect plagiarism
        detections = codebert_service.detect_plagiarism(submission_codes)
        
        # Save detections to database
        for detection in detections:
            # Calculate structural similarity
            sub1 = next(s for s in submission_codes if s['id'] == detection['submission_id_1'])
            sub2 = next(s for s in submission_codes if s['id'] == detection['submission_id_2'])
            structural_sim = codebert_service.calculate_structural_similarity(
                sub1['code'],
                sub2['code']
            )
            
            plagiarism_record = PlagiarismDetection(
                submission_id_1=detection['submission_id_1'],
                submission_id_2=detection['submission_id_2'],
                similarity_score=detection['semantic_similarity'],
                semantic_similarity=detection['semantic_similarity'],
                structural_similarity=round(structural_sim * 100, 2),
                status=detection['status']
            )
            self.db.add(plagiarism_record)
        
        self.db.commit()
        
        return detections
    
    async def analyze_video(
        self,
        submission_id: int,
        requirements: str
    ) -> Dict:
        """
        Analyze video presentation using Whisper + Ollama
        """
        self._log(submission_id, "video_analysis", "started", "Starting video analysis")
        
        try:
            # Get submission
            submission = self.db.query(Submission).filter(
                Submission.submission_id == submission_id
            ).first()
            
            if not submission or not submission.video_url:
                raise Exception("Video not found for submission")
            
            # Download video from MinIO
            bucket, object_name = submission.video_url.split('/', 1)
            video_data = minio_service.download_file(object_name, bucket)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(video_data)
                video_path = tmp_file.name
            
            # Transcribe with Whisper
            self._log(submission_id, "video_transcription", "started", "Transcribing video")
            transcription_result = whisper_service.transcribe_video(video_path)
            
            # Analyze participation
            participation_data = whisper_service.analyze_participation_from_video(video_path)
            
            # Analyze transcription with Ollama
            self._log(submission_id, "transcription_analysis", "started", "Analyzing transcription")
            analysis = await ollama_service.analyze_video_transcription(
                transcription_result['text'],
                requirements
            )
            
            # Cleanup
            os.unlink(video_path)
            
            self._log(
                submission_id,
                "video_analysis",
                "completed",
                "Video analysis completed",
                {
                    "duration": transcription_result['duration'],
                    "speakers": participation_data['num_speakers_detected']
                }
            )
            
            return {
                "transcription": transcription_result['text'],
                "analysis": analysis,
                "participation": participation_data,
                "duration": transcription_result['duration']
            }
        
        except Exception as e:
            self._log(
                submission_id,
                "video_analysis",
                "failed",
                f"Error: {str(e)}"
            )
            raise
    
    async def evaluate_submission_complete(
        self,
        submission_id: int,
        requirements: str,
        rubric: Dict
    ) -> Dict:
        """
        Complete evaluation pipeline: code + video
        """
        self._log(submission_id, "full_evaluation", "started", "Starting complete evaluation")
        
        results = {}
        
        # Evaluate code
        try:
            code_result = await self.evaluate_code(submission_id, requirements, rubric)
            results['code_evaluation'] = code_result
        except Exception as e:
            results['code_evaluation'] = {"error": str(e)}
        
        # Analyze video (if available)
        submission = self.db.query(Submission).filter(
            Submission.submission_id == submission_id
        ).first()
        
        if submission and submission.video_url:
            try:
                video_result = await self.analyze_video(submission_id, requirements)
                results['video_analysis'] = video_result
            except Exception as e:
                results['video_analysis'] = {"error": str(e)}
        
        self._log(
            submission_id,
            "full_evaluation",
            "completed",
            "Complete evaluation finished"
        )
        
        return results
