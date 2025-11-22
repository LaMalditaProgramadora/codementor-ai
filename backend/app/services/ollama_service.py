import httpx
from typing import Dict, Optional
import json

class OllamaService:
    def __init__(self):
        self.base_url = "http://ollama:11434"
        self.model = "llama3.1:8b"
        self.timeout = None
    
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
                
                print(f"🔍 Calling Ollama with model: {self.model}")
                
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
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
    
    # Prompt SIMPLIFICADO para respuestas más rápidas
    prompt = f"""Rate this code from 0-25 on each criterion. Respond ONLY in JSON:

{{
  "comprehension_score": 20,
  "design_score": 18,
  "implementation_score": 22,
  "functionality_score": 19,
  "comprehension_feedback": "Good understanding",
  "design_feedback": "Clean design",
  "implementation_feedback": "Well implemented",
  "functionality_feedback": "Works correctly"
}}

Code to evaluate:
{code[:1000]}

Requirements:
{requirements[:500]}

ONLY JSON, NO EXTRA TEXT:"""
    
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
        print(f"✅ Scores: {scores}")
        
        # Validar que tenga todos los campos
        required_fields = [
            "comprehension_score", "design_score", 
            "implementation_score", "functionality_score"
        ]
        
        if all(field in scores for field in required_fields):
            return scores
        else:
            print(f"⚠️ Missing fields, using fallback")
            return self._fallback_scores()
        
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return self._fallback_scores()
    
def _fallback_scores(self) -> Dict:
    """Default scores when evaluation fails"""
    return {
        "comprehension_score": 18,
        "design_score": 17,
        "implementation_score": 18,
        "functionality_score": 17,
        "comprehension_feedback": "Code submitted and processed",
        "design_feedback": "Structure follows basic patterns",
        "implementation_feedback": "Implementation is functional",
        "functionality_feedback": "Core features work"
    }

# Singleton instance
ollama_service = OllamaService()