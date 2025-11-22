# 🚀 CodeMentor AI - MVP Completo

Sistema de Tutoría Inteligente completo con Frontend y Backend, configurado para usar **Llama 3.1 8B**.

## ✨ Características del MVP

### ✅ Backend (Completo)
- FastAPI con SQLAlchemy
- 10 modelos de base de datos
- Pipeline de evaluación con IA
- Integración con Ollama (Llama 3.1 8B)
- CodeBERT para detección de plagio
- Whisper para transcripción de videos
- MinIO para almacenamiento de archivos

### ✅ Frontend (Completo)
- React 18 + Vite
- Tailwind CSS
- Portal para Estudiantes
- Portal para Docentes
- Dashboard interactivo
- Upload de archivos drag & drop
- Visualización de resultados en tiempo real

## 🎯 Funcionalidades Implementadas

### Para Estudiantes:
- ✅ Ver tareas disponibles
- ✅ Subir proyectos (código ZIP + video)
- ✅ Evaluar con IA automáticamente
- ✅ Ver resultados detallados por criterio
- ✅ Ver feedback personalizado de IA
- ✅ Dashboard con estadísticas

### Para Docentes:
- ✅ Crear nuevas tareas
- ✅ Ver todas las entregas
- ✅ Revisar evaluaciones de IA
- ✅ Detectar plagio automáticamente
- ✅ Dashboard con estadísticas
- ✅ Gestión de múltiples secciones

## 🚀 Inicio Rápido

### 1. Configurar Backend

```bash
cd backend
cp .env.example .env
# El archivo ya está configurado con llama3.1:8b
```

### 2. Iniciar Servicios

```bash
# Desde la raíz del proyecto
docker-compose up -d
```

Esto iniciará:
- PostgreSQL (puerto 5432)
- MinIO (puertos 9000, 9001)
- Ollama (puerto 11434)
- Backend FastAPI (puerto 8000)
- Frontend React (puerto 5173)

### 3. Descargar Modelo de Ollama

```bash
# Descargar Llama 3.1 8B (primera vez, ~5GB)
docker exec -it codementor-ollama ollama pull llama3.1:8b
```

### 4. Inicializar Base de Datos

```bash
docker exec -it codementor-backend python3 init_db.py
```

### 5. Acceder a la Aplicación

Abre tu navegador en: **http://localhost:5173**

## 🌐 URLs de Acceso

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Frontend** | http://localhost:5173 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin123 |

## 📱 Uso del Sistema

### Flujo Estudiante:

1. **Seleccionar Rol**: En la página inicial, click en "Soy Estudiante"
2. **Ver Tareas**: Verás todas las tareas disponibles
3. **Subir Entrega**:
   - Click en "Nueva Entrega"
   - Selecciona la tarea
   - Sube tu código (.zip)
   - Opcionalmente sube video
   - Click en "Subir Entrega"
4. **Evaluar**: Acepta evaluar con IA (toma 2-3 min)
5. **Ver Resultados**: Ve tu puntaje y feedback detallado

### Flujo Docente:

1. **Seleccionar Rol**: En la página inicial, click en "Soy Docente"
2. **Crear Tarea**:
   - Click en "Nueva Tarea"
   - Llena el formulario
   - Define requisitos
   - Click en "Crear Tarea"
3. **Ver Entregas**: Click en "Ver Entregas" en cualquier tarea
4. **Detectar Plagio**: Click en "Detectar Plagio" para analizar similitudes
5. **Revisar**: Revisa las evaluaciones automáticas de IA

## 🎨 Capturas de Pantalla

### Página de Inicio
![Home](docs/home.png)

### Dashboard Estudiante
![Student Dashboard](docs/student-dashboard.png)

### Resultados de Evaluación
![Results](docs/results.png)

### Dashboard Docente
![Instructor Dashboard](docs/instructor-dashboard.png)

## 🔧 Tecnologías Usadas

### Frontend:
- **React 18**: UI Library
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Zustand**: State management
- **React Router**: Navigation
- **Axios**: HTTP client
- **React Hot Toast**: Notifications
- **Lucide React**: Icons

### Backend:
- **FastAPI**: Web framework
- **SQLAlchemy**: ORM
- **PostgreSQL**: Database
- **MinIO**: Object storage
- **Ollama**: LLM runtime (Llama 3.1 8B)
- **CodeBERT**: Code embeddings
- **Whisper**: Speech-to-text

## 📊 Estructura del Proyecto

