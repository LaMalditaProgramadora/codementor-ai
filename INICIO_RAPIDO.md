# ⚡ Inicio Rápido - CodeMentor AI MVP

## 🎯 En 5 minutos tendrás el sistema funcionando

### Paso 1: Prerequisitos (2 min)

✅ Docker Desktop instalado y corriendo  
✅ Al menos 8GB RAM disponible  
✅ 20GB espacio en disco  

### Paso 2: Configurar (30 seg)

```bash
# Descomprimir el proyecto
cd codementor-ai-mvp-completo

# Configurar backend
cd backend
cp .env.example .env
cd ..
```

✅ El `.env` ya está configurado con Llama 3.1 8B (funciona en CPU)

### Paso 3: Iniciar Todo (30 seg)

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver progreso
docker-compose logs -f
```

Espera a ver: "Application startup complete"

### Paso 4: Descargar Modelo IA (2 min)

```bash
# Descargar Llama 3.1 8B (~5GB, solo primera vez)
docker exec -it codementor-ollama ollama pull llama3.1:8b
```

### Paso 5: Inicializar BD (10 seg)

```bash
# Crear tablas
docker exec -it codementor-backend python3 init_db.py
docker exec -it codementor-backend python3 init_data.py
```

Deberías ver: "Database tables created successfully!"

### Paso 6: ¡Usar el Sistema! (1 seg)

Abre tu navegador en:

🌐 **http://localhost:5173**

---

## 🎮 Primera Prueba

### Como Estudiante:

1. Click en **"Soy Estudiante"**
2. Verás el dashboard (aún vacío)
3. Click en **"Nueva Entrega"**
4. Crea un archivo ZIP con algo de código Python:

```bash
mkdir test-project
echo "print('Hello World')" > test-project/main.py
cd test-project && zip -r ../test.zip . && cd ..
```

5. En el formulario:
   - Selecciona "Crear tarea de prueba" (si no hay, créala como docente primero)
   - Código de estudiante: `EST001`
   - Grupo: `1`
   - Sube `test.zip`
   - Click **"Subir Entrega"**

6. Acepta evaluar con IA
7. Espera 1-2 minutos
8. ¡Ve tus resultados! 🎉

### Como Docente:

1. Vuelve a inicio (botón "Cambiar Rol")
2. Click en **"Soy Docente"**
3. Click en **"Nueva Tarea"**
4. Llena el formulario:
   - Título: "Mi Primera Tarea"
   - Descripción: "Proyecto de prueba"
   - Fecha: Una fecha futura
   - Puntaje: 100
   - Sección: SEC001
   - Requisitos: "Desarrollar un programa funcional"
5. Click **"Crear Tarea"**
6. ¡Listo! Ahora los estudiantes pueden subir entregas

---

## ✅ Verificar que Todo Funciona

```bash
# 1. Ver servicios corriendo
docker-compose ps

# Deberías ver 5 servicios "Up":
# - postgres
# - minio
# - ollama
# - backend
# - frontend

# 2. Verificar API
curl http://localhost:8000/health

# Deberías ver: {"status":"healthy"...}

# 3. Verificar Frontend
curl http://localhost:5173

# Deberías ver HTML
```

---

## 🆘 Si Algo Falla

### Servicio no inicia:
```bash
docker-compose restart [servicio]
docker-compose logs [servicio]
```

### Puerto ocupado:
```bash
# Cambiar puertos en docker-compose.yml
# Ejemplo: "8080:8000" en lugar de "8000:8000"
```

### Ollama no descarga:
```bash
# Verificar internet
ping google.com

# Reintentar
docker exec -it codementor-ollama ollama pull llama3.1:8b
```

### Frontend error 404:
```bash
# Esperar a que compile (primera vez toma ~30 seg)
docker-compose logs -f frontend
```

---

## 📊 URLs de Referencia

| Servicio | URL |
|----------|-----|
| **Frontend** | http://localhost:5173 |
| **API Docs** | http://localhost:8000/docs |
| **MinIO Console** | http://localhost:9001 |

---

## 🎯 Comandos Útiles

```bash
# Ver todos los logs
docker-compose logs -f

# Reiniciar todo
docker-compose restart

# Parar todo
docker-compose down

# Ver uso de recursos
docker stats

# Entrar a un contenedor
docker exec -it codementor-backend bash
```

---

## 💡 Tips

1. **Primera carga lenta**: La primera vez que evalúas, Ollama carga el modelo en memoria (30 seg)
2. **Upload grande**: Videos grandes pueden tardar - ten paciencia
3. **Desarrollo**: Los cambios en código se ven automáticamente (hot reload)
4. **Producción**: Recuerda cambiar credenciales antes de desplegar

---

## 🎉 ¡Eso es todo!

Ahora tienes:
- ✅ Backend API funcional
- ✅ Frontend React moderno
- ✅ IA evaluando código (Llama 3.1 8B)
- ✅ Detección de plagio (CodeBERT)
- ✅ Análisis de videos (Whisper)
- ✅ Todo corriendo en Docker

**Tiempo total: ~5 minutos** ⚡

---

¿Problemas? Revisa `README_MVP.md` para documentación completa.
