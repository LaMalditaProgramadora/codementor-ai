import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, FileCode, Video } from 'lucide-react';
import { assignmentsAPI, submissionsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function SubmitAssignment() {
  const navigate = useNavigate();
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignment, setSelectedAssignment] = useState('');
  const [codeFile, setCodeFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [groupNumber, setGroupNumber] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      const response = await assignmentsAPI.getAll();
      setAssignments(response.data);
    } catch (error) {
      toast.error('Error al cargar tareas');
      console.error(error);
    }
  };

  const handleCodeFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.zip')) {
        toast.error('Solo se permiten archivos ZIP');
        return;
      }
      setCodeFile(file);
      toast.success(`Archivo seleccionado: ${file.name}`);
    }
  };

  const handleVideoFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const validTypes = ['video/mp4', 'video/webm', 'video/avi', 'video/quicktime'];
      if (!validTypes.includes(file.type)) {
        toast.error('Solo se permiten archivos de video (MP4, WebM, AVI, MOV)');
        return;
      }
      
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (file.size > maxSize) {
        toast.error('El video no debe superar 100MB');
        return;
      }
      
      setVideoFile(file);
      toast.success(`Video seleccionado: ${file.name}`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedAssignment) {
      toast.error('Selecciona una tarea');
      return;
    }

    if (!codeFile) {
      toast.error('Debes subir el código fuente (ZIP)');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('assignment_id', selectedAssignment);
      formData.append('section_id', 'SEC001');
      formData.append('group_number', groupNumber.toString());
      formData.append('submitted_by', 'EST001');
      formData.append('project_file', codeFile);
      
      if (videoFile) {
        formData.append('video_file', videoFile);
      }

      console.log('📤 Enviando submission:');
      for (let [key, value] of formData.entries()) {
        console.log(`  ${key}:`, value instanceof File ? `${value.name} (${value.size} bytes)` : value);
      }

      const response = await submissionsAPI.create(formData);

      toast.success('¡Entrega realizada con éxito!');
      
      setTimeout(() => {
        navigate(`/student/submission/${response.data.submission_id}`);
      }, 1500);

    } catch (error) {
      console.error('❌ Error completo:', error);
      console.error('Response:', error.response);
      
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          error.response.data.detail.forEach(err => {
            console.error(`Validation error: ${err.loc.join('.')}: ${err.msg}`);
            toast.error(`${err.loc.join('.')}: ${err.msg}`);
          });
        } else {
          toast.error(error.response.data.detail);
        }
      } else {
        toast.error('Error al realizar la entrega');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/student')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver al Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Entregar Tarea</h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="card">
          {/* Seleccionar Tarea */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Seleccionar Tarea *
            </label>
            <select
              value={selectedAssignment}
              onChange={(e) => setSelectedAssignment(e.target.value)}
              className="input-field"
              required
            >
              <option value="">-- Selecciona una tarea --</option>
              {assignments.map((assignment) => (
                <option key={assignment.assignment_id} value={assignment.assignment_id}>
                  {assignment.title}
                </option>
              ))}
            </select>
          </div>

          {/* Número de Grupo */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Número de Grupo
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={groupNumber}
              onChange={(e) => setGroupNumber(parseInt(e.target.value) || 1)}
              className="input-field"
            />
            <p className="text-xs text-gray-500 mt-1">
              Si trabajas solo, deja el valor en 1
            </p>
          </div>

          {/* Código Fuente */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Código Fuente (ZIP) *
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-primary-400 transition-colors">
              <div className="space-y-1 text-center">
                <FileCode className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500">
                    <span>Seleccionar archivo ZIP</span>
                    <input
                      type="file"
                      accept=".zip"
                      onChange={handleCodeFileChange}
                      className="sr-only"
                    />
                  </label>
                </div>
                {codeFile && (
                  <p className="text-sm text-green-600 font-medium">
                    ✓ {codeFile.name} ({(codeFile.size / 1024).toFixed(2)} KB)
                  </p>
                )}
                <p className="text-xs text-gray-500">
                  Archivo ZIP con tu proyecto completo
                </p>
              </div>
            </div>
          </div>

          {/* Video Explicativo */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Video Explicativo (Opcional)
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-purple-400 transition-colors">
              <div className="space-y-1 text-center">
                <Video className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label className="relative cursor-pointer bg-white rounded-md font-medium text-purple-600 hover:text-purple-500">
                    <span>Seleccionar video</span>
                    <input
                      type="file"
                      accept="video/mp4,video/webm,video/avi,video/quicktime"
                      onChange={handleVideoFileChange}
                      className="sr-only"
                    />
                  </label>
                </div>
                {videoFile && (
                  <p className="text-sm text-green-600 font-medium">
                    ✓ {videoFile.name} ({(videoFile.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
                <p className="text-xs text-gray-500">
                  MP4, WebM, AVI o MOV (máximo 100MB)
                </p>
              </div>
            </div>
          </div>

          {/* Botones */}
          <div className="flex items-center justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={() => navigate('/student')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex items-center px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Enviando...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Entregar Tarea
                </>
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}