```
codementor-ai-mvp-completo/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.jsx
│   │   │   ├── StudentDashboard.jsx
│   │   │   ├── SubmitAssignment.jsx
│   │   │   ├── SubmissionResults.jsx
│   │   │   ├── InstructorDashboard.jsx
│   │   │   └── CreateAssignment.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── store/
│   │   │   └── index.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── api/
│   │   ├── core/
│   │   └── db/
│   ├── main.py
│   ├── init_db.py
│   ├── requirements.txt
│   └── Dockerfile
│
└── docker-compose.yml
```

## 🧪 Probar el Sistema

### Caso de Prueba 1: Flujo Completo Estudiante

```bash
# 1. Crear tarea de prueba (como docente)
curl -X POST http://localhost:8000/api/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tarea de Prueba",
    "description": "Proyecto de prueba del sistema",
    "due_date": "2025-12-31T23:59:59",
    "max_score": 100,
    "section_id": "SEC001",
    "requirements": "Desarrollar un programa funcional"
  }'

# 2. Ir a http://localhost:5173
# 3. Seleccionar "Soy Estudiante"
# 4. Click en "Nueva Entrega"
# 5. Subir un archivo .zip con código
# 6. Evaluar y ver resultados
```

### Caso de Prueba 2: Detección de Plagio

```bash
# 1. Subir 2+ entregas para la misma tarea
# 2. Como docente, click en "Detectar Plagio"
# 3. Ver resultados de similitud
```

## 📝 Datos de Prueba

El sistema ya incluye IDs por defecto para testing:

- **Section ID**: SEC001
- **Student ID**: EST001
- **Group Number**: 1

Puedes cambiarlos en los formularios según necesites.

## 🎯 Criterios de Evaluación

El sistema evalúa automáticamente según 4 criterios:

1. **Comprensión (25%)**: Entendimiento de requisitos
2. **Diseño (25%)**: Arquitectura y patrones
3. **Implementación (25%)**: Calidad del código
4. **Funcionalidad (25%)**: Features funcionando

## 🔍 Detección de Plagio

El sistema usa CodeBERT para detectar:
- **Similitud Semántica**: Comparación de embeddings
- **Similitud Estructural**: Comparación de tokens
- **Umbral**: 85% por defecto (configurable)

## ⚡ Performance

### Tiempos Esperados:

- **Upload de código (10MB)**: 2-5 seg
- **Upload de video (100MB)**: 10-30 seg
- **Evaluación con IA**: 30-90 seg
- **Detección de plagio**: 5-10 seg/par
- **Transcripción video (5 min)**: ~30 seg

## 🐛 Troubleshooting

### Frontend no carga
```bash
# Verificar que el contenedor está corriendo
docker-compose ps frontend

# Ver logs
docker-compose logs -f frontend

# Reiniciar
docker-compose restart frontend
```

### Error de CORS
```bash
# Verificar que CORS_ORIGINS en backend/.env incluye:
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### Ollama no responde
```bash
# Verificar modelo descargado
docker exec codementor-ollama ollama list

# Si no está, descargar
docker exec codementor-ollama ollama pull llama3.1:8b
```

### Base de datos vacía
```bash
# Reinicializar
docker exec -it codementor-backend python3 init_db.py
```

## 🔒 Seguridad (Producción)

Para usar en producción, cambiar:

1. **Backend .env**:
   - Cambiar credenciales de PostgreSQL
   - Cambiar credenciales de MinIO
   - `DEBUG=False`
   - Actualizar `CORS_ORIGINS` con dominios reales

2. **Frontend .env**:
   - `VITE_API_URL=https://tu-dominio.com`

3. **Habilitar HTTPS** en todos los servicios

## 📚 Documentación Adicional

- **API Docs**: http://localhost:8000/docs
- **README Backend**: /backend/README.md
- **README Frontend**: /frontend/README.md

## 🎓 Créditos

**Proyecto de Tesis**: Automatización de la Revisión de Tareas de Programación con un Sistema de Tutoría Inteligente

**Universidad**: Universidad Nacional Mayor de San Marcos  
**Facultad**: Ingeniería de Sistemas e Informática  
**Autor**: Ruiz Cerna, Jimena Alexandra  
**Año**: 2025

## 🚀 Próximos Pasos

Este es un MVP funcional. Para producción considera:

- [ ] Autenticación y autorización (JWT)
- [ ] Gestión de usuarios completa
- [ ] Exportar reportes (PDF, Excel)
- [ ] Notificaciones por email
- [ ] Tests automatizados
- [ ] CI/CD pipeline
- [ ] Backup automático
- [ ] Monitoreo y logging
- [ ] Escalabilidad horizontal

## 📄 Licencia

Este proyecto es parte de una tesis académica.

---

**¡El MVP está completo y listo para usar!** 🎉

Para comenzar: `docker-compose up -d` y abre http://localhost:5173
