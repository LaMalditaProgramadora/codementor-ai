"""
Script para crear dataset de evaluaciones de código C#
Combina el Excel de evaluaciones con el código fuente de los proyectos

Uso:
    python extraer_dataset.py

Configuración:
    - RUTA_EXCEL: Ruta al archivo Excel con evaluaciones
    - RUTA_TAREAS: Ruta base donde están las carpetas de tareas
    - RUTA_SALIDA: Donde se guardará el dataset generado
"""

import os
import re
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Intentar importar pandas, si no está disponible dar instrucciones
try:
    import pandas as pd
except ImportError:
    print("❌ Necesitas instalar pandas:")
    print("   pip install pandas openpyxl")
    exit(1)

# ============================================
# CONFIGURACIÓN - AJUSTA ESTAS RUTAS
# ============================================
RUTA_EXCEL = r"D:\Tareas\MapeoTareas3.xlsx"  # Tu archivo Excel
RUTA_TAREAS = r"D:\Tareas"                    # Carpeta raíz de tareas
RUTA_SALIDA = r"D:\Tareas\dataset.jsonl"      # Archivo de salida

# ============================================
# CONFIGURACIÓN DE EXTRACCIÓN
# ============================================
EXTENSIONES_CODIGO = ['.cs']  # Extensiones a extraer
ARCHIVOS_EXCLUIR = ['.Designer.cs', '.designer.cs']  # Sufijos a excluir
CARPETAS_EXCLUIR = ['bin', 'obj', '.vs', 'Properties', 'packages', '.git', 'Debug', 'Release']

# ============================================
# FUNCIONES DE EXTRACCIÓN
# ============================================

def debe_extraer_archivo(ruta_archivo: str) -> bool:
    """Determina si un archivo debe ser extraído"""
    nombre = os.path.basename(ruta_archivo)
    
    # Verificar extensión
    tiene_extension_valida = any(nombre.endswith(ext) for ext in EXTENSIONES_CODIGO)
    if not tiene_extension_valida:
        return False
    
    # Verificar que no sea archivo excluido
    es_excluido = any(nombre.endswith(excl) for excl in ARCHIVOS_EXCLUIR)
    if es_excluido:
        return False
    
    # Verificar que no esté en carpeta excluida
    partes_ruta = ruta_archivo.replace('\\', '/').split('/')
    en_carpeta_excluida = any(carpeta in partes_ruta for carpeta in CARPETAS_EXCLUIR)
    if en_carpeta_excluida:
        return False
    
    return True


def extraer_codigo_de_carpeta(ruta_carpeta: str) -> str:
    """Extrae todo el código C# relevante de una carpeta"""
    archivos_codigo = []
    
    for root, dirs, files in os.walk(ruta_carpeta):
        # Filtrar carpetas excluidas para no recorrerlas
        dirs[:] = [d for d in dirs if d not in CARPETAS_EXCLUIR]
        
        for archivo in files:
            ruta_completa = os.path.join(root, archivo)
            if debe_extraer_archivo(ruta_completa):
                try:
                    with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                        contenido = f.read()
                    
                    # Ruta relativa para el encabezado
                    ruta_relativa = os.path.relpath(ruta_completa, ruta_carpeta)
                    archivos_codigo.append(f"// === {ruta_relativa} ===\n{contenido}")
                except Exception as e:
                    print(f"    ⚠️ Error leyendo {ruta_completa}: {e}")
    
    return "\n\n".join(archivos_codigo)


def extraer_codigo_de_zip(ruta_zip: str) -> str:
    """Extrae código C# de un archivo ZIP"""
    archivos_codigo = []
    
    try:
        with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
            for archivo in zip_ref.namelist():
                if debe_extraer_archivo(archivo):
                    try:
                        with zip_ref.open(archivo) as f:
                            contenido = f.read().decode('utf-8', errors='ignore')
                        archivos_codigo.append(f"// === {archivo} ===\n{contenido}")
                    except Exception as e:
                        print(f"    ⚠️ Error extrayendo {archivo}: {e}")
    except zipfile.BadZipFile:
        print(f"    ❌ Archivo ZIP corrupto: {ruta_zip}")
    except Exception as e:
        print(f"    ❌ Error con ZIP {ruta_zip}: {e}")
    
    return "\n\n".join(archivos_codigo)


