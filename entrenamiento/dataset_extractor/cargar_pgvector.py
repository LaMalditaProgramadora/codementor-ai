"""
Script para cargar el dataset de evaluaciones en PostgreSQL con pgvector
Genera embeddings del código para búsqueda semántica (RAG)

Uso:
    python cargar_pgvector.py

Requisitos:
    pip install asyncpg sentence-transformers torch
"""

import os
import json
import asyncio
from datetime import datetime

# Configuración
RUTA_DATASET = r"D:\Tareas\dataset.jsonl"
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/codementor"

# Modelo para embeddings (CodeBERT o alternativa más ligera)
MODELO_EMBEDDINGS = "microsoft/codebert-base"  # o "sentence-transformers/all-MiniLM-L6-v2" si hay problemas de memoria

# ============================================
# SQL PARA CREAR TABLA
# ============================================
SQL_CREAR_TABLA = """
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS evaluaciones_historicas;

CREATE TABLE evaluaciones_historicas (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(500) UNIQUE,
    seccion VARCHAR(100),
    semana VARCHAR(50),
    nombre_archivo VARCHAR(255),
    video_url TEXT,
    codigo TEXT,
    codigo_embedding vector(768),  -- Dimensión de CodeBERT
    puntaje_total INTEGER,
    rubrica_comprension INTEGER,
    rubrica_diseno INTEGER,
    rubrica_implementacion INTEGER,
    rubrica_funcionalidad INTEGER,
    feedback TEXT,
    comentario_completo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsqueda por similitud
CREATE INDEX idx_codigo_embedding ON evaluaciones_historicas 
USING ivfflat (codigo_embedding vector_cosine_ops) WITH (lists = 100);

-- Índices adicionales
CREATE INDEX idx_seccion ON evaluaciones_historicas(seccion);
CREATE INDEX idx_semana ON evaluaciones_historicas(semana);
CREATE INDEX idx_puntaje ON evaluaciones_historicas(puntaje_total);
"""

SQL_INSERTAR = """
INSERT INTO evaluaciones_historicas (
    external_id, seccion, semana, nombre_archivo, video_url,
    codigo, codigo_embedding, puntaje_total,
    rubrica_comprension, rubrica_diseno, rubrica_implementacion, rubrica_funcionalidad,
    feedback, comentario_completo
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
ON CONFLICT (external_id) DO UPDATE SET
    codigo = EXCLUDED.codigo,
    codigo_embedding = EXCLUDED.codigo_embedding,
    puntaje_total = EXCLUDED.puntaje_total
"""

SQL_BUSCAR_SIMILARES = """
SELECT 
    id, seccion, semana, nombre_archivo, puntaje_total,
    rubrica_comprension, rubrica_diseno, rubrica_implementacion, rubrica_funcionalidad,
    feedback, codigo,
    1 - (codigo_embedding <=> $1) as similitud
FROM evaluaciones_historicas
ORDER BY codigo_embedding <=> $1
LIMIT $2
"""


class EmbeddingGenerator:
    """Genera embeddings de código usando CodeBERT o modelo alternativo"""
    
    def __init__(self, modelo: str = MODELO_EMBEDDINGS):
        print(f"🔄 Cargando modelo de embeddings: {modelo}")
        
        try:
            from sentence_transformers import SentenceTransformer
            self.modelo = SentenceTransformer(modelo)
            self.dimension = self.modelo.get_sentence_embedding_dimension()
            print(f"✅ Modelo cargado. Dimensión: {self.dimension}")
        except Exception as e:
            print(f"⚠️ Error cargando {modelo}, intentando modelo alternativo...")
            from sentence_transformers import SentenceTransformer
            self.modelo = SentenceTransformer("all-MiniLM-L6-v2")
            self.dimension = 384
            print(f"✅ Modelo alternativo cargado. Dimensión: {self.dimension}")
    
    def generar(self, codigo: str) -> list:
        """Genera embedding para un fragmento de código"""
        # Truncar si es muy largo (límite típico ~512 tokens)
        codigo_truncado = codigo[:8000] if len(codigo) > 8000 else codigo
        embedding = self.modelo.encode(codigo_truncado)
        return embedding.tolist()


