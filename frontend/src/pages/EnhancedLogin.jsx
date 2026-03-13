import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, User, AlertCircle } from 'lucide-react';
import { authService } from '../services/enhancedApi';
import { Button, Input, Card, ErrorAlert, SuccessAlert } from './UI';

/**
 * Professional Login Component
 * Enhanced with better UX and error handling
 */
const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      window.location.href = '/admin';
    }
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authService.login(formData);
      
      if (response.success) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        setSuccess('Login successful! Redirecting...');
        
        setTimeout(() => {
          window.location.href = '/admin';
        }, 1500);
      } else {
        setError(response.message || 'Login failed');
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    setLoading(true);
    setError('');

    try {
      // Simple registration with default values
      const userData = {
        email: formData.email,
        password: formData.password,
        full_name: formData.email.split('@')[0],
        role: 'CANDIDATE'
      };

      const response = await authService.register(userData);
      
      if (response.success) {
        setSuccess('Registration successful! You can now login.');
      } else {
        setError(response.message || 'Registration failed');
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md space-y-8"
      >
        {/* Header */}
        <div className="text-center">
          <motion.h2
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-3xl font-extrabold text-gray-900 mb-2"
          >
            AI Interview Platform
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-gray-600 text-sm"
          >
            Sign in to your account or create a new one
          </motion.p>
        </div>

        {/* Error Alert */}
        {error && (
          <ErrorAlert
            error={error}
            onDismiss={() => setError('')}
          />
        )}

        {/* Success Alert */}
        {success && (
          <SuccessAlert
            message={success}
            onDismiss={() => setSuccess('')}
          />
        )}

        {/* Login Form */}
        <Card className="mt-8" title="Sign In">
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <Input
                label="Email Address"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleInputChange}
                required
                icon={Mail}
              />
            </div>

            <div>
              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleInputChange}
                required
                icon={Lock}
                error={error.toLowerCase().includes('password')}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="remember"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="remember" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>
              
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-sm text-blue-600 hover:text-blue-500 transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            <Button
              type="submit"
              loading={loading}
              disabled={!formData.email || !formData.password}
              className="w-full"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </Button>
          </form>

          {/* Register Link */}
          <div className="mt-6 text-center">
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-sm text-gray-600"
            >
              Don't have an account?{' '}
              <button
                type="button"
                onClick={handleRegister}
                className="font-medium text-blue-600 hover:text-blue-500 transition-colors"
              >
                Sign up
              </button>
            </motion.p>
          </div>
        </Card>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-8 text-center text-sm text-gray-500"
        >
          <p>&copy; 2026 AI Interview Platform. All rights reserved.</p>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default Login;
