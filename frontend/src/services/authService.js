import api from './api';

export const authService = {
    login: async (email, password) => {
        // In a real app, this would be a POST to /auth/token
        // For this MVP, we might simulate if the backend doesn't have a simple login yet
        // But assuming backend has /auth/token or similar
        try {
            const response = await api.post('/auth/login', { email, password });
            if (response.data?.access_token) {
                localStorage.setItem('token', response.data.access_token);
                localStorage.setItem('user', JSON.stringify(response.data.user));
            }
            return response.data;
        } catch (error) {
            console.error('Login failed', error);
            throw error;
        }
    },

    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    },

    getCurrentUser: () => {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    }
};