async def main():
    print("=" * 60)
    print("🔧 CARGADOR DE DATASET A POSTGRESQL + PGVECTOR")
    print("=" * 60)
    
    # Verificar archivo
    if not os.path.exists(RUTA_DATASET):
        print(f"❌ No se encontró el dataset: {RUTA_DATASET}")
        print("   Primero ejecuta: python extraer_dataset.py")
        return
    
    # Cargar modelo de embeddings
    embedder = EmbeddingGenerator()
    
    # Conectar a PostgreSQL
    print(f"\n🔌 Conectando a PostgreSQL...")
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Conectado")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\n   Asegúrate de que PostgreSQL esté corriendo y la URL sea correcta")
        return
    
    # Crear tabla
    print("\n📋 Creando tabla evaluaciones_historicas...")
    try:
        await conn.execute(SQL_CREAR_TABLA)
        print("✅ Tabla creada")
    except Exception as e:
        print(f"⚠️ Nota: {e}")
    
    # Cargar dataset
    print(f"\n📖 Leyendo dataset: {RUTA_DATASET}")
    registros = []
    with open(RUTA_DATASET, 'r', encoding='utf-8') as f:
        for linea in f:
            if linea.strip():
                registros.append(json.loads(linea))
    
    print(f"   {len(registros)} registros encontrados")
    
    # Procesar e insertar
    print("\n🚀 Generando embeddings e insertando...")
    insertados = 0
    errores = 0
    
    for i, reg in enumerate(registros):
        try:
            # Generar embedding
            embedding = embedder.generar(reg['codigo'])
            
            # Ajustar dimensión si es necesario
            if len(embedding) != 768:
                # Padding o truncado para coincidir con la dimensión de la tabla
                if len(embedding) < 768:
                    embedding = embedding + [0.0] * (768 - len(embedding))
                else:
                    embedding = embedding[:768]
            
            # Insertar
            rubrica = reg.get('rubrica', {})
            await conn.execute(
                SQL_INSERTAR,
                reg['id'],
                reg['seccion'],
                reg['semana'],
                reg['nombre_archivo'],
                reg.get('video_url'),
                reg['codigo'],
                str(embedding),  # pgvector acepta string de lista
                reg['puntaje_total'],
                rubrica.get('comprension'),
                rubrica.get('diseno'),
                rubrica.get('implementacion'),
                rubrica.get('funcionalidad'),
                reg.get('feedback', ''),
                reg.get('comentario_completo', '')
            )
            
            insertados += 1
            print(f"\r   Progreso: {insertados}/{len(registros)}", end="")
            
        except Exception as e:
            errores += 1
            print(f"\n   ❌ Error en registro {reg['id']}: {e}")
    
    print(f"\n\n✅ Completado: {insertados} insertados, {errores} errores")
    
    # Cerrar conexión
    await conn.close()
    
    # Mostrar ejemplo de uso
    print("\n" + "=" * 60)
    print("📝 EJEMPLO DE USO EN TU CÓDIGO")
    print("=" * 60)
    print("""
# Para buscar proyectos similares:

async def buscar_evaluaciones_similares(codigo_nuevo: str, limit: int = 3):
    embedding = embedder.generar(codigo_nuevo)
    
    resultados = await conn.fetch('''
        SELECT seccion, semana, puntaje_total, feedback, codigo,
               1 - (codigo_embedding <=> $1) as similitud
        FROM evaluaciones_historicas
        ORDER BY codigo_embedding <=> $1
        LIMIT $2
    ''', str(embedding), limit)
    
    return resultados

# Luego construir prompt con ejemplos:

ejemplos = await buscar_evaluaciones_similares(codigo_estudiante)
prompt = f'''
Rúbrica: Comprensión (5pts), Diseño (5pts), Implementación (5pts), Funcionalidad (5pts)

Ejemplos de evaluaciones anteriores similares:
{formatear_ejemplos(ejemplos)}

Evalúa este nuevo código siguiendo el mismo criterio:
```csharp
{codigo_estudiante}
```
'''
""")


if __name__ == "__main__":
    asyncio.run(main())
