import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FileText, Users, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { assignmentsAPI, submissionsAPI, plagiarismAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function InstructorDashboard() {
  const navigate = useNavigate();
  const [assignments, setAssignments] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [plagiarismDetections, setPlagiarismDetections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [assignmentsRes, submissionsRes] = await Promise.all([
        assignmentsAPI.getAll(),
        submissionsAPI.getAll(),
      ]);
      setAssignments(assignmentsRes.data);
      setSubmissions(submissionsRes.data);
    } catch (error) {
      toast.error('Error al cargar datos');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDetectPlagiarism = async (assignmentId) => {
    const confirmDetect = window.confirm(
      '¿Deseas analizar plagio para esta tarea? Esto comparará todas las entregas.'
    );
    
    if (!confirmDetect) return;

    const detectToast = toast.loading('Analizando plagio...');
    try {
      const res = await plagiarismAPI.detect(assignmentId);
      toast.success(`Detecciones encontradas: ${res.data.length}`, { id: detectToast });
      setPlagiarismDetections(res.data);
    } catch (error) {
      toast.error('Error al detectar plagio', { id: detectToast });
      console.error(error);
    }
  };

  const getSubmissionStats = (assignmentId) => {
    const assignmentSubmissions = submissions.filter(
      (s) => s.assignment_id === assignmentId
    );
    return {
      total: assignmentSubmissions.length,
      evaluated: assignmentSubmissions.filter((s) => s.status === 'evaluated').length,
      pending: assignmentSubmissions.filter((s) => s.status === 'uploaded').length,
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Portal Docente</h1>
              <p className="text-sm text-gray-600">Gestión de Tareas y Entregas</p>
            </div>
            <button
              onClick={() => navigate('/')}
              className="btn-secondary text-sm"
            >
              Cambiar Rol
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Estadísticas */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tareas Creadas</p>
                <p className="text-3xl font-bold text-gray-900">{assignments.length}</p>
              </div>
              <FileText className="w-12 h-12 text-primary-600" />
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Entregas</p>
                <p className="text-3xl font-bold text-gray-900">{submissions.length}</p>
              </div>
              <Users className="w-12 h-12 text-green-600" />
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Evaluadas</p>
                <p className="text-3xl font-bold text-gray-900">
                  {submissions.filter(s => s.status === 'evaluated').length}
                </p>
              </div>
              <CheckCircle className="w-12 h-12 text-blue-600" />
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pendientes</p>
                <p className="text-3xl font-bold text-gray-900">
                  {submissions.filter(s => s.status === 'uploaded').length}
                </p>
              </div>
              <Clock className="w-12 h-12 text-yellow-600" />
            </div>
          </div>
        </div>

        {/* Tareas creadas */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900">Mis Tareas</h2>
            <button
              onClick={() => navigate('/instructor/create-assignment')}
              className="btn-primary"
            >
              <Plus className="w-4 h-4 mr-2 inline" />
              Nueva Tarea
            </button>
          </div>

          {assignments.length === 0 ? (
            <div className="card text-center py-12">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No has creado tareas aún</p>
              <button
                onClick={() => navigate('/instructor/create-assignment')}
                className="btn-primary"
              >
                Crear mi primera tarea
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {assignments.map((assignment) => {
                const stats = getSubmissionStats(assignment.assignment_id);
                return (
                  <div key={assignment.assignment_id} className="card hover:shadow-lg transition-shadow">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                          {assignment.title}
                        </h3>
                        <p className="text-gray-600 mb-2">{assignment.description}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>📅 Entrega: {new Date(assignment.due_date).toLocaleDateString()}</span>
                          <span>📊 Puntaje: {assignment.max_score}</span>
                          <span>📝 Sección: {assignment.section_id}</span>
                        </div>
                      </div>
                    </div>

                    {/* Estadísticas de entregas */}
                    <div className="flex items-center space-x-6 mb-4 pb-4 border-b">
                      <div className="flex items-center">
                        <Users className="w-5 h-5 text-gray-400 mr-2" />
                        <span className="text-sm text-gray-700">
                          <span className="font-semibold">{stats.total}</span> entregas
                        </span>
                      </div>
                      <div className="flex items-center">
                        <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                        <span className="text-sm text-gray-700">
                          <span className="font-semibold">{stats.evaluated}</span> evaluadas
                        </span>
                      </div>
                      <div className="flex items-center">
                        <Clock className="w-5 h-5 text-yellow-500 mr-2" />
                        <span className="text-sm text-gray-700">
                          <span className="font-semibold">{stats.pending}</span> pendientes
                        </span>
                      </div>
                    </div>

                    {/* Acciones */}
                    <div className="flex space-x-2">
                      <button
                        onClick={() => navigate(`/instructor/assignment/${assignment.assignment_id}`)}
                        className="btn-primary flex-1"
                      >
                        Ver Entregas
                      </button>
                      <button
                        onClick={() => handleDetectPlagiarism(assignment.assignment_id)}
                        className="btn-secondary"
                      >
                        <AlertTriangle className="w-4 h-4 mr-1 inline" />
                        Detectar Plagio
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Detecciones de plagio recientes */}
        {plagiarismDetections.length > 0 && (
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <AlertTriangle className="w-6 h-6 text-yellow-600 mr-2" />
              Detecciones de Plagio Recientes
            </h2>
            <div className="space-y-3">
              {plagiarismDetections.map((detection, idx) => (
                <div key={idx} className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Similitud entre entregas #{detection.submission_id_1} y #{detection.submission_id_2}
                      </p>
                      <p className="text-sm text-gray-600">
                        Similitud semántica: {detection.semantic_similarity}%
                      </p>
                    </div>
                    <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                      {detection.status === 'suspicious' ? 'Muy sospechoso' : 'Revisar'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
