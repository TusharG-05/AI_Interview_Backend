import React, { useState, useEffect } from 'react';
import { X, Loader2, Calendar, User, BookOpen, Clock, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { interviewService } from '../services/interviewService';

const ScheduleInterviewModal = ({ isOpen, onClose, onScheduled }) => {
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);
    const [papers, setPapers] = useState([]);
    const [candidates, setCandidates] = useState([]);
    const [formData, setFormData] = useState({
        candidate_id: '',
        paper_id: '',
        schedule_time: '',
        duration_minutes: 30
    });
    const [error, setError] = useState(null);

    // Fetch dependencies (papers & candidates) when modal opens
    useEffect(() => {
        if (isOpen) {
            loadDependencies();
        }
    }, [isOpen]);

    const loadDependencies = async () => {
        setFetching(true);
        try {
            const [papersRes, usersRes] = await Promise.all([
                interviewService.getPapers(),
                interviewService.getCandidates(0, 100) // fetch more for selection
            ]);
            setPapers(papersRes.data || []);
            setCandidates(usersRes.data?.items || usersRes.data || []);
        } catch (err) {
            console.error(err);
            setError("Failed to load candidates or papers.");
        } finally {
            setFetching(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Format time to ISO 8601
            const isoTime = new Date(formData.schedule_time).toISOString();

            await interviewService.scheduleInterview({
                ...formData,
                candidate_id: parseInt(formData.candidate_id),
                paper_id: parseInt(formData.paper_id),
                schedule_time: isoTime
            });

            onScheduled();
            onClose();
            // Reset form
            setFormData({ candidate_id: '', paper_id: '', schedule_time: '', duration_minutes: 30 });
        } catch (err) {
            setError(err.message || 'Failed to schedule interview');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden"
                >
                    <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-brand-orange/10 rounded-xl flex items-center justify-center text-brand-orange">
                                <Calendar size={20} />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">Schedule Interview</h3>
                                <p className="text-xs text-gray-500">Assign a paper to a candidate</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full text-gray-400 transition-colors">
                            <X size={20} />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="p-6 space-y-4">
                        {error && (
                            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100 flex items-center gap-2">
                                <span className="font-bold">Error:</span> {error}
                            </div>
                        )}

                        {fetching ? (
                            <div className="py-8 text-center text-gray-400">
                                <Loader2 className="animate-spin mx-auto mb-2" />
                                <p className="text-xs">Loading resources...</p>
                            </div>
                        ) : (
                            <>
                                {/* Candidate Selection */}
                                <div className="space-y-1.5">
                                    <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                        <User size={14} className="text-brand-orange" /> Candidate
                                    </label>
                                    <select
                                        required
                                        className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none bg-white"
                                        value={formData.candidate_id}
                                        onChange={(e) => setFormData({ ...formData, candidate_id: e.target.value })}
                                    >
                                        <option value="">Select a Candidate...</option>
                                        {candidates.map(c => (
                                            <option key={c.id} value={c.id}>{c.full_name} ({c.email})</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Paper Selection */}
                                <div className="space-y-1.5">
                                    <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                        <BookOpen size={14} className="text-brand-orange" /> Assessment Paper
                                    </label>
                                    <select
                                        required
                                        className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none bg-white"
                                        value={formData.paper_id}
                                        onChange={(e) => setFormData({ ...formData, paper_id: e.target.value })}
                                    >
                                        <option value="">Select a Paper...</option>
                                        {papers.map(p => (
                                            <option key={p.id} value={p.id}>{p.name} ({p.question_count} Qs)</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Date & Duration Row */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="text-sm font-bold text-gray-700 flex items-center gap-2">
                                            <Clock size={14} className="text-brand-orange" /> Time
                                        </label>
                                        <input
                                            type="datetime-local"
                                            required
                                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none"
                                            value={formData.schedule_time}
                                            onChange={(e) => setFormData({ ...formData, schedule_time: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-sm font-bold text-gray-700">Duration (Min)</label>
                                        <input
                                            type="number"
                                            min="5"
                                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none"
                                            value={formData.duration_minutes}
                                            onChange={(e) => setFormData({ ...formData, duration_minutes: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div className="pt-4">
                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full btn-primary py-3 rounded-xl flex items-center justify-center gap-2 font-bold"
                                    >
                                        {loading ? <Loader2 className="animate-spin" /> : <CheckCircle2 size={18} />}
                                        {loading ? 'Scheduling...' : 'Confirm Schedule'}
                                    </button>
                                </div>
                            </>
                        )}
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

export default ScheduleInterviewModal;
