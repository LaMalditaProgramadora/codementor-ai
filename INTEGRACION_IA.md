# 🤖 Guía de Integración con Servicios de IA

Esta guía explica cómo configurar y utilizar cada uno de los servicios de IA en CodeMentor AI.

## 📋 Tabla de Contenidos

1. [Ollama con Llama 3.1](#ollama-con-llama-31)
2. [CodeBERT](#codebert)
3. [Whisper](#whisper)
4. [Pipeline de Evaluación](#pipeline-de-evaluación)

---

## 1. Ollama con Llama 3.1

### ¿Qué es Ollama?

Ollama es una plataforma para ejecutar modelos de lenguaje grandes (LLMs) localmente. En CodeMentor AI, usamos Ollama para ejecutar Llama 3.1 70B, que realiza la evaluación inteligente del código.

### Instalación y Configuración

#### Opción 1: Con GPU NVIDIA (Recomendado)

**Requisitos:**
- GPU NVIDIA con al menos 48GB VRAM para Llama 3.1 70B
- NVIDIA Driver actualizado (>= 525.60.13)
- NVIDIA Container Toolkit

**Pasos:**

1. **Verificar GPU:**
```bash
nvidia-smi
```

2. **Instalar NVIDIA Container Toolkit:**
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

3. **Iniciar Ollama con GPU:**
```bash
docker-compose up -d ollama
```

4. **Descargar Llama 3.1 70B:**
```bash
docker exec -it codementor-ollama ollama pull llama3.1:70b
```

Este proceso descargará ~40GB de datos y puede tomar 30-60 minutos dependiendo de tu conexión.

#### Opción 2: Solo CPU (Para Testing)

Si no tienes GPU, puedes usar Llama 3.1 8B:

```bash
# Descargar modelo más pequeño
docker exec -it codementor-ollama ollama pull llama3.1:8b

# Actualizar configuración
# En backend/.env cambiar:
# OLLAMA_MODEL=llama3.1:8b
```

### Verificar Instalación

```bash
# Verificar que Ollama está corriendo
curl http://ollama:11434/api/tags

# Probar generación de texto
docker exec -it codementor-ollama ollama run llama3.1:70b "Explica qué es un algoritmo"

# Probar desde Python
docker exec -it codementor-backend python3 -c "
import asyncio
from app.services.ollama_service import ollama_service

async def test():
    result = await ollama_service.generate('Hola, ¿cómo estás?')
    print(result)

asyncio.run(test())
"
```

### Uso en el Código

El servicio de Ollama se encuentra en `backend/app/services/ollama_service.py`.

**Ejemplo básico:**

```python
from app.services.ollama_service import ollama_service

# Generar texto
response = await ollama_service.generate(
    prompt="Analiza este código Python: print('Hello')",
    system_prompt="Eres un experto en programación"
)

# Analizar código con rúbrica
analysis = await ollama_service.analyze_code(
    code="tu código aquí",
    requirements="requisitos del proyecto",
    rubric={
        "comprehension": {"max_score": 25},
        "design": {"max_score": 25},
        "implementation": {"max_score": 25},
        "functionality": {"max_score": 25}
    }
)
```

### Personalizar Prompts

Los prompts para evaluación de código están en `ollama_service.py`:

```python
def analyze_code(self, code: str, requirements: str, rubric: Dict):
    system_prompt = """Eres un profesor experto en programación..."""
    
    prompt = f"""
    Analiza el siguiente código según estos criterios:
    
    REQUISITOS: {requirements}
    RÚBRICA: {rubric}
    CÓDIGO: {code}
    
    Proporciona evaluación en formato JSON...
    """
```

**Mejores prácticas para prompts:**

1. **Ser específico**: Define claramente qué esperas en la respuesta
2. **Usar formato estructurado**: Pide JSON para facilitar el parsing
3. **Incluir ejemplos**: Si es posible, muestra ejemplos de respuestas esperadas
4. **Controlar temperatura**: Usa 0.7 para balance entre creatividad y consistencia

### Configuración Avanzada

**Ajustar parámetros del modelo:**

```python
payload = {
    "model": self.model,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.7,      # 0-1, mayor = más creativo
        "top_p": 0.9,            # Nucleus sampling
        "top_k": 40,             # Top-k sampling
        "num_predict": 2048,     # Máx tokens en respuesta
        "stop": ["```"]          # Secuencias de parada
    }
}
```

### Troubleshooting

**Problema: "Model not found"**
```bash
# Listar modelos disponibles
docker exec -it codementor-ollama ollama list

# Si no aparece, descargarlo
docker exec -it codementor-ollama ollama pull llama3.1:70b
```

**Problema: Out of Memory**
```bash
# Ver uso de memoria
nvidia-smi

# Usar modelo más pequeño o aumentar swap
```

---

## 2. CodeBERT

### ¿Qué es CodeBERT?

CodeBERT es un modelo pre-entrenado de Microsoft para entender código fuente. Lo usamos para:
- Detección de plagio semántico
- Generación de embeddings de código
- Análisis de similitud estructural

### Instalación

CodeBERT se instala automáticamente con transformers:

```bash
pip install transformers torch
```

### Configuración

En `backend/.env`:
```
CODEBERT_MODEL=microsoft/codebert-base
SIMILARITY_THRESHOLD=0.85
```

### Primera Ejecución

La primera vez que uses CodeBERT, descargará el modelo (~500MB):

```bash
docker exec -it codementor-backend python3 -c "
from app.services.codebert_service import codebert_service
codebert_service.initialize()
print('✓ CodeBERT listo')
"
```

### Uso en el Código

**1. Generar Embeddings:**

```python
from app.services.codebert_service import codebert_service

code = '''
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
'''

# Obtener embedding vectorial
embedding = codebert_service.get_code_embedding(code)
print(embedding.shape)  # (768,)
```

**2. Calcular Similitud:**

```python
code1 = "def suma(a, b): return a + b"
code2 = "def add(x, y): return x + y"

similarity = codebert_service.calculate_similarity(code1, code2)
print(f"Similitud: {similarity:.2%}")  # Ej: Similitud: 92.5%
```

**3. Detectar Plagio:**

```python
submissions = [
    {'id': 1, 'code': 'código del estudiante 1'},
    {'id': 2, 'code': 'código del estudiante 2'},
    {'id': 3, 'code': 'código del estudiante 3'},
]

detections = codebert_service.detect_plagiarism(submissions)

for detection in detections:
    print(f"Posible plagio entre {detection['submission_id_1']} y {detection['submission_id_2']}")
    print(f"Similitud: {detection['semantic_similarity']}%")
```

### Ajustar Umbral de Similitud

```python
# En el código
codebert_service.similarity_threshold = 0.90  # Más estricto

# O en .env
SIMILARITY_THRESHOLD=0.90
```

**Guía de umbrales:**
- `0.95-1.0`: Muy sospechoso (casi idéntico)
- `0.85-0.95`: Revisar manualmente
- `0.70-0.85`: Similar pero posiblemente aceptable
- `<0.70`: Diferente

### Similitud Estructural vs Semántica

CodeMentor AI calcula ambas:

```python
# Similitud semántica (CodeBERT)
semantic = codebert_service.calculate_similarity(code1, code2)

# Similitud estructural (tokens)
structural = codebert_service.calculate_structural_similarity(code1, code2)

# Combinar para decisión final
if semantic > 0.90 and structural > 0.80:
    print("Plagio muy probable")
```

### Performance

CodeBERT puede procesar ~10-20 códigos/segundo en CPU.

Para mejorar performance:

```python
# Procesar en batch
codes = ["código1", "código2", "código3", ...]
embeddings = codebert_service.batch_get_embeddings(codes)
```

---

## 3. Whisper

### ¿Qué es Whisper?

Whisper es el modelo de reconocimiento de voz de OpenAI. Lo usamos para:
- Transcribir videos de presentaciones
- Detectar participantes en videos grupales
- Analizar calidad de explicaciones

### Instalación

```bash
pip install openai-whisper ffmpeg-python
```

### Modelos Disponibles

| Modelo | Tamaño | RAM | Velocidad | Precisión |
|--------|--------|-----|-----------|-----------|
| tiny   | 39 MB  | 1 GB | Muy rápida | Básica |
| base   | 74 MB  | 1 GB | Rápida | Buena ⭐ |
| small  | 244 MB | 2 GB | Media | Muy buena |
| medium | 769 MB | 5 GB | Lenta | Excelente |
| large  | 1.5 GB | 10 GB | Muy lenta | Máxima |

**Recomendado: `base` para balance entre velocidad y precisión**

### Configuración

En `backend/.env`:
```
WHISPER_MODEL=base
```

### Primera Ejecución

```bash
docker exec -it codementor-backend python3 -c "
from app.services.whisper_service import whisper_service
whisper_service.initialize()
print('✓ Whisper listo')
"
```

### Uso en el Código

**1. Transcribir Audio/Video:**

```python
from app.services.whisper_service import whisper_service

# Transcribir video
result = whisper_service.transcribe_video(
    video_path="presentacion.mp4",
    language="es"  # español
)

print(result['text'])  # Texto completo
print(result['duration'])  # Duración en segundos
print(result['language'])  # Idioma detectado
```

**2. Transcribir con Timestamps:**

```python
result = whisper_service.transcribe_with_timestamps(
    audio_path="audio.mp3",
    language="es"
)

for segment in result['segments']:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}")
```

**3. Detectar Participantes:**

```python
segments = result['segments']
speaker_info = whisper_service.detect_speakers(segments)

print(f"Número de hablantes detectados: {speaker_info['num_speakers']}")

for i, speaker in enumerate(speaker_info['speakers']):
    print(f"Hablante {i+1}: {speaker['total_time']:.2f} segundos")
```

**4. Analizar Participación (Completo):**

```python
participation = whisper_service.analyze_participation_from_video(
    video_path="presentacion_grupal.mp4"
)

print(f"Duración total: {participation['total_duration']}s")
print(f"Transcripción: {participation['transcription']}")

for speaker in participation['speaker_times']:
    print(f"Hablante {speaker['speaker_id']}: {speaker['percentage']:.1f}%")
```

### Idiomas Soportados

Whisper soporta 99 idiomas. Los más relevantes:

```python
# Español
result = whisper_service.transcribe_video(path, language="es")

# Inglés
result = whisper_service.transcribe_video(path, language="en")

# Detección automática
result = whisper_service.transcribe_video(path)  # Auto-detecta
```

### Extraer Audio de Video

```python
audio_path = whisper_service.extract_audio_from_video(
    video_path="video.mp4",
    output_path="audio.wav"  # Opcional
)
```

### Performance

Tiempos aproximados (modelo base):
- Video 5 min: ~30 segundos
- Video 15 min: ~1.5 minutos
- Video 30 min: ~3 minutos

---

## 4. Pipeline de Evaluación

### Arquitectura del Pipeline

```
Submission
    │
    ├─► Extract Code from ZIP
    │       │
    │       ├─► Ollama (Code Analysis)
    │       │       └─► Generate Feedback
    │       │
    │       └─► CodeBERT (Plagiarism Check)
    │
    └─► Extract Video
            │
            └─► Whisper (Transcription)
                    │
                    └─► Ollama (Video Analysis)
                            └─► Participation Insights
```

### Uso del Pipeline

El pipeline está en `backend/app/services/evaluation_pipeline.py`:

```python
from sqlalchemy.orm import Session
from app.services.evaluation_pipeline import EvaluationPipeline

# Crear pipeline
pipeline = EvaluationPipeline(db_session)

# Evaluar solo código
code_result = await pipeline.evaluate_code(
    submission_id=1,
    requirements="Desarrollar CRUD completo",
    rubric={
        "comprehension": {"max_score": 25},
        "design": {"max_score": 25},
        "implementation": {"max_score": 25},
        "functionality": {"max_score": 25}
    }
)

# Evaluar solo video
video_result = await pipeline.analyze_video(
    submission_id=1,
    requirements="Explicar arquitectura del sistema"
)

# Evaluación completa (código + video)
full_result = await pipeline.evaluate_submission_complete(
    submission_id=1,
    requirements="Proyecto final",
    rubric={...}
)
```

### Detección de Plagio en Batch

```python
# Analizar todas las entregas de una tarea
detections = await pipeline.detect_plagiarism(
    assignment_id=1,
    submission_ids=[1, 2, 3, 4, 5]  # Opcional: solo estas
)

for detection in detections:
    print(f"Plagio detectado:")
    print(f"  Entre: {detection['submission_id_1']} y {detection['submission_id_2']}")
    print(f"  Similitud semántica: {detection['semantic_similarity']}%")
    print(f"  Similitud estructural: {detection['structural_similarity']}%")
```

### Logging

El pipeline registra cada paso en la base de datos:

```sql
SELECT 
    step,
    status,
    message,
    timestamp
FROM simple_logs
WHERE submission_id = 1
ORDER BY timestamp DESC;
```

### Manejo de Errores

El pipeline maneja errores gracefully:

```python
try:
    result = await pipeline.evaluate_submission_complete(...)
    
    if 'error' in result.get('code_evaluation', {}):
        print(f"Error en código: {result['code_evaluation']['error']}")
    
    if 'error' in result.get('video_analysis', {}):
        print(f"Error en video: {result['video_analysis']['error']}")
        
except Exception as e:
    print(f"Error crítico: {e}")
```

### Procesamiento Asíncrono

Todos los métodos del pipeline son asíncronos:

```python
import asyncio

async def process_multiple():
    tasks = [
        pipeline.evaluate_submission_complete(1, reqs, rubric),
        pipeline.evaluate_submission_complete(2, reqs, rubric),
        pipeline.evaluate_submission_complete(3, reqs, rubric),
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# Ejecutar
results = asyncio.run(process_multiple())
```

---

## 🎯 Ejemplo Completo de Integración

Aquí un ejemplo completo de uso end-to-end:

```python
from fastapi import FastAPI, UploadFile
from app.services.evaluation_pipeline import EvaluationPipeline
from app.services.minio_service import minio_service

@app.post("/evaluate-complete")
async def evaluate_complete(
    submission_id: int,
    db: Session = Depends(get_db)
):
    """
    Evaluación completa de una entrega
    """
    # 1. Iniciar pipeline
    pipeline = EvaluationPipeline(db)
    
    # 2. Definir requisitos y rúbrica
    requirements = """
    - Sistema CRUD completo
    - Arquitectura MVC
    - Base de datos PostgreSQL
    - API REST
    - Frontend React
    """
    
    rubric = {
        "comprehension": {
            "max_score": 25,
            "criteria": "Entendimiento de requisitos"
        },
        "design": {
            "max_score": 25,
            "criteria": "Arquitectura y patrones"
        },
        "implementation": {
            "max_score": 25,
            "criteria": "Calidad del código"
        },
        "functionality": {
            "max_score": 25,
            "criteria": "Funcionalidad completa"
        }
    }
    
    # 3. Ejecutar evaluación completa
    result = await pipeline.evaluate_submission_complete(
        submission_id=submission_id,
        requirements=requirements,
        rubric=rubric
    )
    
    # 4. Detectar plagio
    plagiarism = await pipeline.detect_plagiarism(
        assignment_id=result['assignment_id']
    )
    
    # 5. Retornar resultados
    return {
        "submission_id": submission_id,
        "code_evaluation": result['code_evaluation'],
        "video_analysis": result.get('video_analysis'),
        "plagiarism_alerts": plagiarism,
        "status": "completed"
    }
```

---

## 📚 Recursos Adicionales

- **Ollama**: https://github.com/ollama/ollama
- **Llama 3.1**: https://llama.meta.com/
- **CodeBERT**: https://huggingface.co/microsoft/codebert-base
- **Whisper**: https://github.com/openai/whisper
- **FastAPI**: https://fastapi.tiangolo.com/

---

**¿Preguntas?** Consulta el README principal o los logs del sistema.
