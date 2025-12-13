# CodeMentor AI - Sistema de Tutoría Inteligente

Sistema de evaluación automatizada de tareas de programación usando LLMs (Llama 3.1 70B), CodeBERT y Whisper.

## 📋 Descripción del Proyecto

CodeMentor AI es un Sistema de Tutoría Inteligente (ITS) diseñado para automatizar la revisión de proyectos de programación en cursos universitarios de Ingeniería Informática. El sistema utiliza tecnologías de IA de vanguardia para proporcionar retroalimentación detallada y personalizada a los estudiantes.

### Características Principales

✅ **Evaluación Automática de Código**: Análisis profundo usando Llama 3.1 70B
✅ **Detección de Plagio**: Similitud semántica y estructural con CodeBERT
✅ **Análisis de Videos**: Transcripción y análisis de presentaciones con Whisper
✅ **Feedback Personalizado**: Comentarios constructivos por criterio de evaluación
✅ **Portal Docente**: Gestión de tareas, secciones y calificaciones
✅ **Portal Estudiante**: Envío de proyectos y visualización de feedback

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico

**Frontend:**
- React 18
- Tailwind CSS
- Vite

**Backend:**
- FastAPI
- SQLAlchemy
- Pydantic

**Base de Datos:**
- PostgreSQL 15 con pgvector

**Almacenamiento:**
- MinIO (S3-compatible)

**Servicios de IA:**
- **Ollama**: Llama 3.1 70B para evaluación de código
- **CodeBERT**: microsoft/codebert-base para detección de plagio
- **Whisper**: OpenAI Whisper para transcripción de audio/video

**DevOps:**
- Docker & Docker Compose

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────┐
│         CAPA DE PRESENTACIÓN            │
│  ┌──────────────┐  ┌──────────────┐    │
│  │   Portal     │  │   Portal     │    │
│  │  Estudiante  │  │   Docente    │    │
│  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────┘
           │ HTTPS         │ HTTPS
           └───────────┬───────────┘
┌─────────────────────────────────────────┐
│          CAPA DE LÓGICA                 │
│         ┌──────────────┐                │
│         │   FastAPI    │                │
│         │   Backend    │                │
│         └──────────────┘                │
└─────────────────────────────────────────┘
           │              │
    ┌──────┴──────┐   ┌──┴──────────────┐
┌───────────────────┐ ┌──────────────────┐
│  ALMACENAMIENTO   │ │  SERVICIOS IA    │
│ ┌──────┐ ┌──────┐│ │ ┌──────────────┐ │
│ │Postgr││MinIO ││ │ │Ollama(Llama) │ │
│ │eSQL  ││      ││ │ │CodeBERT      │ │
│ └──────┘ └──────┘│ │ │Whisper       │ │
└───────────────────┘ │ └──────────────┘ │
                      └──────────────────┘
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- **Docker Desktop** 20.10+
- **Docker Compose** 2.0+
- **Git**
- **GPU NVIDIA** (recomendado para Ollama con modelo 70B)
  - Driver NVIDIA actualizado
  - NVIDIA Container Toolkit
- **Mínimo 32GB RAM** (recomendado 64GB para Llama 3.1 70B)
- **Mínimo 100GB espacio en disco**

### Paso 1: Clonar el Repositorio

```bash
git clone <repository-url>
cd codementor-ai
```

### Paso 2: Configurar Variables de Entorno

```bash
# En el directorio backend
cd backend
cp .env.example .env

# Editar .env si es necesario
nano .env
```

### Paso 3: Configurar NVIDIA Container Toolkit (Para GPU)

Si tienes GPU NVIDIA y quieres usar Llama 3.1 70B:

```bash
# Instalar NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Paso 4: Iniciar Servicios con Docker Compose

```bash
# Desde el directorio raíz del proyecto
docker-compose up -d
```

Esto iniciará todos los servicios:
- PostgreSQL (puerto 5432)
- MinIO (puertos 9000, 9001)
- Ollama (puerto 11434)
- Backend FastAPI (puerto 8000)
- Frontend React (puerto 5173)

### Paso 5: Verificar que los Servicios Estén Corriendo

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f ollama

# Ver estado de los contenedores
docker-compose ps
```

