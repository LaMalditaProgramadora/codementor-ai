import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, FileCode, Video } from 'lucide-react';
import { submissionsAPI, gradesAPI } from '../services/api';
import toast from 'react-hot-toast';

// Helper para convertir strings a números de forma segura
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
    const percentage = (score / 5) * 100; // Escala 0-5
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    const percentage = (score / 5) * 100; // Escala 0-5
    if (percentage >= 80) return 'bg-green-100';
    if (percentage >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
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

  // Calcular scores de forma segura
  const comprehensionScore = safeParseFloat(grade.ai_comprehension_score);
  const designScore = safeParseFloat(grade.ai_design_score);
  const implementationScore = safeParseFloat(grade.ai_implementation_score);
  const functionalityScore = safeParseFloat(grade.ai_functionality_score);

  // Calcular total (preferir ai_total_score si existe)
  const totalScore = grade.ai_total_score 
    ? safeParseFloat(grade.ai_total_score)
    : comprehensionScore + designScore + implementationScore + functionalityScore;

  // Nota: Los scores vienen en escala 0-5 cada uno, total 20
  const maxScore = 20;
  const scorePercentage = (totalScore / maxScore) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/student')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver al Dashboard
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Resultados de Evaluación</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Puntaje Total */}
        <div className="card mb-8 text-center">
          <div className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-blue-100 text-blue-800 mb-4">
            <CheckCircle className="w-4 h-4 mr-2" />
            Evaluado con IA: Llama 3.1 8B
          </div>
          
          <div className="mb-2">
            <span 
              className="text-6xl font-bold" 
              style={{ 
                color: scorePercentage >= 80 ? '#10b981' : scorePercentage >= 60 ? '#f59e0b' : '#ef4444' 
              }}
            >
              {totalScore.toFixed(1)}
            </span>
            <span className="text-2xl text-gray-500">/{maxScore}</span>
          </div>
          <p className="text-gray-600">Puntaje Total</p>
          <p className="text-sm text-gray-500 mt-1">
            {scorePercentage.toFixed(0)}% - Escala vigesimal: {(totalScore * 20 / maxScore).toFixed(1)}/20
          </p>
        </div>

        {/* Criterios de Evaluación */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Comprensión */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Comprensión del Problema</h3>
              <span className={`text-2xl font-bold ${getScoreColor(comprehensionScore)}`}>
                {comprehensionScore.toFixed(1)}/5
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full ${getScoreBg(comprehensionScore)}`}
                style={{ width: `${(comprehensionScore / 5) * 100}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">Entendimiento de requisitos</p>
          </div>

          {/* Diseño */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Diseño de la Solución</h3>
              <span className={`text-2xl font-bold ${getScoreColor(designScore)}`}>
                {designScore.toFixed(1)}/5
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full ${getScoreBg(designScore)}`}
                style={{ width: `${(designScore / 5) * 100}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">Arquitectura y patrones de diseño</p>
          </div>

          {/* Implementación */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Implementación</h3>
              <span className={`text-2xl font-bold ${getScoreColor(implementationScore)}`}>
                {implementationScore.toFixed(1)}/5
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full ${getScoreBg(implementationScore)}`}
                style={{ width: `${(implementationScore / 5) * 100}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">Calidad de código y buenas prácticas</p>
          </div>

          {/* Funcionalidad */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Funcionalidad</h3>
              <span className={`text-2xl font-bold ${getScoreColor(functionalityScore)}`}>
                {functionalityScore.toFixed(1)}/5
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full ${getScoreBg(functionalityScore)}`}
                style={{ width: `${(functionalityScore / 5) * 100}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">Requisitos funcionan correctamente</p>
          </div>
        </div>

        {/* Feedback */}
        {grade.feedback && (
          <div className="card mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Retroalimentación Detallada</h3>
            
            <div className="space-y-4">
              {grade.feedback.comprehension_comments && (
                <div className="border-l-4 border-blue-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1 flex items-center">
                    <span className="mr-2">📘</span>
                    Comprensión del Problema ({comprehensionScore.toFixed(1)}/5)
                  </h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{grade.feedback.comprehension_comments}</p>
                </div>
              )}
              
              {grade.feedback.design_comments && (
                <div className="border-l-4 border-purple-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1 flex items-center">
                    <span className="mr-2">🎨</span>
                    Diseño de la Solución ({designScore.toFixed(1)}/5)
                  </h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{grade.feedback.design_comments}</p>
                </div>
              )}
              
              {grade.feedback.implementation_comments && (
                <div className="border-l-4 border-green-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1 flex items-center">
                    <span className="mr-2">💻</span>
                    Implementación ({implementationScore.toFixed(1)}/5)
                  </h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{grade.feedback.implementation_comments}</p>
                </div>
              )}
              
              {grade.feedback.functionality_comments && (
                <div className="border-l-4 border-yellow-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1 flex items-center">
                    <span className="mr-2">⚡</span>
                    Funcionalidad ({functionalityScore.toFixed(1)}/5)
                  </h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{grade.feedback.functionality_comments}</p>
                </div>
              )}
              
              {grade.feedback.general_comments && (
                <div className="border-l-4 border-gray-500 pl-4 py-2">
                  <h4 className="font-semibold text-gray-900 mb-1 flex items-center">
                    <span className="mr-2">📝</span>
                    Comentarios Generales
                  </h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{grade.feedback.general_comments}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Archivos */}
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Archivos Entregados</h3>
          <div className="flex space-x-4">
            {submission.project_path && (
              <div className="flex items-center space-x-2 text-gray-700">
                <FileCode className="w-5 h-5 text-blue-600" />
                <span>Código fuente</span>
              </div>
            )}
            {submission.video_url && (
              <div className="flex items-center space-x-2 text-gray-700">
                <Video className="w-5 h-5 text-purple-600" />
                <span>Video explicativo</span>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}