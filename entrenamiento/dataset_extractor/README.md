# Dataset Extractor para CodeMentor AI

Herramienta para extraer código de proyectos C# evaluados y crear un dataset para RAG con pgvector.

## Requisitos

```bash
pip install pandas openpyxl asyncpg sentence-transformers torch
```

## Estructura esperada

```
D:\Tareas\
├── MapeoTareas3.xlsx          # Excel con evaluaciones
├── 1ASI0393-2510-2057\        # Carpeta por sección
│   ├── Semana 2\
│   │   ├── TA2_GRUPO1.zip
│   │   └── Proyecto_Descomprimido\
│   └── Semana 3\
└── 1ASI0393-2520-4546\
    └── ...
```

## Uso

### Paso 1: Extraer dataset

Edita `extraer_dataset.py` y ajusta las rutas:

```python
RUTA_EXCEL = r"D:\Tareas\MapeoTareas3.xlsx"
RUTA_TAREAS = r"D:\Tareas"
RUTA_SALIDA = r"D:\Tareas\dataset.jsonl"
```

Ejecuta:

```bash
python extraer_dataset.py
```

Salida: `dataset.jsonl` con registros como:

```json
{
  "id": "1ASI0393-2520-4209_Semana 2_Tarea2.zip",
  "codigo": "// === Form1.cs ===\nusing System;...",
  "puntaje_total": 17,
  "rubrica": {"comprension": 5, "diseno": 4, "implementacion": 4, "funcionalidad": 4},
  "feedback": "Agregar carpetas para diferenciar las capas..."
}
```

### Paso 2: Cargar en PostgreSQL con pgvector

Edita `cargar_pgvector.py` y ajusta:

```python
RUTA_DATASET = r"D:\Tareas\dataset.jsonl"
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/codementor"
```

Ejecuta:

```bash
python cargar_pgvector.py
```

### Paso 3: Usar en tu API

```python
async def buscar_evaluaciones_similares(codigo_nuevo: str, limit: int = 3):
    embedding = embedder.generar(codigo_nuevo)
    
    return await conn.fetch('''
        SELECT puntaje_total, feedback, codigo,
               1 - (codigo_embedding <=> $1) as similitud
        FROM evaluaciones_historicas
        ORDER BY codigo_embedding <=> $1
        LIMIT $2
    ''', str(embedding), limit)

# Construir prompt con ejemplos
ejemplos = await buscar_evaluaciones_similares(codigo_estudiante)
prompt = f"""
Ejemplos de evaluaciones similares:
{formatear_ejemplos(ejemplos)}

Evalúa este código con el mismo criterio:
{codigo_estudiante}
"""
```

## Notas

- Solo extrae archivos `.cs` (no `.Designer.cs`)
- Ignora carpetas: `bin/`, `obj/`, `.vs/`, `Properties/`
- Los `.rar` no están soportados (descomprimir manualmente)
- El embedding usa CodeBERT (768 dimensiones)

## Autor

Generado para el proyecto de tesis CodeMentor AI - UNMSM
