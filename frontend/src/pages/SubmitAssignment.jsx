import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Upload, FileText, Video, ArrowLeft, Loader2 } from 'lucide-react';
import { submissionsAPI, assignmentsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function SubmitAssignment() {
  const navigate = useNavigate();
  const location = useLocation();
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    assignment_id: location.state?.assignment?.assignment_id || '',
    section_id: 'SEC001', // Default
    group_number: 1,
    submitted_by: 'EST001', // Default
    project_file: null,
    video_file: null,
  });

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      const res = await assignmentsAPI.getAll();
      setAssignments(res.data);
    } catch (error) {
      toast.error('Error al cargar tareas');
    }
  };

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (file) {
      setFormData({ ...formData, [type]: file });
      toast.success(`Archivo ${type === 'project_file' ? 'de código' : 'de video'} seleccionado`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.assignment_id) {
      toast.error('Selecciona una tarea');
      return;
    }

    if (!formData.project_file) {
      toast.error('Debes subir el archivo de código (.zip)');
      return;
    }

    setLoading(true);
    const submitToast = toast.loading('Subiendo entrega...');

    try {
      const data = new FormData();
      data.append('assignment_id', formData.assignment_id);
      data.append('section_id', formData.section_id);
      data.append('group_number', formData.group_number);
      data.append('submitted_by', formData.submitted_by);
      data.append('project_file', formData.project_file);

      // ✅ Solo enviar video_url si existe
      if (formData.video_url) {
        data.append('video_url', formData.video_url);
      }

      const response = await submissionsAPI.create(data);

      toast.success('¡Entrega realizada con éxito!', { id: submitToast });

      const shouldEvaluate = window.confirm(
        '¿Deseas evaluar tu entrega con IA ahora? (Puede tomar 2-5 minutos)'
      );

      if (shouldEvaluate) {
        toast.loading('Evaluando con IA en segundo plano...', { id: submitToast });
        await submissionsAPI.evaluate(response.data.submission_id);
        toast.success('Evaluación iniciada. Recibirás los resultados pronto.', { id: submitToast });
        navigate('/student');
      } else {
        navigate('/student');
      }
    } catch (error) {
      toast.error('Error al subir entrega', { id: submitToast });
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/student')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver al Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Nueva Entrega</h1>
          <p className="text-sm text-gray-600">Sube tu proyecto y video de presentación</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Seleccionar tarea */}
          <div className="card">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Seleccionar Tarea *
            </label>
            <select
              className="input-field"
              value={formData.assignment_id}
              onChange={(e) => setFormData({ ...formData, assignment_id: e.target.value })}
              required
            >
              <option value="">Selecciona una tarea...</option>
              {assignments.map((assignment) => (
                <option key={assignment.assignment_id} value={assignment.assignment_id}>
                  {assignment.title} - Entrega: {new Date(assignment.due_date).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>

          {/* Información del grupo */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Información del Grupo</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Código de Estudiante *
                </label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.submitted_by}
                  onChange={(e) => setFormData({ ...formData, submitted_by: e.target.value })}
                  placeholder="EST001"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Número de Grupo *
                </label>
                <input
                  type="number"
                  className="input-field"
                  value={formData.group_number}
                  onChange={(e) => setFormData({ ...formData, group_number: parseInt(e.target.value) })}
                  min="1"
                  required
                />
              </div>
            </div>
          </div>

          {/* Upload de código */}
          <div className="card">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Archivo de Código (ZIP) *
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-500 transition-colors">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <label className="cursor-pointer">
                <span className="text-primary-600 hover:text-primary-700 font-medium">
                  Seleccionar archivo ZIP
                </span>
                <input
                  type="file"
                  className="hidden"
                  accept=".zip"
                  onChange={(e) => handleFileChange(e, 'project_file')}
                  required
                />
              </label>
              <p className="text-sm text-gray-500 mt-2">
                {formData.project_file ? formData.project_file.name : 'Máx. 50MB'}
              </p>
            </div>
          </div>

          {/* Video URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              URL del Video Explicativo (Opcional)
            </label>
            <input
              type="url"
              value={formData.video_url || ''}
              onChange={(e) => setFormData({ ...formData, video_url: e.target.value })}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              YouTube, Google Drive, Vimeo, o cualquier URL de video público
            </p>
            {formData.video_url && (
              <p className="text-sm text-green-600 mt-2">
                ✓ URL ingresada
              </p>
            )}
          </div>

          {/* Info importante */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">ℹ️ Información Importante</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• El código será analizado automáticamente con IA (Llama 3.1 8B)</li>
              <li>• La evaluación incluye: Comprensión, Diseño, Implementación y Funcionalidad</li>
              <li>• Si subes video, también será transcrito y analizado</li>
              <li>• El proceso de evaluación toma aproximadamente 2-3 minutos</li>
              <li>• Recibirás feedback detallado por cada criterio</li>
            </ul>
          </div>

          {/* Botones */}
          <div className="flex space-x-4">
            <button
              type="button"
              onClick={() => navigate('/student')}
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
                  Subiendo...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  Subir Entrega
                </>
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
