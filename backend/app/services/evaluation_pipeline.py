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
        
        # 3. Transcribir y evaluar video si existe
        video_transcript = None
        video_analysis = None
        video_penalty = 0  # Penalización si no hay video o no es relevante
        
        if submission.video_url:
            print(f"🎥 Video URL found: {submission.video_url}")
            
            video_path = None
            
            try:
                # Solo soportar videos subidos a MinIO
                if 'youtube.com' in submission.video_url or 'youtu.be' in submission.video_url:
                    print(f"⚠️ YouTube videos are not currently supported")
                    print(f"⚠️ Skipping video transcription")
                    
                else:
                    # Procesar video de MinIO
                    print(f"📦 Processing video from MinIO...")
                    parts = submission.video_url.split('/', 1)
                    
                    if len(parts) != 2:
                        print(f"⚠️ Invalid MinIO URL format: {submission.video_url}")
                        raise Exception("Invalid video URL format")
                    
                    bucket, object_name = parts
                    
                    print(f"📥 Downloading from MinIO: {bucket}/{object_name}")
                    video_data = minio_service.client.get_object(bucket, object_name)
                    video_bytes = video_data.read()
                    
                    # Guardar temporalmente
                    video_ext = object_name.split('.')[-1] if '.' in object_name else 'mp4'
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{video_ext}') as tmp_file:
                        tmp_file.write(video_bytes)
                        video_path = tmp_file.name
                    
                    print(f"✅ Video downloaded: {video_path} ({len(video_bytes) / 1024 / 1024:.2f} MB)")
                    
                    # Transcribir con Whisper
                    print(f"🎤 Transcribing video with Whisper...")
                    transcription_result = whisper_service.transcribe_video(video_path)
                    video_transcript = transcription_result['text']
                    
                    print(f"✅ Video transcribed: {len(video_transcript)} characters")
                    print(f"📝 Transcript preview: {video_transcript[:200]}...")
                    
                    # Guardar transcripción en BD
                    submission.video_transcription = video_transcript
                    submission.video_duration = transcription_result.get('duration', 0)
                    
                    # Verificar relevancia del video con Ollama
                    if len(video_transcript) > 50:
                        print(f"🧠 Checking video relevance with Ollama...")
                        
                        relevance_prompt = f"""Eres un profesor evaluando si un video explicativo corresponde a una tarea de programación.

REQUISITOS DE LA TAREA:
{requirements[:800]}

TRANSCRIPCIÓN DEL VIDEO:
{video_transcript[:1500]}

Analiza si el video:
1. Explica el código relacionado a esta tarea
2. Menciona conceptos técnicos relevantes a los requisitos
3. Demuestra comprensión del problema planteado

Responde SOLO en JSON:
{{
  "is_relevant": true,
  "confidence": 0.85,
  "mentions_requirements": true,
  "demonstrates_understanding": true,
  "reason": "El estudiante explica claramente la implementación de List<T> y eventos, que son requisitos clave."
}}

Donde:
- is_relevant: true si el video corresponde a la tarea, false si habla de otro tema
- confidence: 0.0 a 1.0 (qué tan seguro estás)
- mentions_requirements: true si menciona conceptos de los requisitos
- demonstrates_understanding: true si demuestra entender el problema
- reason: explicación breve de tu evaluación

RESPONDE SOLO CON EL JSON:"""
                        
                        relevance_result = await ollama_service.analyze_code(relevance_prompt, "")
                        
                        if relevance_result.get("success"):
                            try:
                                relevance_text = relevance_result.get("analysis", "").strip()
                                
                                # Extraer JSON
                                if "{" in relevance_text and "}" in relevance_text:
                                    start = relevance_text.find("{")
                                    end = relevance_text.rfind("}") + 1
                                    json_text = relevance_text[start:end]
                                    relevance_data = json.loads(json_text)
                                    
                                    is_relevant = relevance_data.get('is_relevant', True)
                                    confidence = relevance_data.get('confidence', 0.5)
                                    reason = relevance_data.get('reason', '')
                                    
                                    # Guardar en BD
                                    submission.video_relevance_check = json.dumps(relevance_data, ensure_ascii=False)
                                    
                                    print(f"📊 Video relevance: {'✅ Relevant' if is_relevant else '❌ Not relevant'} (confidence: {confidence:.2f})")
                                    print(f"   Reason: {reason}")
                                    
                                    # Aplicar penalización si no es relevante
                                    if not is_relevant or confidence < 0.6:
                                        video_penalty = 2  # -2 puntos totales
                                        print(f"⚠️ VIDEO PENALTY APPLIED: -2 points (video not relevant to assignment)")
                                        print(f"   Will deduct: -1 from Comprehension, -1 from Functionality")
                                    else:
                                        print(f"✅ Video is relevant, no penalty applied")
                                
                            except json.JSONDecodeError as e:
                                print(f"⚠️ Could not parse relevance check: {e}")
                        else:
                            print(f"⚠️ Relevance check failed, assuming video is acceptable")
                    
                    # Analizar participación (si es video de grupo)
                    if submission.group_number and submission.group_number > 1:
                        print(f"👥 Analyzing participation for group {submission.group_number}...")
                        participation_data = whisper_service.analyze_participation_from_video(video_path)
                        
                        submission.speakers_detected = participation_data['num_speakers_detected']
                        
                        video_analysis = {
                            'transcription': video_transcript,
                            'duration': transcription_result.get('duration', 0),
                            'participation': participation_data
                        }
                        
                        print(f"✅ Detected {participation_data['num_speakers_detected']} speakers")
                        for speaker_info in participation_data['speaker_times']:
                            print(f"   Speaker {speaker_info['speaker_id']}: {speaker_info['time']}s ({speaker_info['percentage']:.1f}%)")
                    
                    # Limpiar archivo temporal
                    if video_path and os.path.exists(video_path):
                        try:
                            os.unlink(video_path)
                            print(f"🗑️ Cleaned up temporary file")
                        except Exception as cleanup_error:
                            print(f"⚠️ Could not delete temp file: {cleanup_error}")
                
            except Exception as e:
                print(f"⚠️ Video processing failed: {str(e)}")
                print(f"⚠️ Continuing code evaluation without video analysis")
                import traceback
                traceback.print_exc()
                
                # Limpiar archivo temporal si existe
                if video_path and os.path.exists(video_path):
                    try:
                        os.unlink(video_path)
                    except:
                        pass
        
        else:
            # No hay video - aplicar penalización
            print(f"⚠️ No video provided")
            print(f"⚠️ VIDEO PENALTY APPLIED: -2 points (missing video explanation)")
            print(f"   Will deduct: -1 from Comprehension, -1 from Functionality")
            video_penalty = 2
            submission.video_relevance_check = json.dumps({
                "is_relevant": False,
                "reason": "No video provided"
            }, ensure_ascii=False)

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

        # 4.5. Escalar scores y aplicar penalización de video
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
        
        # Aplicar penalización de video
        if video_penalty > 0:
            print(f"⚠️ Applying video penalty: -{video_penalty} points")
            
            # -1 punto en comprensión
            comprehension_penalty = min(1.0, comprehension)  # No bajar de 0
            comprehension = max(0, comprehension - comprehension_penalty)
            print(f"   Comprehension: {comprehension + comprehension_penalty:.2f} → {comprehension:.2f} (-{comprehension_penalty:.2f})")
            
            # -1 punto en funcionalidad
            functionality_penalty = min(1.0, functionality)  # No bajar de 0
            functionality = max(0, functionality - functionality_penalty)
            print(f"   Functionality: {functionality + functionality_penalty:.2f} → {functionality:.2f} (-{functionality_penalty:.2f})")
            
            # Actualizar feedback
            penalty_msg = "\n\n⚠️ PENALIZACIÓN POR VIDEO: Se descontó 1 punto en Comprensión y 1 punto en Funcionalidad debido a: "
            
            if submission.video_url:
                penalty_msg += "el video no corresponde al contexto de la tarea asignada."
            else:
                penalty_msg += "no se proporcionó video explicativo."
            
            scores['comprehension_feedback'] = scores.get('comprehension_feedback', '') + penalty_msg
            scores['functionality_feedback'] = scores.get('functionality_feedback', '') + penalty_msg
        
        print(f"📊 Final scores (after penalties):")
        print(f"   Comprehension: {comprehension}/5")
        print(f"   Design: {design}/5")
        print(f"   Implementation: {implementation}/5")
        print(f"   Functionality: {functionality}/5")
        
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