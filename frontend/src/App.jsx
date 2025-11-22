import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Pages
import HomePage from './pages/HomePage';
import StudentDashboard from './pages/StudentDashboard';
import SubmitAssignment from './pages/SubmitAssignment';
import SubmissionResults from './pages/SubmissionResults';
import InstructorDashboard from './pages/InstructorDashboard';
import CreateAssignment from './pages/CreateAssignment';
import AssignmentSubmissions from './pages/AssignmentSubmissions';

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 4000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      
      <Routes>
        {/* Home */}
        <Route path="/" element={<HomePage />} />
        
        {/* Student Routes */}
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/student/submit" element={<SubmitAssignment />} />
        <Route path="/student/submission/:id" element={<SubmissionResults />} />
        
        {/* Instructor Routes */}
        <Route path="/instructor" element={<InstructorDashboard />} />
        <Route path="/instructor/create-assignment" element={<CreateAssignment />} />
        <Route path="/instructor/assignment/:id" element={<AssignmentSubmissions />} />
        
        {/* 404 */}
        <Route path="*" element={
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
              <p className="text-xl text-gray-600 mb-8">Página no encontrada</p>
              <a href="/" className="btn-primary">
                Volver al inicio
              </a>
            </div>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
