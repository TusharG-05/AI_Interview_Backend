import React, { useState, useEffect } from 'react';
import {
    Calendar, Clock, CheckCircle2, ChevronRight, Play, ExternalLink,
    History as HistoryIcon, User, AlertCircle
} from 'lucide-react';
import { format } from 'date-fns';
import { interviewService } from '../services/interviewService';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const CandidateDashboard = () => {
    const navigate = useNavigate();
    const [invitations, setInvitations] = useState([]);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [invitesRes, historyRes] = await Promise.all([
                interviewService.getMyInterviews(),
                interviewService.getHistory()
            ]);
            // Filter invites for non-completed
            const active = (invitesRes.data || []).filter(i =>
                i.status && !['completed', 'expired', 'cancelled'].includes(i.status.toLowerCase())
            );
            setInvitations(active);

            // Filter history for completed/expired
            const past = (invitesRes.data || []).filter(i =>
                i.status && ['completed', 'expired', 'cancelled'].includes(i.status.toLowerCase())
            );
            // If getHistory returns duplicate or specific structure, rely on it, 
            // but for now reusing getMyInterviews logic or just using what's there if distinct.
            // Assuming historyRes might be different or same endpoint. 
            // The previous code used interviewService.getHistory(), let's trust it but fall back to filtered active.

            // Actually, let's just use what was returned but filter invites to clean up the UI
            setHistory(historyRes.data || past);
        } catch (err) {
            console.error('Failed to fetch candidate data', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
            <div className="w-12 h-12 border-4 border-brand-orange border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 font-medium font-inter">Syncing Invitation Portal...</p>
        </div>
    );

    return (
        <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">

            {/* Active Invitations */}
            <section className="space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-brand-orange/10 rounded-xl flex items-center justify-center text-brand-orange">
                        <Calendar size={24} />
                    </div>
                    <h2 className="text-2xl font-extrabold text-gray-900 tracking-tight">Active Invitations</h2>
                </div>

                <div className="space-y-4">
                    {invitations.length > 0 ? invitations.map((invite) => (
                        <motion.div
                            key={invite.interview_id}
                            whileHover={{ scale: 1.01 }}
                            className="p-8 bg-white border border-gray-100 rounded-3xl shadow-xl shadow-gray-200/50 flex flex-col md:flex-row justify-between items-center gap-8 relative overflow-hidden"
                        >
                            {/* Highlight background */}
                            <div className="absolute top-0 left-0 w-2 h-full bg-brand-orange" />

                            <div className="flex-1 space-y-2">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="px-2 py-0.5 bg-brand-orange/10 text-brand-orange text-[10px] font-bold uppercase rounded-md">New Request</span>
                                    <span className="text-xs text-gray-400 italic">Token: {invite.interview_id}</span>
                                </div>
                                <h3 className="text-2xl font-bold text-gray-900">{invite.paper_name}</h3>
                                <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-gray-500">
                                    <div className="flex items-center gap-2 text-sm">
                                        <Clock size={16} className="text-brand-orange" />
                                        <span>{format(new Date(invite.date || invite.schedule_time), 'EEEE, MMMM do')}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm">
                                        <User size={16} className="text-brand-orange" />
                                        <span>at {format(new Date(invite.date || invite.schedule_time), 'p')}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex shrink-0 gap-3">
                                <button
                                    onClick={() => navigate(`/interview/${invite.interview_id}`)}
                                    className="btn-primary py-3 px-8 text-lg flex items-center gap-2"
                                >
                                    <Play size={20} fill="currentColor" />
                                    Start Now
                                </button>
                            </div>
                        </motion.div>
                    )) : (
                        <div className="p-12 text-center bg-gray-50 border-2 border-dashed border-gray-200 rounded-[2.5rem] flex flex-col items-center gap-4">
                            <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center text-gray-300">
                                <AlertCircle size={32} />
                            </div>
                            <div>
                                <p className="text-lg font-bold text-gray-800">No Pending Invites</p>
                                <p className="text-gray-500 mt-1 max-w-xs">You're all caught up. New interview requests will appear here when scheduled by an admin.</p>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            {/* Recent Activity / History */}
            <section className="space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600">
                        <HistoryIcon size={24} />
                    </div>
                    <div className="flex-1 flex justify-between items-center">
                        <h2 className="text-2xl font-extrabold text-gray-900 tracking-tight">Recent Activity</h2>
                        <button
                            onClick={() => navigate('/candidate/history')}
                            className="text-brand-orange text-sm font-bold hover:underline"
                        >
                            View All
                        </button>
                    </div>
                </div>

                <div className="bg-white border border-gray-100 rounded-[2rem] shadow-sm overflow-hidden">
                    <div className="divide-y divide-gray-50">
                        {history.length > 0 ? history.slice(0, 3).map((item) => (
                            <div
                                key={item.interview_id}
                                className="p-6 flex items-center justify-between hover:bg-gray-50/50 transition-colors group"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-gray-100 text-gray-500 shadow-inner">
                                        <CheckCircle2 size={24} />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-gray-900">{item.paper_name}</h4>
                                        <p className="text-xs text-gray-500 uppercase font-bold tracking-tight">{item.date}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="px-3 py-1 bg-gray-100 text-gray-400 text-[10px] font-bold uppercase rounded-md tracking-wider">
                                        {item.status || 'FINISHED'}
                                    </span>
                                    <ChevronRight size={20} className="text-gray-300 group-hover:text-brand-orange transition-colors" />
                                </div>
                            </div>
                        )) : (
                            <p className="p-12 text-center text-gray-400 italic">No historical data available.</p>
                        )}
                    </div>
                </div>
            </section>

            {/* Tips / Promo Section */}
            <section className="p-10 bg-gradient-to-br from-brand-orange to-brand-orange-dark rounded-[2.5rem] text-white flex flex-col md:flex-row items-center gap-8 shadow-2xl shadow-brand-orange/30">
                <div className="space-y-4">
                    <h3 className="text-3xl font-black">Prepare for Success</h3>
                    <p className="text-white/80 max-w-md text-lg">
                        Our AI analysis looks for gaze stability, verbal clarity, and technical accuracy. Make sure you are in a well-lit environment.
                    </p>
                    <button className="bg-white text-brand-orange px-6 py-2.5 rounded-full font-bold text-sm tracking-wide shadow-xl flex items-center gap-2 hover:bg-gray-100 transition-colors">
                        Read Proctoring Guide <ExternalLink size={16} />
                    </button>
                </div>
                <div className="md:ml-auto w-32 h-32 bg-white/10 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
                    <CheckCircle2 size={64} className="text-white/20" />
                </div>
            </section>
        </div>
    );
};

export default CandidateDashboard;