def buscar_proyecto(seccion: str, semana: str, nombre_archivo: str) -> Optional[str]:
    """Busca el proyecto en la estructura de carpetas"""
    # Construir ruta esperada
    ruta_semana = os.path.join(RUTA_TAREAS, seccion, semana)
    
    if not os.path.exists(ruta_semana):
        return None
    
    # Buscar el archivo/carpeta
    nombre_base = os.path.splitext(nombre_archivo)[0] if nombre_archivo else ""
    
    # Estrategia 1: Buscar archivo exacto
    for item in os.listdir(ruta_semana):
        ruta_item = os.path.join(ruta_semana, item)
        
        # Coincidencia exacta
        if item == nombre_archivo:
            return ruta_item
        
        # Coincidencia sin extensión (carpeta descomprimida)
        if item == nombre_base:
            return ruta_item
        
        # Coincidencia parcial (por si hay variaciones)
        if nombre_base and nombre_base.lower() in item.lower():
            return ruta_item
    
    return None


def parsear_rubrica(comentario: str) -> dict:
    """Extrae los puntajes de la rúbrica del comentario"""
    rubrica = {
        "comprension": None,
        "diseno": None,
        "implementacion": None,
        "funcionalidad": None
    }
    
    if not comentario or pd.isna(comentario):
        return rubrica
    
    patrones = {
        "comprension": r"Comprensión del problema:\s*(\d+)",
        "diseno": r"Diseño de la solución:\s*(\d+)",
        "implementacion": r"Implementación:\s*(\d+)",
        "funcionalidad": r"Funcionalidad:\s*(\d+)"
    }
    
    for campo, patron in patrones.items():
        match = re.search(patron, comentario, re.IGNORECASE)
        if match:
            rubrica[campo] = int(match.group(1))
    
    return rubrica


