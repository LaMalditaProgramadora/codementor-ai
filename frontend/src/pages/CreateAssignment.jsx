import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { assignmentsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function CreateAssignment() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    max_score: 100,
    requirements: '',
    section_id: 'SEC001',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const createToast = toast.loading('Creando tarea...');

    try {
      await assignmentsAPI.create({
        ...formData,
        due_date: new Date(formData.due_date).toISOString(),
      });
      toast.success('¡Tarea creada exitosamente!', { id: createToast });
      navigate('/instructor');
    } catch (error) {
      toast.error('Error al crear tarea', { id: createToast });
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/instructor')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver al Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Nueva Tarea</h1>
          <p className="text-sm text-gray-600">Crea una nueva tarea de programación</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Información Básica</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Título de la Tarea *
                </label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Ej: Proyecto Final - Sistema CRUD"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Descripción
                </label>
                <textarea
                  className="input-field"
                  rows="4"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe la tarea..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Fecha de Entrega *
                  </label>
                  <input
                    type="datetime-local"
                    className="input-field"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Puntaje Máximo *
                  </label>
                  <input
                    type="number"
                    className="input-field"
                    value={formData.max_score}
                    onChange={(e) => setFormData({ ...formData, max_score: parseInt(e.target.value) })}
                    min="1"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sección *
                </label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.section_id}
                  onChange={(e) => setFormData({ ...formData, section_id: e.target.value })}
                  placeholder="SEC001"
                  required
                />
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Requisitos del Proyecto</h3>
            <textarea
              className="input-field"
              rows="8"
              value={formData.requirements}
              onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
              placeholder="Especifica los requisitos del proyecto:
              
- Requisito 1
- Requisito 2
- Requisito 3"
            />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">ℹ️ Criterios de Evaluación</h4>
            <p className="text-sm text-blue-800 mb-2">
              El sistema de IA evaluará automáticamente las entregas según estos criterios:
            </p>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• <strong>Comprensión (25%):</strong> Entendimiento de requisitos y problemas</li>
              <li>• <strong>Diseño (25%):</strong> Arquitectura y patrones de diseño</li>
              <li>• <strong>Implementación (25%):</strong> Calidad del código y buenas prácticas</li>
              <li>• <strong>Funcionalidad (25%):</strong> Características funcionando correctamente</li>
            </ul>
          </div>

          <div className="flex space-x-4">
            <button
              type="button"
              onClick={() => navigate('/instructor')}
              className="btn-secondary flex-1"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-primary flex-1 flex items-center justify-center"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Creando...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5 mr-2" />
                  Crear Tarea
                </>
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
