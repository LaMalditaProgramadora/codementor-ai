import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, CheckCircle, AlertCircle } from 'lucide-react';
import { submissionsAPI, gradesAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function SubmissionResults() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState(null);
  const [grade, setGrade] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [submissionRes, gradesRes] = await Promise.all([
        submissionsAPI.getById(id),
        gradesAPI.getAll({ submission_id: id }),
      ]);
      setSubmission(submissionRes.data);
      if (gradesRes.data.length > 0) {
        setGrade(gradesRes.data[0]);
      }
    } catch (error) {
      toast.error('Error al cargar resultados');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!submission || !grade) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="card text-center">
          <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">No se encontraron resultados</h2>
          <p className="text-gray-600 mb-4">Esta entrega aún no ha sido evaluada</p>
          <button onClick={() => navigate('/student')} className="btn-primary">
            Volver al Dashboard
          </button>
        </div>
      </div>
    );
  }

  const criteria = [
    {
      name: 'Comprensión',
      score: grade.ai_comprehension_score,
      description: 'Entendimiento de requisitos y problemas',
    },
    {
      name: 'Diseño',
      score: grade.ai_design_score,
      description: 'Arquitectura y patrones de diseño',
    },
    {
      name: 'Implementación',
      score: grade.ai_implementation_score,
      description: 'Calidad del código y buenas prácticas',
    },
    {
      name: 'Funcionalidad',
      score: grade.ai_functionality_score,
      description: 'Características funcionando correctamente',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/student')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver al Dashboard
          </button>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Resultados de Evaluación</h1>
              <p className="text-sm text-gray-600">
                Entrega #{submission.submission_id} • {new Date(submission.submission_date).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <span className="text-sm font-medium text-green-600">Evaluado</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Puntaje total */}
        <div className={`card mb-8 border-2 ${getScoreBg(grade.ai_total_score)}`}>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600 mb-2">Puntaje Total</p>
            <p className={`text-6xl font-bold ${getScoreColor(grade.ai_total_score)}`}>
              {parseFloat(grade.ai_total_score).toFixed(1)}
            </p>
            <p className="text-sm text-gray-600 mt-2">de 100 puntos</p>
            <div className="mt-4 flex items-center justify-center space-x-2">
              <div className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                🤖 Evaluado con IA: Llama 3.1 8B
              </div>
            </div>
          </div>
        </div>

        {/* Puntajes por criterio */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {criteria.map((criterion) => (
            <div key={criterion.name} className="card">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{criterion.name}</h3>
                  <p className="text-sm text-gray-600">{criterion.description}</p>
                </div>
                <span className={`text-3xl font-bold ${getScoreColor(criterion.score)}`}>
                  {parseFloat(criterion.score).toFixed(1)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                <div
                  className={`h-2 rounded-full transition-all ${
                    criterion.score >= 80 ? 'bg-green-600' :
                    criterion.score >= 60 ? 'bg-yellow-600' : 'bg-red-600'
                  }`}
                  style={{ width: `${criterion.score}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>

        {/* Feedback de IA */}
        <div className="card mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">💬 Feedback de IA</h2>
          <div className="space-y-4">
            {grade.feedback && (
              <>
                {grade.feedback.comprehension_comments && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-blue-900 mb-2">📖 Comprensión</h3>
                    <p className="text-blue-800 text-sm">{grade.feedback.comprehension_comments}</p>
                  </div>
                )}
                
                {grade.feedback.design_comments && (
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-purple-900 mb-2">🎨 Diseño</h3>
                    <p className="text-purple-800 text-sm">{grade.feedback.design_comments}</p>
                  </div>
                )}
                
                {grade.feedback.implementation_comments && (
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-green-900 mb-2">💻 Implementación</h3>
                    <p className="text-green-800 text-sm">{grade.feedback.implementation_comments}</p>
                  </div>
                )}
                
                {grade.feedback.functionality_comments && (
                  <div className="bg-yellow-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-yellow-900 mb-2">⚙️ Funcionalidad</h3>
                    <p className="text-yellow-800 text-sm">{grade.feedback.functionality_comments}</p>
                  </div>
                )}
                
                {grade.feedback.general_comments && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">📝 Comentarios Generales</h3>
                    <p className="text-gray-800 text-sm">{grade.feedback.general_comments}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Archivos de la entrega */}
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📁 Archivos de la Entrega</h2>
          <div className="space-y-2">
            {submission.project_path && (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-700">📦 Código del proyecto</span>
                <button className="btn-secondary text-sm">
                  <Download className="w-4 h-4 mr-1 inline" />
                  Descargar
                </button>
              </div>
            )}
            {submission.video_url && (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-700">🎥 Video de presentación</span>
                <button className="btn-secondary text-sm">
                  <Download className="w-4 h-4 mr-1 inline" />
                  Descargar
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