## 🤖 Configuración de los Servicios de IA

### 1. Configurar Ollama con Llama 3.1 70B

Ollama debe descargar el modelo Llama 3.1 70B la primera vez. Este proceso puede tomar tiempo dependiendo de tu conexión.

#### Opción A: Descarga Automática (Recomendado)

```bash
# Conectarse al contenedor de Ollama
docker exec -it codementor-ollama bash

# Descargar el modelo Llama 3.1 70B
ollama pull llama3.1:70b

# Verificar que el modelo está disponible
ollama list

# Salir del contenedor
exit
```

#### Opción B: Usar un Modelo Más Pequeño (Para Testing o Recursos Limitados)

Si no tienes GPU o suficiente RAM, puedes usar un modelo más pequeño:

```bash
# En el contenedor de Ollama
docker exec -it codementor-ollama ollama pull llama3.1:8b

# Actualizar .env para usar el modelo más pequeño
# OLLAMA_MODEL=llama3.1:8b
```

#### Verificar que Ollama Funciona

```bash
# Probar el modelo
docker exec -it codementor-ollama ollama run llama3.1:70b "Hola, ¿cómo estás?"
```

### 2. Configurar CodeBERT

CodeBERT se descarga automáticamente la primera vez que se usa. No requiere configuración adicional.

**Verificación:**

```bash
# Conectarse al contenedor del backend
docker exec -it codementor-backend bash

# Ejecutar Python y probar CodeBERT
python3 -c "
from app.services.codebert_service import codebert_service
codebert_service.initialize()
print('CodeBERT inicializado correctamente')
"

exit
```

### 3. Configurar Whisper

Whisper también se descarga automáticamente. Puedes elegir entre diferentes tamaños de modelo:

- `tiny`: Más rápido, menos preciso
- `base`: Balance (predeterminado)
- `small`: Más preciso
- `medium`: Muy preciso
- `large`: Máxima precisión (requiere más recursos)

**Cambiar el modelo de Whisper:**

Edita `.env`:
```
WHISPER_MODEL=small  # o tiny, base, medium, large
```

**Verificación:**

```bash
# En el contenedor del backend
docker exec -it codementor-backend python3 -c "
from app.services.whisper_service import whisper_service
whisper_service.initialize()
print('Whisper inicializado correctamente')
"
```

## 📊 Inicializar la Base de Datos

```bash
# Crear las tablas en PostgreSQL
docker exec -it codementor-backend python3 init_db.py

# Verificar que las tablas se crearon
docker exec -it codementor-postgres psql -U codementor_user -d codementor -c "\dt"
```

## 🌐 Acceder a las Interfaces

Una vez que todos los servicios estén corriendo:

- **Frontend (Portal Estudiante/Docente)**: http://localhost:5173
- **Backend API (Swagger Docs)**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001
  - Usuario: `minioadmin`
  - Contraseña: `minioadmin123`
- **Ollama API**: http://ollama:11434

## 📝 Uso del Sistema

### Para Docentes

1. **Crear una Sección**
```bash
curl -X POST "http://localhost:8000/api/sections" \
  -H "Content-Type: application/json" \
  -d '{
    "section_id": "SEC001",
    "section_code": "CS101-A",
    "semester": "2025-1",
    "year": 2025,
    "instructor_id": 1
  }'
```

2. **Crear una Tarea**
```bash
curl -X POST "http://localhost:8000/api/assignments" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Proyecto Final - Sistema de Gestión",
    "description": "Desarrollar un sistema CRUD completo",
    "due_date": "2025-12-20T23:59:59",
    "max_score": 100,
    "requirements": "Debe incluir: frontend, backend, BD",
    "section_id": "SEC001"
  }'
```

### Para Estudiantes

1. **Enviar una Tarea**
```bash
curl -X POST "http://localhost:8000/api/submissions" \
  -F "assignment_id=1" \
  -F "section_id=SEC001" \
  -F "group_number=1" \
  -F "submitted_by=20190001" \
  -F "project_file=@proyecto.zip" \
  -F "video_file=@presentacion.mp4"
```

