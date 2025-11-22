from app.db.session import SessionLocal
from app.models.models import Instructor, Section, Student
from sqlalchemy.exc import IntegrityError

def seed_initial_data():
    """Crear datos iniciales para el sistema"""
    db = SessionLocal()
    
    try:
        print("🌱 Iniciando seed de datos iniciales...")
        
        # 1. Crear Instructor por defecto
        try:
            instructor = Instructor(
                name="Profesor Demo",
                email="profesor@codementor.com",
                role="profesor"
            )
            db.add(instructor)
            db.flush()
            instructor_id = instructor.instructor_id
            print(f"✅ Instructor creado: ID {instructor_id}")
        except IntegrityError:
            db.rollback()
            instructor = db.query(Instructor).filter_by(email="profesor@codementor.com").first()
            instructor_id = instructor.instructor_id if instructor else 1
            print(f"ℹ️  Instructor ya existe: ID {instructor_id}")
        
        # 2. Crear Sección por defecto
        try:
            section = Section(
                section_id="SEC001",
                section_code="SEC001",
                semester="2025-1",
                year=2025,
                instructor_id=instructor_id
            )
            db.add(section)
            db.commit()
            print(f"✅ Sección creada: {section.section_id}")
        except IntegrityError:
            db.rollback()
            print(f"ℹ️  Sección ya existe: SEC001")
        
        # 3. Crear Estudiante por defecto
        try:
            student = Student(
                student_id="EST001",
                first_name="Estudiante",
                last_name="Demo",
                email="estudiante@codementor.com",
                section_id="SEC001",
                group_number=1
            )
            db.add(student)
            db.commit()
            print(f"✅ Estudiante creado: {student.student_id}")
        except IntegrityError:
            db.rollback()
            print(f"ℹ️  Estudiante ya existe: EST001")
        
        # 4. Crear sección adicional
        try:
            section2 = Section(
                section_id="1ASI0393-2520-4546",
                section_code="1ASI0393-2520-4546",
                semester="2025-1",
                year=2025,
                instructor_id=instructor_id
            )
            db.add(section2)
            db.commit()
            print(f"✅ Sección creada: {section2.section_id}")
        except IntegrityError:
            db.rollback()
            print(f"ℹ️  Sección ya existe: 1ASI0393-2520-4546")
        
        # 5. Crear estudiante adicional
        try:
            student2 = Student(
                student_id="U201514642",
                first_name="Jimena",
                last_name="Ruiz",
                email="u201514642@codementor.com",
                section_id="SEC001",
                group_number=1
            )
            db.add(student2)
            db.commit()
            print(f"✅ Estudiante creado: {student2.student_id}")
        except IntegrityError:
            db.rollback()
            print(f"ℹ️  Estudiante ya existe: U201514642")
        
        print("✅ Seed de datos completado!")
        
    except Exception as e:
        print(f"❌ Error durante seed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_initial_data()