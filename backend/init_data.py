from app.db.session import engine, Base
from app.models.models import *

def reset_database():
    """Borrar y recrear todas las tablas"""
    print("🗑️  Borrando todas las tablas...")
    Base.metadata.drop_all(bind=engine)
    
    print("📦 Recreando tablas...")
    Base.metadata.create_all(bind=engine)
    
    print("🌱 Insertando datos iniciales...")
    from seed_data import seed_initial_data
    seed_initial_data()
    
    print("✅ Base de datos reiniciada exitosamente!")

if __name__ == "__main__":
    reset_database()