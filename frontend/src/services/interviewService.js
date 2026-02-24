import api from './api';

export const interviewService = {
    // Admin APIs
    getPapers: () => api.get('/admin/papers'),
    createPaper: (data) => api.post('/admin/papers', data),
    getPaper: (id) => api.get(`/admin/papers/${id}`),
    updatePaper: (id, data) => api.patch(`/admin/papers/${id}`, data),
    deletePaper: (id) => api.delete(`/admin/papers/${id}`),

    // Questions
    addQuestion: (paperId, data) => api.post(`/admin/papers/${paperId}/questions`, data),
    updateQuestion: (qId, data) => api.patch(`/admin/questions/${qId}`, data),
    deleteQuestion: (qId) => api.delete(`/admin/questions/${qId}`),

    getInterviews: () => api.get('/admin/interviews'),
    scheduleInterview: (data) => api.post('/admin/interviews/schedule', data),
    deleteInterview: (id) => api.delete(`/admin/interviews/${id}`), // Method to delete interview
    watchInterview: (id, offer) => api.post(`/analyze/video/watch/${id}`, offer),
    getLiveStatus: () => api.get('/admin/interviews/live-status'),

    // Candidates
    getCandidates: (skip = 0, limit = 20, search = '') => {
        let url = `/admin/candidates?skip=${skip}&limit=${limit}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        return api.get(url);
    },
    createCandidate: (data) => api.post('/admin/users', data),
    updateCandidate: (id, data) => api.patch(`/admin/users/${id}`, data),
    deleteCandidate: (id) => api.delete(`/admin/users/${id}`),

    // Candidate APIs
    getMyInterviews: () => api.get('/candidate/interviews'),
    getHistory: () => api.get('/candidate/history'),
    uploadSelfie: (formData) => api.post('/interview/upload-selfie', formData),

    // Interview Flow
    getInterviewAccess: (token) => api.get(`/interview/access/${token}`),
    startSession: (id) => api.post(`/interview/start-session/${id}`),
    getNextQuestion: (id) => api.get(`/interview/next-question/${id}`),
    submitAnswerAudio: (formData) => api.post('/interview/submit-answer-audio', formData),
    submitAnswerText: (data) => api.post('/interview/submit-answer-text', data),
    finishInterview: (id) => api.post(`/interview/finish/${id}`),
    getAudioUrl: (responseId) => `${api.defaults.baseURL}/admin/results/audio/${responseId}`,

    // WebRTC Proctoring
    offerVideoStream: (sdp, interview_id) => api.post('/analyze/video/offer', {
        sdp,
        type: 'offer',
        interview_id
    }),

    // General
    getInterviewResult: (id) => api.get(`/admin/results/${id}`),
};
