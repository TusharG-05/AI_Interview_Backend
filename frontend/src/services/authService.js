import api from './api';

export const authService = {
    login: async (email, password) => {
        // In a real app, this would be a POST to /auth/token
        // For this MVP, we might simulate if the backend doesn't have a simple login yet
        // But assuming backend has /auth/token or similar
        try {
            const response = await api.post('/auth/login', { email, password });
            // The audit tool confirmed the structure is: { status_code, data: { access_token, id, email, full_name, role, ... }, message, success }
            if (response.success && response.data?.access_token) {
                const { access_token, ...userData } = response.data;
                localStorage.setItem('token', access_token);
                localStorage.setItem('user', JSON.stringify(userData));
                return response.data;
            }
            throw new Error(response.message || 'Login failed');
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
