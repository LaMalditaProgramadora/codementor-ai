import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Assignments
export const assignmentsAPI = {
  getAll: (sectionId) => api.get('/api/assignments', { params: { section_id: sectionId } }),
  getById: (id) => api.get(`/api/assignments/${id}`),
  create: (data) => api.post('/api/assignments', data),
};

// Submissions
export const submissionsAPI = {
  getAll: (params) => api.get('/api/submissions', { params }),
  getById: (id) => api.get(`/api/submissions/${id}`),
  create: (formData) => api.post('/api/submissions', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  evaluate: (id) => api.post(`/api/submissions/${id}/evaluate`),
  downloadProject: (id) => api.get(`/api/submissions/${id}/download/project`),
  downloadVideo: (id) => api.get(`/api/submissions/${id}/download/video`),
};

// Grades
export const gradesAPI = {
  getAll: (params) => api.get('/api/grades', { params }),
  getById: (id) => api.get(`/api/grades/${id}`),
  update: (id, data) => api.put(`/api/grades/${id}`, data),
};

// Students
export const studentsAPI = {
  getAll: (params) => api.get('/api/students', { params }),
  getById: (id) => api.get(`/api/students/${id}`),
  create: (data) => api.post('/api/students', data),
};

// Sections
export const sectionsAPI = {
  getAll: () => api.get('/api/sections'),
  getById: (id) => api.get(`/api/sections/${id}`),
  create: (data) => api.post('/api/sections', data),
};

// Plagiarism
export const plagiarismAPI = {
  detect: (assignmentId) => api.post(`/api/plagiarism/detect?assignment_id=${assignmentId}`),
  getDetections: (params) => api.get('/api/plagiarism', { params }),
};

// Health check
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