2. **Evaluar una Tarea**
```bash
curl -X POST "http://localhost:8000/api/submissions/1/evaluate"
```

### Ver Resultados

```bash
# Ver calificación
curl "http://localhost:8000/api/grades?submission_id=1"

# Ver feedback
curl "http://localhost:8000/api/submissions/1"
```

## 🔍 Detección de Plagio

Para analizar plagio en todas las entregas de una tarea:

```bash
curl -X POST "http://localhost:8000/api/plagiarism/detect?assignment_id=1"
```

## 🧪 Testing

```bash
# Ejecutar tests
docker exec -it codementor-backend pytest

# Con coverage
docker exec -it codementor-backend pytest --cov=app tests/
```

## 📈 Monitoreo y Logs

### Ver Logs en Tiempo Real

```bash
# Todos los servicios
docker-compose logs -f

# Solo el backend
docker-compose logs -f backend

# Solo Ollama
docker-compose logs -f ollama
```

### Ver Logs en la Base de Datos

```bash
# Conectarse a PostgreSQL
docker exec -it codementor-postgres psql -U codementor_user -d codementor

# Ver logs de evaluación
SELECT * FROM simple_logs ORDER BY timestamp DESC LIMIT 10;
```

## 🛠️ Troubleshooting

### Problema: Ollama no puede descargar el modelo

**Solución:**
```bash
# Verificar conexión a internet en el contenedor
docker exec -it codementor-ollama ping -c 4 google.com

# Intentar descargar manualmente
docker exec -it codementor-ollama ollama pull llama3.1:70b
```

### Problema: Out of Memory con Llama 3.1 70B

**Solución:**
```bash
# Usar un modelo más pequeño
docker exec -it codementor-ollama ollama pull llama3.1:8b

# Actualizar .env
OLLAMA_MODEL=llama3.1:8b

# Reiniciar backend
docker-compose restart backend
```

### Problema: CodeBERT no se descarga

**Solución:**
```bash
# Entrar al contenedor
docker exec -it codementor-backend bash

# Descargar manualmente
python3 -c "
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('microsoft/codebert-base')
model = AutoModel.from_pretrained('microsoft/codebert-base')
print('CodeBERT descargado correctamente')
"
```

### Problema: Error de conexión con MinIO

**Solución:**
```bash
# Verificar que MinIO está corriendo
docker-compose ps minio

# Reiniciar MinIO
docker-compose restart minio

# Verificar logs
docker-compose logs minio
```

## 📦 Estructura del Proyecto

```
codementor-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   │       ├── submissions.py
│   │   │       ├── assignments.py
│   │   │       ├── grades.py
│   │   │       └── plagiarism.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── db/
│   │   │   └── session.py
│   │   ├── models/
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   └── schemas.py
│   │   └── services/
│   │       ├── ollama_service.py
│   │       ├── codebert_service.py
│   │       ├── whisper_service.py
│   │       ├── minio_service.py
│   │       └── evaluation_pipeline.py
│   ├── main.py
│   ├── init_db.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔒 Consideraciones de Seguridad

- Cambiar credenciales por defecto en producción
- Usar HTTPS en producción
- Implementar autenticación y autorización
- Configurar firewall para limitar acceso a puertos
- Mantener servicios actualizados

## 📚 Referencias y Documentación

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)

## 👥 Créditos

Desarrollado como parte del proyecto de tesis:
"Automatización de la Revisión de Tareas de Programación con un Sistema de Tutoría Inteligente"

Universidad Nacional Mayor de San Marcos
Facultad de Ingeniería de Sistemas e Informática

## 📄 Licencia

Este proyecto es parte de una tesis académica.

---

**Nota**: Este README cubre la implementación hasta la Semana 4 del cronograma, que incluye:
- ✅ Semana 1: Infraestructura (Docker, PostgreSQL, MinIO, Modelos)
- ✅ Semana 2: Backend API (FastAPI, endpoints, MinIO integration)
- ✅ Semana 3: IA - Código (Ollama, CodeBERT, pipeline)
- ✅ Semana 4: IA - Video (Whisper, análisis, pipeline completo)
