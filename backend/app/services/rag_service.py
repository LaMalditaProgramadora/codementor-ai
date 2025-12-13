"""
Servicio RAG para búsqueda de evaluaciones similares.
Usa el dataset.jsonl para encontrar proyectos similares y enriquecer los prompts.

Ubicación: backend/app/services/rag_service.py
"""

import json
import os
from typing import List, Dict, Optional

# Configuración
DATASET_PATH = os.getenv("DATASET_PATH", "/app/app/entrenamiento/dataset.jsonl")


class RAGService:
    """
    Servicio de Retrieval Augmented Generation.
    Busca evaluaciones históricas similares para incluir en el prompt.
    """
    
    def __init__(self):
        self.dataset: List[Dict] = []
        self.db_pool = None  # Para pgvector (futuro)
        self._cargar_dataset()
    
    def _cargar_dataset(self):
        """Carga el dataset en memoria"""
        if os.path.exists(DATASET_PATH):
            try:
                with open(DATASET_PATH, 'r', encoding='utf-8') as f:
                    for linea in f:
                        if linea.strip():
                            self.dataset.append(json.loads(linea))
                print(f"✅ RAG Dataset cargado: {len(self.dataset)} evaluaciones históricas")
            except Exception as e:
                print(f"⚠️ Error cargando dataset RAG: {e}")
                self.dataset = []
        else:
            print(f"⚠️ Dataset RAG no encontrado en: {DATASET_PATH}")
            print(f"   El sistema funcionará sin ejemplos históricos")
    
    def buscar_similares_simple(self, codigo: str, limit: int = 5) -> List[Dict]:
        """
        Búsqueda simple por keywords (fallback sin pgvector).
        Para producción, usar pgvector con embeddings.
        """
        if not self.dataset:
            return []
        
        # Extraer keywords del código (palabras relevantes)
        keywords = set()
        for palabra in codigo.lower().replace('\n', ' ').replace('\t', ' ').split():
            # Filtrar palabras muy cortas y keywords de C#
            if len(palabra) > 3 and palabra not in {'using', 'public', 'private', 'class', 'void', 'static', 'string', 'return', 'this', 'null', 'true', 'false'}:
                keywords.add(palabra)
        
        # Puntuar cada ejemplo por coincidencia
        scored = []
        for ejemplo in self.dataset:
            codigo_ejemplo = ejemplo.get('codigo', '').lower()
            
            # Contar coincidencias de keywords
            coincidencias = sum(1 for kw in keywords if kw in codigo_ejemplo)
            
            # Bonus si es la misma semana (similar complejidad)
            semana_ejemplo = ejemplo.get('semana', '')
            
            scored.append((coincidencias, ejemplo))
        
        # Ordenar por coincidencias y retornar top N
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Filtrar los que tienen al menos algunas coincidencias
        resultados = [item[1] for item in scored[:limit] if item[0] > 0]
        
        if resultados:
            print(f"🔍 RAG: Encontrados {len(resultados)} proyectos similares")
        
        return resultados
    
    async def buscar_similares_pgvector(self, codigo: str, limit: int = 5) -> List[Dict]:
        """
        Búsqueda semántica con pgvector (requiere embeddings cargados).
        TODO: Implementar cuando se cargue el dataset con embeddings.
        """
        # Por ahora, usar fallback
        return self.buscar_similares_simple(codigo, limit)
    
    async def buscar_similares(self, codigo: str, limit: int = 5) -> List[Dict]:
        """Método principal de búsqueda"""
        # Intentar pgvector primero (futuro)
        # resultados = await self.buscar_similares_pgvector(codigo, limit)
        
        # Por ahora usar búsqueda simple
        resultados = self.buscar_similares_simple(codigo, limit)
        
        return resultados
    
    def formatear_ejemplos_para_prompt(self, ejemplos: List[Dict]) -> str:
        """
        Formatea los ejemplos históricos para incluir en el prompt de Ollama.
        """
        if not ejemplos:
            return ""
        
        texto = "\n═══════════════════════════════════════════════════════\n"
        texto += "EJEMPLOS DE EVALUACIONES ANTERIORES (usa este criterio):\n"
        texto += "═══════════════════════════════════════════════════════\n\n"
        
        for i, ej in enumerate(ejemplos, 1):
            # Obtener rúbrica
            rubrica = ej.get('rubrica', {})
            comprension = rubrica.get('comprension', 'N/A')
            diseno = rubrica.get('diseno', 'N/A')
            implementacion = rubrica.get('implementacion', 'N/A')
            funcionalidad = rubrica.get('funcionalidad', 'N/A')
            
            # Truncar código si es muy largo
            codigo = ej.get('codigo', '')
            if len(codigo) > 800:
                codigo = codigo[:800] + "\n// ... (código truncado)"
            
            texto += f"""### Ejemplo {i}: Puntaje {ej.get('puntaje_total', 'N/A')}/20
Rúbrica:
- Comprensión: {comprension}/5
- Diseño: {diseno}/5
- Implementación: {implementacion}/5
- Funcionalidad: {funcionalidad}/5

Feedback del profesor:
{ej.get('feedback', 'Sin feedback')}

Fragmento del código evaluado:
```csharp
{codigo}
```

---
"""
        
        texto += "\n⚠️ IMPORTANTE: Evalúa el nuevo código con el MISMO criterio de los ejemplos anteriores.\n\n"
        
        return texto
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del dataset"""
        if not self.dataset:
            return {"total": 0, "loaded": False}
        
        puntajes = [d.get('puntaje_total', 0) for d in self.dataset]
        
        return {
            "total": len(self.dataset),
            "loaded": True,
            "puntaje_promedio": round(sum(puntajes) / len(puntajes), 2) if puntajes else 0,
            "puntaje_min": min(puntajes) if puntajes else 0,
            "puntaje_max": max(puntajes) if puntajes else 0
        }


# Singleton
rag_service = RAGService()
