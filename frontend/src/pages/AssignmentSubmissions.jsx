import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Users, CheckCircle, Clock, Download, AlertTriangle } from 'lucide-react';
import { assignmentsAPI, submissionsAPI, gradesAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function AssignmentSubmissions() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [assignmentRes, submissionsRes] = await Promise.all([
        assignmentsAPI.getById(id),
        submissionsAPI.getAll({ assignment_id: id }),
      ]);
      setAssignment(assignmentRes.data);
      setSubmissions(submissionsRes.data);
    } catch (error) {
      toast.error('Error al cargar datos');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async (submissionId) => {
    const confirm = window.confirm('¿Evaluar esta entrega con IA? Toma 1-2 minutos');
    if (!confirm) return;

    const evalToast = toast.loading('Evaluando con IA...');
    try {
      await submissionsAPI.evaluate(submissionId);
      toast.success('¡Evaluación completada!', { id: evalToast });
      loadData(); // Recargar datos
    } catch (error) {
      toast.error('Error al evaluar', { id: evalToast });
      console.error(error);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      uploaded: { color: 'bg-blue-100 text-blue-800', icon: Clock, text: 'Subido' },
      evaluating: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, text: 'Evaluando' },
      evaluated: { color: 'bg-green-100 text-green-800', icon: CheckCircle, text: 'Evaluado' },
    };
    const badge = badges[status] || badges.uploaded;
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${badge.color}`}>
        <Icon className="w-4 h-4 mr-1" />
        {badge.text}
      </span>
    );
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
          <button
            onClick={() => navigate('/instructor')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver al Dashboard
          </button>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{assignment?.title}</h1>
              <p className="text-sm text-gray-600">{assignment?.description}</p>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                <span>📅 Entrega: {new Date(assignment?.due_date).toLocaleDateString()}</span>
                <span>📊 Puntaje: {assignment?.max_score}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Estadísticas */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Entregas</p>
                <p className="text-3xl font-bold text-gray-900">{submissions.length}</p>
              </div>
              <Users className="w-12 h-12 text-primary-600" />
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
              <CheckCircle className="w-12 h-12 text-green-600" />
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

        {/* Lista de entregas */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Entregas</h2>
          
          {submissions.length === 0 ? (
            <div className="card text-center py-12">
              <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No hay entregas aún</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {submissions.map((submission) => (
                <div key={submission.submission_id} className="card hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          Entrega #{submission.submission_id}
                        </h3>
                        {getStatusBadge(submission.status)}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>📅 {new Date(submission.submission_date).toLocaleString()}</span>
                        <span>👤 {submission.submitted_by}</span>
                        <span>👥 Grupo {submission.group_number}</span>
                      </div>
                    </div>
                  </div>

                  {/* Archivos */}
                  <div className="mb-4 flex items-center space-x-4">
                    {submission.project_path && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Download className="w-4 h-4 mr-1" />
                        Código
                      </div>
                    )}
                    {submission.video_url && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Download className="w-4 h-4 mr-1" />
                        Video
                      </div>
                    )}
                  </div>

                  {/* Acciones */}
                  <div className="flex space-x-2">
                    {submission.status === 'uploaded' && (
                      <button
                        onClick={() => handleEvaluate(submission.submission_id)}
                        className="btn-primary flex-1"
                      >
                        Evaluar con IA
                      </button>
                    )}
                    
                    {submission.status === 'evaluated' && (
                      <button
                        onClick={() => navigate(`/student/submission/${submission.submission_id}`)}
                        className="btn-primary flex-1"
                      >
                        Ver Resultados
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}