def extraer_feedback(comentario: str) -> str:
    """Extrae el feedback sin la rúbrica numérica"""
    if not comentario or pd.isna(comentario):
        return ""
    
    # Remover las líneas de rúbrica
    lineas = comentario.split('\n')
    feedback_lineas = []
    
    patrones_rubrica = [
        r"Comprensión del problema:\s*\d+",
        r"Diseño de la solución:\s*\d+",
        r"Implementación:\s*\d+",
        r"Funcionalidad:\s*\d+"
    ]
    
    for linea in lineas:
        es_rubrica = any(re.search(p, linea, re.IGNORECASE) for p in patrones_rubrica)
        if not es_rubrica and linea.strip():
            feedback_lineas.append(linea.strip())
    
    return '\n'.join(feedback_lineas)


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def main():
    print("=" * 60)
    print("🔧 EXTRACTOR DE DATASET PARA CODEMENTOR AI")
    print("=" * 60)
    print(f"\n📁 Excel: {RUTA_EXCEL}")
    print(f"📁 Tareas: {RUTA_TAREAS}")
    print(f"📁 Salida: {RUTA_SALIDA}\n")
    
    # Verificar que existen las rutas
    if not os.path.exists(RUTA_EXCEL):
        print(f"❌ No se encontró el Excel: {RUTA_EXCEL}")
        return
    
    if not os.path.exists(RUTA_TAREAS):
        print(f"❌ No se encontró la carpeta de tareas: {RUTA_TAREAS}")
        return
    
    # Leer Excel
    print("📖 Leyendo Excel...")
    xlsx = pd.ExcelFile(RUTA_EXCEL)
    
    dataset = []
    stats = {
        "total": 0,
        "encontrados": 0,
        "con_codigo": 0,
        "sin_codigo": 0,
        "no_encontrados": 0
    }
    
    # Procesar cada hoja (excepto Hoja1 que está vacía)
    for hoja in xlsx.sheet_names:
        if hoja == 'Hoja1':
            continue
            
        print(f"\n📋 Procesando hoja: {hoja}")
        df = pd.read_excel(xlsx, sheet_name=hoja)
        
        for idx, row in df.iterrows():
            stats["total"] += 1
            
            seccion = str(row.get('Sección', '')).strip()
            semana = str(row.get('Semana', '')).strip()
            nombre_archivo = str(row.get('NombreArchivo', '')).strip()
            puntaje = row.get('Puntaje', 0)
            comentario = str(row.get('Comentario', ''))
            video = str(row.get('Vídeo', ''))
            
            # Saltar filas sin datos válidos
            if not seccion or not semana or pd.isna(row.get('Sección')):
                continue
            
            print(f"  [{stats['total']}] {seccion}/{semana}/{nombre_archivo[:30]}...", end=" ")
            
            # Buscar el proyecto
            ruta_proyecto = buscar_proyecto(seccion, semana, nombre_archivo)
            
            if not ruta_proyecto:
                print("❌ No encontrado")
                stats["no_encontrados"] += 1
                continue
            
            stats["encontrados"] += 1
            
            # Extraer código
            if os.path.isdir(ruta_proyecto):
                codigo = extraer_codigo_de_carpeta(ruta_proyecto)
            elif ruta_proyecto.endswith('.zip'):
                codigo = extraer_codigo_de_zip(ruta_proyecto)
            elif ruta_proyecto.endswith('.rar'):
                print("⚠️ RAR (no soportado)")
                stats["sin_codigo"] += 1
                continue
            else:
                print("⚠️ Tipo desconocido")
                stats["sin_codigo"] += 1
                continue
            
            if not codigo.strip():
                print("⚠️ Sin código C#")
                stats["sin_codigo"] += 1
                continue
            
            stats["con_codigo"] += 1
            print(f"✅ {len(codigo)} chars")
            
            # Parsear rúbrica y feedback
            rubrica = parsear_rubrica(comentario)
            feedback = extraer_feedback(comentario)
            
            # Crear registro
            registro = {
                "id": f"{seccion}_{semana}_{nombre_archivo}",
                "seccion": seccion,
                "semana": semana,
                "nombre_archivo": nombre_archivo,
                "video_url": video if video and video != 'nan' else None,
                "codigo": codigo,
                "puntaje_total": int(puntaje) if not pd.isna(puntaje) else 0,
                "rubrica": rubrica,
                "feedback": feedback,
                "comentario_completo": comentario if comentario != 'nan' else ""
            }
            
            dataset.append(registro)
    
    # Guardar dataset
    print(f"\n💾 Guardando dataset en {RUTA_SALIDA}...")
    with open(RUTA_SALIDA, 'w', encoding='utf-8') as f:
        for registro in dataset:
            f.write(json.dumps(registro, ensure_ascii=False) + '\n')
    
    # Estadísticas finales
    print("\n" + "=" * 60)
    print("📊 ESTADÍSTICAS")
    print("=" * 60)
    print(f"   Total evaluaciones en Excel: {stats['total']}")
    print(f"   Proyectos encontrados:       {stats['encontrados']}")
    print(f"   Con código extraído:         {stats['con_codigo']} ✅")
    print(f"   Sin código válido:           {stats['sin_codigo']}")
    print(f"   No encontrados:              {stats['no_encontrados']}")
    print(f"\n   Dataset guardado: {RUTA_SALIDA}")
    print(f"   Registros totales: {len(dataset)}")
    
    # Mostrar ejemplo
    if dataset:
        print("\n" + "=" * 60)
        print("📝 EJEMPLO DE REGISTRO")
        print("=" * 60)
        ejemplo = dataset[0].copy()
        ejemplo['codigo'] = ejemplo['codigo'][:500] + "..." if len(ejemplo['codigo']) > 500 else ejemplo['codigo']
        print(json.dumps(ejemplo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
