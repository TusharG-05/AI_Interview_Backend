import api from './api';

/**
 * Comprehensive API Service Layer
 * Integrates with all 67 backend endpoints
 */

// ==================== AUTHENTICATION SERVICES ====================
export const authService = {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  loginWithToken: async (formData) => {
    const response = await api.post('/auth/token', formData);
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};

// ==================== ADMIN SERVICES ====================
export const adminService = {
  // Question Papers
  getPapers: async (params = {}) => {
    const response = await api.get('/admin/papers', { params });
    return response.data;
  },

  createPaper: async (paperData) => {
    const response = await api.post('/admin/papers', paperData);
    return response.data;
  },

  getPaper: async (paperId) => {
    const response = await api.get(`/admin/papers/${paperId}`);
    return response.data;
  },

  updatePaper: async (paperId, paperData) => {
    const response = await api.patch(`/admin/papers/${paperId}`, paperData);
    return response.data;
  },

  deletePaper: async (paperId) => {
    const response = await api.delete(`/admin/papers/${paperId}`);
    return response.data;
  },

  // Paper Questions
  getPaperQuestions: async (paperId) => {
    const response = await api.get(`/admin/papers/${paperId}/questions`);
    return response.data;
  },

  addQuestionToPaper: async (paperId, questionData) => {
    const response = await api.post(`/admin/papers/${paperId}/questions`, questionData);
    return response.data;
  },

  getAllQuestions: async (params = {}) => {
    const response = await api.get('/admin/questions', { params });
    return response.data;
  },

  getQuestion: async (questionId) => {
    const response = await api.get(`/admin/questions/${questionId}`);
    return response.data;
  },

  updateQuestion: async (questionId, questionData) => {
    const response = await api.patch(`/admin/questions/${questionId}`, questionData);
    return response.data;
  },

  deleteQuestion: async (questionId) => {
    const response = await api.delete(`/admin/questions/${questionId}`);
    return response.data;
  },

  // AI Generation
  generatePaper: async (requestData) => {
    const response = await api.post('/admin/generate-paper', requestData);
    return response.data;
  },

  generateCodingPaper: async (requestData) => {
    const response = await api.post('/admin/generate-coding-paper', requestData);
    return response.data;
  },

  uploadDocument: async (paperId, file) => {
    const formData = new FormData();
    formData.append('paper_id', paperId);
    formData.append('file', file);
    
    const response = await api.post('/admin/upload-doc', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Interview Management
  scheduleInterview: async (interviewData) => {
    const response = await api.post('/admin/interviews/schedule', interviewData);
    return response.data;
  },

  getInterviews: async (params = {}) => {
    const response = await api.get('/admin/interviews', { params });
    return response.data;
  },

  getLiveStatus: async () => {
    const response = await api.get('/admin/interviews/live-status');
    return response.data;
  },

  getInterview: async (interviewId) => {
    const response = await api.get(`/admin/interviews/${interviewId}`);
    return response.data;
  },

  updateInterview: async (interviewId, updateData) => {
    const response = await api.patch(`/admin/interviews/${interviewId}`, updateData);
    return response.data;
  },

  deleteInterview: async (interviewId) => {
    const response = await api.delete(`/admin/interviews/${interviewId}`);
    return response.data;
  },

  // Results & Analytics
  getAllResults: async () => {
    const response = await api.get('/admin/users/results');
    return response.data;
  },

  getResult: async (interviewId) => {
    const response = await api.get(`/admin/results/${interviewId}`);
    return response.data;
  },

  updateResult: async (interviewId, updateData) => {
    const response = await api.patch(`/admin/results/${interviewId}`, updateData);
    return response.data;
  },

  deleteResult: async (interviewId) => {
    const response = await api.delete(`/admin/results/${interviewId}`);
    return response.data;
  },

  getResponse: async (responseId) => {
    const response = await api.get(`/admin/interviews/response/${responseId}`);
    return response.data;
  },

  getResponseAudio: async (responseId) => {
    const response = await api.get(`/admin/results/audio/${responseId}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  getEnrollmentAudio: async (interviewId) => {
    const response = await api.get(`/admin/interviews/enrollment-audio/${interviewId}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // User Management
  getCandidates: async (params = {}) => {
    const response = await api.get('/admin/candidates', { params });
    return response.data;
  },

  createUser: async (userData) => {
    const response = await api.post('/admin/users', userData);
    return response.data;
  },

  // Email Testing
  testEmail: async () => {
    const response = await api.get('/admin/test-email');
    return response.data;
  },

  testEmailSync: async () => {
    const response = await api.get('/admin/test-email-sync');
    return response.data;
  }
};

// ==================== CODING PAPERS SERVICES ====================
export const codingPapersService = {
  // Paper CRUD
  getCodingPapers: async (params = {}) => {
    const response = await api.get('/coding-papers/', { params });
    return response.data;
  },

  createCodingPaper: async (paperData) => {
    const response = await api.post('/coding-papers/', paperData);
    return response.data;
  },

  getCodingPaper: async (paperId) => {
    const response = await api.get(`/coding-papers/${paperId}`);
    return response.data;
  },

  updateCodingPaper: async (paperId, paperData) => {
    const response = await api.patch(`/coding-papers/${paperId}`, paperData);
    return response.data;
  },

  deleteCodingPaper: async (paperId) => {
    const response = await api.delete(`/coding-papers/${paperId}`);
    return response.data;
  },

  // Coding Questions CRUD
  getCodingQuestions: async (paperId) => {
    const response = await api.get(`/coding-papers/${paperId}/questions`);
    return response.data;
  },

  addCodingQuestion: async (paperId, questionData) => {
    const response = await api.post(`/coding-papers/${paperId}/questions`, questionData);
    return response.data;
  },

  updateCodingQuestion: async (questionId, questionData) => {
    const response = await api.patch(`/coding-papers/questions/${questionId}`, questionData);
    return response.data;
  },

  deleteCodingQuestion: async (questionId) => {
    const response = await api.delete(`/coding-papers/questions/${questionId}`);
    return response.data;
  }
};

// ==================== TEAMS SERVICES ====================
export const teamsService = {
  getTeams: async (params = {}) => {
    const response = await api.get('/teams/teams', { params });
    return response.data;
  },

  createTeam: async (teamData) => {
    const response = await api.post('/teams/teams', teamData);
    return response.data;
  },

  getTeam: async (teamId) => {
    const response = await api.get(`/teams/teams/${teamId}`);
    return response.data;
  },

  updateTeam: async (teamId, teamData) => {
    const response = await api.patch(`/teams/teams/${teamId}`, teamData);
    return response.data;
  },

  deleteTeam: async (teamId) => {
    const response = await api.delete(`/teams/teams/${teamId}`);
    return response.data;
  }
};

// ==================== CANDIDATE SERVICES ====================
export const candidateService = {
  getHistory: async () => {
    const response = await api.get('/candidate/history');
    return response.data;
  },

  getInterviews: async () => {
    const response = await api.get('/candidate/interviews');
    return response.data;
  },

  uploadSelfie: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/candidate/upload-selfie', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getProfileImage: async (userId) => {
    const response = await api.get(`/candidate/profile-image/${userId}`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// ==================== INTERVIEW SERVICES ====================
export const interviewService = {
  accessInterview: async (token) => {
    const response = await api.get(`/interview/access/${token}`);
    return response.data;
  },

  startSession: async (interviewId, enrollmentAudio) => {
    const formData = new FormData();
    formData.append('interview_id', interviewId);
    if (enrollmentAudio) {
      formData.append('enrollment_audio', enrollmentAudio);
    }
    
    const response = await api.post(`/interview/start-session/${interviewId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  uploadSelfie: async (interviewId, file) => {
    const formData = new FormData();
    formData.append('interview_id', interviewId);
    formData.append('file', file);
    
    const response = await api.post('/interview/upload-selfie', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getNextQuestion: async (interviewId) => {
    const response = await api.get(`/interview/next-question/${interviewId}`);
    return response.data;
  },

  getQuestionAudio: async (questionId) => {
    const response = await api.get(`/interview/audio/question/${questionId}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  submitAnswerAudio: async (interviewId, questionId, audioFile) => {
    const formData = new FormData();
    formData.append('interview_id', interviewId);
    formData.append('question_id', questionId);
    formData.append('audio', audioFile);
    
    const response = await api.post('/interview/submit-answer-audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  submitAnswerCode: async (interviewId, codingQuestionId, code, language) => {
    const formData = new FormData();
    formData.append('interview_id', interviewId);
    formData.append('coding_question_id', codingQuestionId);
    formData.append('code', code);
    if (language) {
      formData.append('language', language);
    }
    
    const response = await api.post('/interview/submit-answer-code', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  submitAnswerText: async (interviewId, questionId, answer) => {
    const formData = new FormData();
    formData.append('interview_id', interviewId);
    formData.append('question_id', questionId);
    formData.append('answer', answer);
    
    const response = await api.post('/interview/submit-answer-text', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  finishInterview: async (interviewId) => {
    const response = await api.post(`/interview/finish/${interviewId}`);
    return response.data;
  },

  evaluateAnswer: async (question, answer) => {
    const response = await api.post('/interview/evaluate-answer', { question, answer });
    return response.data;
  },

  logTabSwitch: async (interviewId) => {
    const response = await api.post(`/interview/${interviewId}/tab-switch`);
    return response.data;
  }
};

// ==================== SETTINGS SERVICES ====================
export const settingsService = {
  getSystemStatus: async () => {
    const response = await api.get('/settings/');
    return response.data;
  }
};

// ==================== VIDEO SERVICES ====================
export const videoService = {
  // Note: WebSocket endpoints are blocked on Hugging Face
  // These are provided for local development only
  getVideoFeed: async () => {
    try {
      const response = await api.get('/video/video_feed');
      return response.data;
    } catch (error) {
      console.warn('Video feed not available in production environment');
      return null;
    }
  },

  createOffer: async (offerData) => {
    try {
      const response = await api.post('/video/offer', offerData);
      return response.data;
    } catch (error) {
      console.warn('WebRTC not available in production environment');
      return null;
    }
  },

  watchSession: async (interviewId) => {
    try {
      const response = await api.post(`/video/watch/${interviewId}`);
      return response.data;
    } catch (error) {
      console.warn('Ghost mode not available in production environment');
      return null;
    }
  }
};

// ==================== UTILITY FUNCTIONS ====================
export const apiUtils = {
  handleApiError: (error) => {
    console.error('API Error:', error);
    
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    throw error;
  },

  getAuthHeaders: () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  formatFileSize: (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const idx = Math.min(i, sizes.length - 1);
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[idx]}`;
  }
};

export default {
  authService,
  adminService,
  codingPapersService,
  teamsService,
  candidateService,
  interviewService,
  settingsService,
  videoService,
  apiUtils
};
