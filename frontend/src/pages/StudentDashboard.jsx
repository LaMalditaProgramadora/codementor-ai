import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Video, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { submissionsAPI, assignmentsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function StudentDashboard() {
  const navigate = useNavigate();
  const [assignments, setAssignments] = useState([]);
  const [submissions, setSubmissions] = useState([]);
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

  const getStatusBadge = (status) => {
    const badges = {
      uploaded: { color: 'bg-blue-100 text-blue-800', icon: Clock, text: 'Subido' },
      evaluating: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, text: 'Evaluando' },
      evaluated: { color: 'bg-green-100 text-green-800', icon: CheckCircle, text: 'Evaluado' },
      pending: { color: 'bg-gray-100 text-gray-800', icon: AlertCircle, text: 'Pendiente' },
    };
    const badge = badges[status] || badges.pending;
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
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Portal Estudiante</h1>
              <p className="text-sm text-gray-600">Mis Tareas y Entregas</p>
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
        {/* Estadísticas rápidas */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tareas Disponibles</p>
                <p className="text-3xl font-bold text-gray-900">{assignments.length}</p>
              </div>
              <FileText className="w-12 h-12 text-primary-600" />
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Mis Entregas</p>
                <p className="text-3xl font-bold text-gray-900">{submissions.length}</p>
              </div>
              <Upload className="w-12 h-12 text-green-600" />
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
        </div>

        {/* Tareas disponibles */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900">Tareas Disponibles</h2>
            <button
              onClick={() => navigate('/student/submit')}
              className="btn-primary"
            >
              <Upload className="w-4 h-4 mr-2 inline" />
              Nueva Entrega
            </button>
          </div>

          {assignments.length === 0 ? (
            <div className="card text-center py-12">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No hay tareas disponibles</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {assignments.map((assignment) => (
                <div key={assignment.assignment_id} className="card hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        {assignment.title}
                      </h3>
                      <p className="text-gray-600 mb-4">{assignment.description}</p>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>📅 Entrega: {new Date(assignment.due_date).toLocaleDateString()}</span>
                        <span>📊 Puntaje máximo: {assignment.max_score}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => navigate('/student/submit', { state: { assignment } })}
                      className="btn-primary whitespace-nowrap"
                    >
                      Entregar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Mis entregas */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Mis Entregas</h2>
          
          {submissions.length === 0 ? (
            <div className="card text-center py-12">
              <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No has realizado entregas aún</p>
              <button
                onClick={() => navigate('/student/submit')}
                className="btn-primary mt-4"
              >
                Hacer mi primera entrega
              </button>
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
                        <span>👥 Grupo {submission.group_number}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {submission.project_path && (
                      <div className="flex items-center text-sm text-gray-600">
                        <FileText className="w-4 h-4 mr-1" />
                        Código
                      </div>
                    )}
                    {submission.video_url && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Video className="w-4 h-4 mr-1" />
                        Video
                      </div>
                    )}
                  </div>

                  {submission.status === 'evaluated' && (
                    <button
                      onClick={() => navigate(`/student/submission/${submission.submission_id}`)}
                      className="btn-primary mt-4 w-full"
                    >
                      Ver Resultados
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
