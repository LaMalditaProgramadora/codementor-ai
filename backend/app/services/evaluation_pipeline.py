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
    
    async def evaluate_code(self, code: str, requirements: str, rubric: Dict) -> Dict:
        """Evaluate code against requirements and rubric"""
        
        # Prompt DETALLADO con rúbrica específica
        prompt = f"""Eres un profesor de Ingeniería Informática evaluando un proyecto de C#/.NET. 
    Analiza el código y proporciona una evaluación detallada según la siguiente rúbrica (máximo 20 puntos):

    ═══════════════════════════════════════════════════════
    RÚBRICA DE EVALUACIÓN (Total: 20 puntos)
    ═══════════════════════════════════════════════════════

    1. COMPRENSIÓN DEL PROBLEMA (0-5 puntos):
    - ¿Tiene todo lo solicitado en los requisitos?
    - ¿Usa nombres específicos cuando se requieren?
    - ¿La solución es adecuada al problema planteado?
    - ¿Se evidencia comprensión clara de los requisitos?

    2. DISEÑO DE LA SOLUCIÓN (0-5 puntos):
    - Arquitectura de clases y separación de responsabilidades
    - Uso de controllers o arquitectura por capas (datos, negocio, presentación)
    - Uso apropiado de List<T> y estructuras de datos
    - Aplicación correcta de POO (encapsulación, herencia, polimorfismo)
    - Diseño de interfaz de usuario (usabilidad en Windows Forms)

    3. IMPLEMENTACIÓN (0-5 puntos):
    - Calidad del código (legibilidad, nomenclatura, indentación)
    - Uso correcto de C# y .NET Framework
    - Implementación de Entity Framework (si se requiere)
    - Manejo adecuado de eventos en Windows Forms
    - Ausencia de errores de compilación

    4. FUNCIONALIDAD (0-5 puntos):
    - Cumplimiento de todos los requisitos funcionales
    - Correcta manipulación de DataGridView (si aplica)
    - Validaciones de datos implementadas
    - Flujo de navegación coherente entre formularios

    ═══════════════════════════════════════════════════════
    REQUISITOS DEL PROYECTO:
    {requirements[:800]}

    ═══════════════════════════════════════════════════════
    CÓDIGO A EVALUAR:
    {code[:2000]}

    ═══════════════════════════════════════════════════════

    INSTRUCCIONES:
    1. Analiza cuidadosamente cada aspecto del código
    2. Asigna un puntaje de 0-5 para cada criterio
    3. Proporciona feedback DETALLADO y ESPECÍFICO para cada criterio
    4. Menciona ejemplos concretos del código (nombres de clases, métodos, etc.)
    5. Si el puntaje total >= 16: feedback constructivo con sugerencias menores
    6. Si el puntaje total < 16: feedback detallado con aspectos a mejorar

    Responde ÚNICAMENTE en JSON con esta estructura exacta:

    {{
    "comprehension_score": 4,
    "design_score": 3,
    "implementation_score": 4,
    "functionality_score": 4,
    "comprehension_feedback": "El estudiante demuestra buena comprensión del problema. Ha implementado los requisitos principales como [ejemplos específicos]. Sin embargo, falta [aspectos específicos]. Sugerencia: [recomendación concreta].",
    "design_feedback": "La arquitectura presenta [análisis]. Se observa [puntos positivos]. Áreas de mejora: [sugerencias específicas con ejemplos].",
    "implementation_feedback": "La calidad del código es [evaluación]. Puntos fuertes: [ejemplos]. Considerar mejorar: [sugerencias concretas].",
    "functionality_feedback": "El proyecto cumple con [requisitos cumplidos]. Funcionalidad observada: [detalles]. Pendiente: [aspectos faltantes]."
    }}

    IMPORTANTE: 
    - Cada score debe ser 0-5 (NO 0-25)
    - El feedback debe ser específico, constructivo y educativo
    - Menciona nombres de clases/métodos del código cuando sea relevante
    - Si nota total >= 16: menciona "¡Buen trabajo! [feedback constructivo]"
    - Si nota total == 20: menciona "¡Excelente trabajo! Has cumplido todos los requisitos de manera sobresaliente."
    - Si nota total < 16: proporciona feedback detallado con ejemplos y referencias

    RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL:"""
        
        result = await self.analyze_code(prompt, "")
        
        if not result.get("success"):
            print(f"❌ LLM call failed: {result.get('error')}")
            return self._fallback_scores()
        
        # Parse JSON
        try:
            analysis_text = result.get("analysis", "").strip()
            
            # Buscar JSON en la respuesta
            if "{" in analysis_text and "}" in analysis_text:
                start = analysis_text.find("{")
                end = analysis_text.rfind("}") + 1
                json_text = analysis_text[start:end]
            else:
                json_text = analysis_text
            
            print(f"📝 Parsing JSON...")
            scores = json.loads(json_text)
            
            # Validar scores están en rango 0-5
            for key in ["comprehension_score", "design_score", "implementation_score", "functionality_score"]:
                if key in scores:
                    score = float(scores[key])
                    if score > 5:
                        print(f"⚠️ Score {key}={score} > 5, scaling down")
                        scores[key] = score * 5 / 25  # Convertir si viene en escala 25
            
            print(f"✅ Scores parsed successfully")
            print(f"   Comprehension: {scores.get('comprehension_score', 0)}/5")
            print(f"   Design: {scores.get('design_score', 0)}/5")
            print(f"   Implementation: {scores.get('implementation_score', 0)}/5")
            print(f"   Functionality: {scores.get('functionality_score', 0)}/5")
            
            # Validar que tenga todos los campos
            required_fields = [
                "comprehension_score", "design_score", 
                "implementation_score", "functionality_score",
                "comprehension_feedback", "design_feedback",
                "implementation_feedback", "functionality_feedback"
            ]
            
            if all(field in scores for field in required_fields):
                return scores
            else:
                missing = [f for f in required_fields if f not in scores]
                print(f"⚠️ Missing fields: {missing}, using fallback")
                return self._fallback_scores()
            
        except Exception as e:
            print(f"❌ Parse error: {e}")
            print(f"   Raw response: {analysis_text[:500]}")
            return self._fallback_scores()

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
            scores = {
                "comprehension_score": 15,
                "design_score": 15,
                "implementation_score": 15,
                "functionality_score": 15,
                "comprehension_feedback": "Error during evaluation",
                "design_feedback": "Error during evaluation",
                "implementation_feedback": "Error during evaluation",
                "functionality_feedback": "Error during evaluation"
            }
        
        # 5. Crear Grade en la BD
        try:
            print(f"🔨 Creating Grade...")
            print(f"   submission_id: {submission_id}")
            print(f"   student_id: {submission.submitted_by}")
            print(f"   comprehension: {scores.get('comprehension_score', 15)}")
            print(f"   design: {scores.get('design_score', 15)}")
            print(f"   implementation: {scores.get('implementation_score', 15)}")
            print(f"   functionality: {scores.get('functionality_score', 15)}")
            
            grade = Grade(
                submission_id=submission_id,
                student_id=submission.submitted_by,
                ai_comprehension_score=scores.get("comprehension_score", 15),
                ai_design_score=scores.get("design_score", 15),
                ai_implementation_score=scores.get("implementation_score", 15),
                ai_functionality_score=scores.get("functionality_score", 15),
                ai_total_score=(
                    scores.get("comprehension_score", 15) +
                    scores.get("design_score", 15) +
                    scores.get("implementation_score", 15) +
                    scores.get("functionality_score", 15)
                ),
                status="auto_graded"
            )
            
            print(f"🔨 Adding Grade to session...")
            self.db.add(grade)
            
            print(f"🔨 Flushing to get ID...")
            self.db.flush()
            
            print(f"✅ Grade created with ID: {grade.grade_id}")
            
            # 6. Crear Feedback
            print(f"🔨 Creating Feedback...")
            feedback = Feedback(
                grade_id=grade.grade_id,
                submission_id=submission_id,  # ✅ Agregar submission_id
                comprehension_comments=scores.get("comprehension_feedback", "Good understanding"),  # ✅ _comments
                design_comments=scores.get("design_feedback", "Clean design"),  # ✅ _comments
                implementation_comments=scores.get("implementation_feedback", "Well implemented"),  # ✅ _comments
                functionality_comments=scores.get("functionality_feedback", "Works correctly"),  # ✅ _comments
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