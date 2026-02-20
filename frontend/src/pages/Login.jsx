import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, User, ArrowRight, Loader2, Mail, Lock, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { authService } from '../services/authService';

const Login = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const result = await authService.login(email, password);
            const user = result;
            if (user.role === 'admin' || user.role === 'super_admin') {
                navigate('/admin');
            } else {
                navigate('/candidate');
            }
        } catch (err) {
            setError(err.message || 'Invalid credentials. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-white flex flex-col md:flex-row shadow-2xl overflow-hidden">
            {/* Left Side - Brand and Welcome */}
            <div className="md:w-1/2 bg-brand-orange p-12 flex flex-col justify-between text-white relative">
                <div className="z-10">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center">
                            <span className="text-brand-orange font-bold text-2xl">v</span>
                        </div>
                        <span className="font-bold text-3xl tracking-tight leading-none">VisionAI</span>
                    </div>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <h1 className="text-5xl font-extrabold mb-6 leading-tight">
                            Reinventing <br />
                            <span className="text-brand-orange-light">Technical Hiring</span>
                        </h1>
                        <p className="text-xl text-white/80 max-w-md">
                            The world's most advanced AI-proctored interview platform with real-time gaze and face tracking.
                        </p>
                    </motion.div>
                </div>

                <div className="mt-12 md:mt-0 z-10 flex gap-4 items-center">
                    <div className="flex -space-x-2">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="w-10 h-10 rounded-full border-2 border-brand-orange bg-white/20" />
                        ))}
                    </div>
                    <p className="text-sm font-medium">Joined by 10,000+ candidates today</p>
                </div>

                {/* Decorative Elements */}
                <div className="absolute top-[-10%] right-[-10%] w-64 h-64 bg-white/10 rounded-full blur-3xl text-brand-orange" />
                <div className="absolute bottom-[10%] left-[-5%] w-48 h-48 bg-black/10 rounded-full blur-2xl text-brand-orange" />
            </div>

            {/* Right Side - Login Form */}
            <div className="md:w-1/2 p-8 md:p-24 flex flex-col justify-center bg-gray-50">
                <div className="max-w-md w-full mx-auto">
                    <div className="mb-10 text-center md:text-left">
                        <h2 className="text-4xl font-black text-gray-900 mb-3 tracking-tight">Welcome Back</h2>
                        <p className="text-gray-500 font-medium">Enter your credentials to access the portal.</p>
                    </div>

                    <AnimatePresence>
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-600 text-sm font-semibold"
                            >
                                <AlertCircle size={18} />
                                {error}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-sm font-bold text-gray-700 ml-1">Email Address</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-brand-orange transition-colors">
                                    <Mail size={20} />
                                </div>
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="block w-full pl-11 pr-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-brand-orange/10 focus:border-brand-orange outline-none transition-all font-medium text-gray-900"
                                    placeholder="admin@test.com"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between items-center ml-1">
                                <label className="text-sm font-bold text-gray-700">Password</label>
                                <button type="button" onClick={() => alert('Please contact your administrator to reset your password.')} className="text-xs font-bold text-brand-orange hover:underline">Forgot?</button>
                            </div>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-brand-orange transition-colors">
                                    <Lock size={20} />
                                </div>
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="block w-full pl-11 pr-4 py-4 bg-white border border-gray-200 rounded-2xl focus:ring-4 focus:ring-brand-orange/10 focus:border-brand-orange outline-none transition-all font-medium text-gray-900"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full btn-primary py-4 rounded-2xl text-lg flex items-center justify-center gap-3 shadow-xl shadow-brand-orange/20 mt-8 disabled:opacity-70"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="animate-spin" size={24} />
                                    <span>Authenticating...</span>
                                </>
                            ) : (
                                <>
                                    <span>Sign In</span>
                                    <ArrowRight size={20} />
                                </>
                            )}
                        </button>
                    </form>

                    <p className="mt-10 text-center text-sm text-gray-400 font-medium">
                        Having trouble logging in? <br className="md:hidden" />
                        <button type="button" onClick={() => alert('Please contact support@visionai.com')} className="text-brand-orange font-bold hover:underline">Contact System Admin</button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
