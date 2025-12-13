import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, FileCode, Video, Download, FileText } from 'lucide-react';
import { submissionsAPI, gradesAPI } from '../services/api';
import toast from 'react-hot-toast';

const safeParseFloat = (value, defaultValue = 0) => {
  if (value === null || value === undefined) return defaultValue;
  const parsed = parseFloat(value);
  return isNaN(parsed) ? defaultValue : parsed;
};

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
      
      if (gradesRes.data && gradesRes.data.length > 0) {
        const gradeData = gradesRes.data[0];
        
        try {
          const feedbackRes = await fetch(`http://localhost:8000/api/feedback?grade_id=${gradeData.grade_id}`);
          const feedbackData = await feedbackRes.json();
          
          if (feedbackData && feedbackData.length > 0) {
            gradeData.feedback = feedbackData[0];
          }
        } catch (error) {
          console.error('Error loading feedback:', error);
        }
        
        setGrade(gradeData);
      }
    } catch (error) {
      toast.error('Error al cargar resultados');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadSubmission = () => {
    if (submission?.project_path) {
      const minioUrl = `http://localhost:9000/${submission.project_path}`;
      window.open(minioUrl, '_blank');
    } else {
      toast.error('No hay archivo disponible para descargar');
    }
  };

  const getScoreBg = (score) => {
    const percentage = (score / 5) * 100;
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreBadge = (score) => {
    const percentage = (score / 5) * 100;
    if (percentage >= 80) return 'bg-green-100 text-green-800';
    if (percentage >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
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
          <p className="text-gray-600">No se encontraron resultados para esta entrega</p>
          <button onClick={() => navigate('/student')} className="btn-primary mt-4">
            Volver al Dashboard
          </button>
        </div>
      </div>
    );
  }

  const comprehensionScore = safeParseFloat(grade.ai_comprehension_score);
  const designScore = safeParseFloat(grade.ai_design_score);
  const implementationScore = safeParseFloat(grade.ai_implementation_score);
  const functionalityScore = safeParseFloat(grade.ai_functionality_score);
  const totalScore = grade.ai_total_score ? safeParseFloat(grade.ai_total_score) : comprehensionScore + designScore + implementationScore + functionalityScore;
  const maxScore = 20;
  const scorePercentage = (totalScore / maxScore) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button onClick={() => navigate('/student')} className="flex items-center text-gray-600 hover:text-gray-900 mb-4">
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver al Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Resultados de Evaluación</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card mb-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">📎 Archivos Entregados</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {submission.project_path && (
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center space-x-3">
                  <FileCode className="w-6 h-6 text-blue-600" />
                  <div>
                    <p className="font-medium text-gray-900">Código Fuente</p>
                    <p className="text-sm text-gray-600">{submission.project_path.split('/').pop()}</p>
                  </div>
                </div>
                <button onClick={handleDownloadSubmission} className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  <Download className="w-4 h-4" />
                  <span>Descargar</span>
                </button>
              </div>
            )}
            {submission.video_url && (
              <div className="card mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">🎥 Video Explicativo</h3>
                <div className="aspect-video bg-black rounded-lg overflow-hidden">
                  <video
                    controls
                    className="w-full h-full"
                    src={`http://localhost:8000/api/submissions/${submission.submission_id}/video`}
                  >
                    Tu navegador no soporta la reproducción de video.
                  </video>
                </div>
                <div className="mt-4 flex justify-end">
                  <a
                    href={`http://localhost:8000/api/submissions/${submission.submission_id}/video`}
                    download
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    <span>Descargar Video</span>
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="card mb-8 text-center">
          <div className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-blue-100 text-blue-800 mb-4">
            <CheckCircle className="w-4 h-4 mr-2" />
            Evaluado con IA: Llama 3.1 8B
          </div>
          <div className="mb-2">
            <span className="text-6xl font-bold" style={{ color: scorePercentage >= 80 ? '#10b981' : scorePercentage >= 60 ? '#f59e0b' : '#ef4444' }}>
              {totalScore.toFixed(1)}
            </span>
            <span className="text-2xl text-gray-500">/{maxScore}</span>
          </div>
          <p className="text-gray-600 font-medium">Puntaje Total</p>
          <p className="text-sm text-gray-500 mt-1">{scorePercentage.toFixed(0)}% - Escala vigesimal: {totalScore.toFixed(1)}/20</p>
        </div>

        <div className="card mb-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">📊 Detalle de Evaluación</h3>
          <div className="space-y-6">
            <div className="border-l-4 border-blue-500 pl-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">📘</span>
                  <h4 className="text-lg font-semibold text-gray-900">Comprensión del Problema</h4>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreBadge(comprehensionScore)}`}>
                  {comprehensionScore.toFixed(1)}/5 puntos
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                <div className={`h-3 rounded-full ${getScoreBg(comprehensionScore)}`} style={{ width: `${(comprehensionScore / 5) * 100}%` }}></div>
              </div>
              {grade.feedback?.comprehension_comments && (
                <div className="mt-3 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{grade.feedback.comprehension_comments}</p>
                </div>
              )}
            </div>

            <div className="border-l-4 border-purple-500 pl-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">🎨</span>
                  <h4 className="text-lg font-semibold text-gray-900">Diseño de la Solución</h4>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreBadge(designScore)}`}>
                  {designScore.toFixed(1)}/5 puntos
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                <div className={`h-3 rounded-full ${getScoreBg(designScore)}`} style={{ width: `${(designScore / 5) * 100}%` }}></div>
              </div>
              {grade.feedback?.design_comments && (
                <div className="mt-3 p-4 bg-purple-50 rounded-lg">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{grade.feedback.design_comments}</p>
                </div>
              )}
            </div>

            <div className="border-l-4 border-green-500 pl-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">💻</span>
                  <h4 className="text-lg font-semibold text-gray-900">Implementación</h4>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreBadge(implementationScore)}`}>
                  {implementationScore.toFixed(1)}/5 puntos
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                <div className={`h-3 rounded-full ${getScoreBg(implementationScore)}`} style={{ width: `${(implementationScore / 5) * 100}%` }}></div>
              </div>
              {grade.feedback?.implementation_comments && (
                <div className="mt-3 p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{grade.feedback.implementation_comments}</p>
                </div>
              )}
            </div>

            <div className="border-l-4 border-yellow-500 pl-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">⚡</span>
                  <h4 className="text-lg font-semibold text-gray-900">Funcionalidad</h4>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreBadge(functionalityScore)}`}>
                  {functionalityScore.toFixed(1)}/5 puntos
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                <div className={`h-3 rounded-full ${getScoreBg(functionalityScore)}`} style={{ width: `${(functionalityScore / 5) * 100}%` }}></div>
              </div>
              {grade.feedback?.functionality_comments && (
                <div className="mt-3 p-4 bg-yellow-50 rounded-lg">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{grade.feedback.functionality_comments}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {grade.feedback?.general_comments && (
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <span className="text-2xl">📝</span>
              <h3 className="text-xl font-bold text-gray-900">Comentarios Generales</h3>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{grade.feedback.general_comments}</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}