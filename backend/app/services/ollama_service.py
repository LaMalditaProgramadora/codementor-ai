import httpx
from typing import Dict, Optional
import json
import os

class OllamaService:
    def __init__(self):
        # Leer variables de entorno
        self.base_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "6000"))  # 15 minutos
        
        print(f"🔧 OllamaService initialized with URL: {self.base_url}")
        print(f"🔧 Model: {self.model}, Timeout: {self.timeout}s")
    
    async def check_health(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.base_url)
                return response.status_code == 200
        except:
            return False
    
    async def analyze_code(self, code: str, requirements: str = "", context: Dict = None) -> Dict:
        """Analyze code with Llama"""
        try:
            # Construir el prompt
            if requirements:
                prompt = f"Analyze this code against requirements:\n\nRequirements: {requirements}\n\nCode:\n{code[:2000]}"
            else:
                prompt = code
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
                
                # ✅ Headers para bypass de ngrok
                headers = {
                    "ngrok-skip-browser-warning": "true",
                    "User-Agent": "CodeMentor-Backend/1.0"
                }
                
                print(f"🔍 Calling Ollama at {self.base_url} with model: {self.model}")
                
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers=headers  # ✅ Agregar headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                print(f"✅ Ollama response received")
                
                return {
                    "analysis": result.get("response", ""),
                    "model": self.model,
                    "success": True
                }
                
        except Exception as e:
            print(f"❌ Error calling Ollama: {str(e)}")
            return {
                "analysis": "",
                "error": str(e),
                "success": False
            }
    
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

2. DISEÑO DE LA SOLUCIÓN (0-5 puntos):
   - Arquitectura de clases y separación de responsabilidades
   - Uso apropiado de List<T> y estructuras de datos
   - Aplicación correcta de POO

3. IMPLEMENTACIÓN (0-5 puntos):
   - Calidad del código (legibilidad, nomenclatura)
   - Uso correcto de C# y .NET Framework
   - Manejo adecuado de eventos

4. FUNCIONALIDAD (0-5 puntos):
   - Cumplimiento de requisitos funcionales
   - Validaciones de datos implementadas
   - Flujo de navegación coherente

═══════════════════════════════════════════════════════
REQUISITOS:
{requirements[:800]}

CÓDIGO:
{code[:1500]}

═══════════════════════════════════════════════════════

Responde ÚNICAMENTE en JSON con esta estructura exacta:

{{
  "comprehension_score": 4,
  "design_score": 3,
  "implementation_score": 4,
  "functionality_score": 4,
  "comprehension_feedback": "El estudiante demuestra buena comprensión. Ha implementado [ejemplos específicos]. Falta [aspectos]. Sugerencia: [recomendación].",
  "design_feedback": "La arquitectura presenta [análisis]. Puntos positivos: [ejemplos]. Áreas de mejora: [sugerencias].",
  "implementation_feedback": "Calidad del código: [evaluación]. Puntos fuertes: [ejemplos]. Considerar mejorar: [sugerencias].",
  "functionality_feedback": "El proyecto cumple con [requisitos]. Funcionalidad: [detalles]. Pendiente: [aspectos]."
}}

IMPORTANTE: 
- Cada score debe ser 0-5 (NO 0-25)
- Feedback específico y constructivo
- Si nota total >= 16: menciona "¡Buen trabajo!"
- Si nota total == 20: menciona "¡Excelente trabajo!"
- Si nota total < 16: feedback detallado

RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL:"""
        
        result = await self.analyze_code(prompt, "")
        
        print(f"🔍 DEBUG - Result success: {result.get('success')}")
        print(f"🔍 DEBUG - Result keys: {result.keys()}")
        if result.get('analysis'):
            print(f"🔍 DEBUG - Analysis preview: {str(result.get('analysis', ''))[:300]}")
        
        if not result.get("success"):
            print(f"❌ LLM call failed: {result.get('error')}")
            return self._fallback_scores()
        
        # Parse JSON
        try:
            analysis_text = result.get("analysis", "").strip()
            
            if not analysis_text:
                print(f"❌ Empty response from Ollama")
                return self._fallback_scores()
            
            # Buscar JSON en la respuesta
            if "{" in analysis_text and "}" in analysis_text:
                start = analysis_text.find("{")
                end = analysis_text.rfind("}") + 1
                json_text = analysis_text[start:end]
            else:
                print(f"❌ No JSON found in response")
                print(f"   Raw response: {analysis_text[:500]}")
                return self._fallback_scores()
            
            print(f"📝 Parsing JSON... ({len(json_text)} chars)")
            scores = json.loads(json_text)
            
            # Validar y escalar scores si es necesario
            for key in ["comprehension_score", "design_score", "implementation_score", "functionality_score"]:
                if key in scores:
                    score = float(scores[key])
                    if score > 5:
                        print(f"⚠️ Score {key}={score} > 5, scaling down to 0-5 range")
                        scores[key] = round(score * 5 / 25, 2)  # Convertir 0-25 a 0-5
                    else:
                        scores[key] = round(score, 2)
            
            print(f"✅ Scores parsed successfully:")
            print(f"   Comprehension: {scores.get('comprehension_score', 0)}/5")
            print(f"   Design: {scores.get('design_score', 0)}/5")
            print(f"   Implementation: {scores.get('implementation_score', 0)}/5")
            print(f"   Functionality: {scores.get('functionality_score', 0)}/5")
            
            # Validar que tenga todos los campos requeridos
            required_fields = [
                "comprehension_score", "design_score", 
                "implementation_score", "functionality_score",
                "comprehension_feedback", "design_feedback",
                "implementation_feedback", "functionality_feedback"
            ]
            
            missing_fields = [f for f in required_fields if f not in scores]
            
            if missing_fields:
                print(f"⚠️ Missing fields: {missing_fields}")
                # Agregar campos faltantes con valores por defecto
                for field in missing_fields:
                    if field.endswith('_score'):
                        scores[field] = 3
                    else:
                        scores[field] = "Feedback no disponible"
            
            return scores
            
        except json.JSONDecodeError as e:
            print(f"❌ Parse error: {e}")
            print(f"   Attempted to parse: {json_text[:500]}")
            return self._fallback_scores()
        except Exception as e:
            print(f"❌ Unexpected error during parsing: {e}")
            import traceback
            traceback.print_exc()
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

# Singleton instance
ollama_service = OllamaService()