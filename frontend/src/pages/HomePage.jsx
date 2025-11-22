import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store';
import { GraduationCap, UserCircle, BookOpen } from 'lucide-react';

export default function HomePage() {
  const navigate = useNavigate();
  const setRole = useAuthStore((state) => state.setRole);

  const handleRoleSelect = (role) => {
    setRole(role);
    navigate(role === 'student' ? '/student' : '/instructor');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <BookOpen className="w-16 h-16 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            CodeMentor AI
          </h1>
          <p className="text-xl text-gray-600">
            Sistema de Tutoría Inteligente para Evaluación de Código
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Powered by Llama 3.1 8B • CodeBERT • Whisper
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Estudiante */}
          <button
            onClick={() => handleRoleSelect('student')}
            className="card hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 cursor-pointer group"
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mb-4 group-hover:bg-primary-200 transition-colors">
                <GraduationCap className="w-10 h-10 text-primary-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Soy Estudiante
              </h2>
              <p className="text-gray-600 mb-4">
                Sube tus proyectos y recibe retroalimentación instantánea con IA
              </p>
              <ul className="text-sm text-gray-500 space-y-2 text-left">
                <li>✓ Subir código y videos</li>
                <li>✓ Evaluación automática con IA</li>
                <li>✓ Feedback detallado por criterio</li>
                <li>✓ Ver calificaciones en tiempo real</li>
              </ul>
            </div>
          </button>

          {/* Docente */}
          <button
            onClick={() => handleRoleSelect('instructor')}
            className="card hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 cursor-pointer group"
          >
            <div className="flex flex-col items-center text-center">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-4 group-hover:bg-green-200 transition-colors">
                <UserCircle className="w-10 h-10 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Soy Docente
              </h2>
              <p className="text-gray-600 mb-4">
                Gestiona tareas, revisa entregas y supervisa evaluaciones de IA
              </p>
              <ul className="text-sm text-gray-500 space-y-2 text-left">
                <li>✓ Crear y gestionar tareas</li>
                <li>✓ Revisar evaluaciones de IA</li>
                <li>✓ Detectar plagio automático</li>
                <li>✓ Publicar calificaciones finales</li>
              </ul>
            </div>
          </button>
        </div>

        <div className="mt-12 text-center">
          <div className="card inline-block">
            <p className="text-sm text-gray-600">
              <span className="font-semibold">Demo MVP</span> - Sistema configurado con Llama 3.1 8B
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Universidad Nacional Mayor de San Marcos • Tesis de Maestría 2025
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
