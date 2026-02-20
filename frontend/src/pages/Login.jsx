import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, User, ArrowRight, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

const Login = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(null);

    const handleLogin = (role) => {
        setLoading(role);
        // Simulate API delay
        setTimeout(() => {
            const mockUser = {
                id: role === 'admin' ? 1 : 2,
                full_name: role === 'admin' ? 'System Administrator' : 'John Candidate',
                email: role === 'admin' ? 'admin@visionai.com' : 'john@example.com',
                role: role
            };
            localStorage.setItem('token', 'mock-jwt-token');
            localStorage.setItem('user', JSON.stringify(mockUser));
            navigate(`/${role}`);
        }, 1200);
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
                        <span className="font-bold text-3xl tracking-tight">VisionAI</span>
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

                <div className="mt-12 md:mt-0 z-10">
                    <div className="flex gap-4 items-center">
                        <div className="flex -space-x-2">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="w-10 h-10 rounded-full border-2 border-brand-orange bg-gray-200" />
                            ))}
                        </div>
                        <p className="text-sm font-medium">Joined by 10,000+ candidates today</p>
                    </div>
                </div>

                {/* Decorative Circles */}
                <div className="absolute top-[-10%] right-[-10%] w-64 h-64 bg-white/10 rounded-full blur-3xl" />
                <div className="absolute bottom-[10%] left-[-5%] w-48 h-48 bg-black/10 rounded-full blur-2xl" />
            </div>

            {/* Right Side - Login Forms */}
            <div className="md:w-1/2 p-8 md:p-24 flex flex-col justify-center bg-gray-50">
                <div className="max-w-md w-full mx-auto">
                    <div className="mb-12">
                        <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h2>
                        <p className="text-gray-500">Choose your role to continue to the dashboard.</p>
                    </div>

                    <div className="space-y-4">
                        {/* Admin Option */}
                        <motion.div
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className={`p-6 bg-white rounded-2xl border-2 cursor-pointer transition-all duration-300 ${loading === 'admin' ? 'border-brand-orange ring-4 ring-brand-orange/10' : 'border-transparent hover:border-brand-orange/30 shadow-sm hover:shadow-md'
                                }`}
                            onClick={() => !loading && handleLogin('admin')}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 bg-brand-orange/10 rounded-2xl flex items-center justify-center text-brand-orange">
                                        <ShieldCheck size={32} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-xl text-gray-900">Admin Control</h3>
                                        <p className="text-sm text-gray-500">Manage papers and candidates</p>
                                    </div>
                                </div>
                                {loading === 'admin' ? (
                                    <Loader2 className="animate-spin text-brand-orange" />
                                ) : (
                                    <ArrowRight className="text-gray-300 group-hover:text-brand-orange" />
                                )}
                            </div>
                        </motion.div>

                        {/* Candidate Option */}
                        <motion.div
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className={`p-6 bg-white rounded-2xl border-2 cursor-pointer transition-all duration-300 ${loading === 'candidate' ? 'border-brand-orange ring-4 ring-brand-orange/10' : 'border-transparent hover:border-brand-orange/30 shadow-sm hover:shadow-md'
                                }`}
                            onClick={() => !loading && handleLogin('candidate')}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600">
                                        <User size={32} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-xl text-gray-900">Candidate Portal</h3>
                                        <p className="text-sm text-gray-500">View invitations and take tests</p>
                                    </div>
                                </div>
                                {loading === 'candidate' ? (
                                    <Loader2 className="animate-spin text-blue-600" />
                                ) : (
                                    <ArrowRight className="text-gray-300" />
                                )}
                            </div>
                        </motion.div>
                    </div>

                    <div className="mt-12 pt-8 border-t border-gray-200 text-center">
                        <p className="text-sm text-gray-500">
                            Need technical support? <br />
                            <a href="#" className="text-brand-orange font-semibold hover:underline">Contact System Admin</a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
