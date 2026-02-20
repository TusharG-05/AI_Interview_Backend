import api from './api';

export const interviewService = {
    // Admin APIs
    getPapers: () => api.get('/admin/papers'),
    createPaper: (data) => api.post('/admin/papers', data),
    getInterviews: () => api.get('/admin/interviews'),
    scheduleInterview: (data) => api.post('/admin/interviews/schedule', data),
    getCandidates: () => api.get('/admin/users?role=candidate'), // Assuming this exists or needed

    // Candidate APIs
    getMyInterviews: () => api.get('/candidate/interviews'),
    getHistory: () => api.get('/candidate/history'),

    // General
    getInterviewSession: (token) => api.get(`/interview/access/${token}`),
};
