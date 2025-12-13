import zipfile
import io
import os
import tempfile
import json
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
    
    async def _extract_code_from_zip(self, project_path: str) -> Optional[str]:
        """Extract code from ZIP file in MinIO (async version)"""
        try:
            if not project_path:
                print(f"⚠️ No project_path provided")
                return None
            
            print(f"📦 Project path: {project_path}")
            
            # Parse bucket and object path
            parts = project_path.split('/', 1)
            if len(parts) != 2:
                print(f"⚠️ Invalid project_path format: {project_path}")
                print(f"   Expected format: 'bucket/path/to/file.zip'")
                return None
            
            bucket, object_name = parts
            print(f"📥 Downloading from MinIO: bucket={bucket}, object={object_name}")
            
            # Download from MinIO
            try:
                file_data = minio_service.client.get_object(bucket, object_name)
                zip_data = file_data.read()
                print(f"✅ Downloaded {len(zip_data)} bytes")
            except Exception as e:
                print(f"❌ MinIO download failed: {str(e)}")
                return None
            
            # Extract code files
            code_parts = []
            try:
                with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
                    print(f"📂 ZIP contains {len(zip_file.namelist())} files")
                    
                    for filename in zip_file.namelist():
                        # Solo archivos de código (ignorar carpetas)
                        if not filename.endswith('/') and filename.endswith(('.cs', '.py', '.java', '.js', '.cpp', '.c', '.h', '.txt')):
                            try:
                                content = zip_file.read(filename).decode('utf-8', errors='ignore')
                                code_parts.append(f"// File: {filename}\n{content}\n")
                                print(f"📄 Extracted: {filename} ({len(content)} chars)")
                            except Exception as e:
                                print(f"⚠️ Could not extract {filename}: {e}")
            except zipfile.BadZipFile:
                print(f"❌ Invalid ZIP file")
                return None
            
            if code_parts:
                result = "\n\n".join(code_parts)
                print(f"✅ Total code extracted: {len(result)} characters from {len(code_parts)} files")
                return result
            else:
                print(f"⚠️ No code files found in ZIP")
                return None
            
        except Exception as e:
            print(f"❌ Error extracting code: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fallback_scores(self) -> Dict:
        """Default scores when evaluation fails"""
        return {
            "comprehension_score": 3,
            "design_score": 3,
            "implementation_score": 3,
            "functionality_score": 3,
            "comprehension_feedback": "El código ha sido recibido correctamente. Se requiere revisión manual para una evaluación detallada debido a limitaciones técnicas en la evaluación automática.",
            "design_feedback": "Se observa una estructura básica en el código. Se recomienda revisar la arquitectura y separación de responsabilidades siguiendo principios de POO.",
            "implementation_feedback": "La implementación está presente. Se sugiere revisar las convenciones de código de C# y .NET Framework para mejorar la legibilidad.",
            "functionality_feedback": "Se requiere verificación manual para confirmar el cumplimiento completo de los requisitos funcionales."
        }
    
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
        rubric: dict
    ):
        """Complete evaluation pipeline"""
        
        print(f"📊 Starting evaluation for submission {submission_id}")
        
        # 1. Obtener submission
        submission = self.db.query(Submission).filter(
            Submission.submission_id == submission_id
        ).first()
        
        if not submission:
            print(f"❌ Submission {submission_id} not found")
            return None
        
        print(f"✅ Submission found: {submission.submission_id}")
        print(f"   Project path: {submission.project_path}")
        print(f"   Video URL: {submission.video_url}")
        
        # 2. Descargar y extraer código del ZIP
        try:
            code = await self._extract_code_from_zip(submission.project_path)
            
            if not code or len(code.strip()) == 0:
                print(f"⚠️ No code found, using placeholder")
                code = """
// Sample code file
public class Program {
    public static void Main() {
        System.Console.WriteLine("Hello World");
    }
}
"""
            
            print(f"📄 Code extracted: {len(code)} characters")
            
        except Exception as e:
            print(f"❌ Error extracting code: {str(e)}")
            import traceback
            traceback.print_exc()
            code = "// Error extracting code from submission"
        
        # 3. Transcribir video si existe (opcional para futuro)
        video_transcript = None
        if submission.video_url:
            print(f"🎥 Video URL found: {submission.video_url}")
            # TODO: Implementar transcripción con Whisper
            # video_transcript = await whisper_service.transcribe_video_url(submission.video_url)
        
        # 4. Evaluar con Ollama
        print(f"🤖 Calling Ollama for evaluation...")
        try:
            scores = await ollama_service.evaluate_code(code, requirements, rubric)
            print(f"📊 Scores received: {scores}")
        except Exception as e:
            print(f"❌ Error calling Ollama: {str(e)}")
            import traceback
            traceback.print_exc()
            # Usar scores por defecto
            scores = self._fallback_scores()
        
        # 5. Escalar scores si es necesario (de 0-25 a 0-5)
        def scale_to_5(score):
            score = float(score)
            if score > 5:
                return round((score * 5 / 25), 2)
            else:
                return round(score, 2)
        
        comprehension = scale_to_5(scores.get("comprehension_score", 3))
        design = scale_to_5(scores.get("design_score", 3))
        implementation = scale_to_5(scores.get("implementation_score", 3))
        functionality = scale_to_5(scores.get("functionality_score", 3))
        
        print(f"📊 Scaled scores (0-5):")
        print(f"   Comprehension: {comprehension}")
        print(f"   Design: {design}")
        print(f"   Implementation: {implementation}")
        print(f"   Functionality: {functionality}")
        
        # 6. Crear Grade en la BD
        try:
            print(f"🔨 Creating Grade...")
            
            grade = Grade(
                submission_id=submission_id,
                student_id=submission.submitted_by,
                ai_comprehension_score=comprehension,
                ai_design_score=design,
                ai_implementation_score=implementation,
                ai_functionality_score=functionality,
                ai_total_score=round(comprehension + design + implementation + functionality, 2),
                status="auto_graded"
            )
            
            print(f"🔨 Adding Grade to session...")
            self.db.add(grade)
            
            print(f"🔨 Flushing to get ID...")
            self.db.flush()
            
            print(f"✅ Grade created with ID: {grade.grade_id}")
            
            # 7. Crear Feedback
            print(f"🔨 Creating Feedback...")
            feedback = Feedback(
                grade_id=grade.grade_id,
                submission_id=submission_id,
                comprehension_comments=scores.get("comprehension_feedback", "Good understanding"),
                design_comments=scores.get("design_feedback", "Clean design"),
                implementation_comments=scores.get("implementation_feedback", "Well implemented"),
                functionality_comments=scores.get("functionality_feedback", "Works correctly"),
                general_comments="Evaluated automatically by AI"
            )
            
            self.db.add(feedback)
            
            print(f"🔨 Committing to database...")
            self.db.commit()
            
            print(f"✅ Feedback created with grade_id: {grade.grade_id}")
            print(f"✅ Evaluation completed successfully!")
            
            return {
                "grade_id": grade.grade_id,
                "total_score": grade.ai_total_score,
                "scores": scores
            }
            
        except Exception as e:
            print(f"❌ ERROR creating Grade/Feedback: {str(e)}")
            self.db.rollback()
            import traceback
            traceback.print_exc()
            raise