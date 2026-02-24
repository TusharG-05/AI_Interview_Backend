import React, { useState, useEffect } from 'react';
import {
    Users, BookOpen, Calendar, Clock, Plus,
    Search, Filter, ChevronRight, AlertCircle, CheckCircle2, MoreVertical
} from 'lucide-react';
import { format } from 'date-fns';
import { interviewService } from '../services/interviewService';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import CreatePaperModal from '../components/CreatePaperModal';
import ScheduleInterviewModal from '../components/ScheduleInterviewModal';

const AdminDashboard = () => {
    const navigate = useNavigate();
    const [interviews, setInterviews] = useState([]);
    const [papers, setPapers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isPaperModalOpen, setIsPaperModalOpen] = useState(false);
    const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);

    const [liveCount, setLiveCount] = useState(0);

    useEffect(() => {
        const load = async () => {
            const count = await fetchData();
            setLiveCount(count);
        };
        load();

        // Poll every 30s
        const interval = setInterval(async () => {
            try {
                const res = await interviewService.getLiveStatus();
                setLiveCount(res.data?.length || 0);
            } catch (e) {
                console.warn('Live status poll failed:', e);
            }
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [interviewsRes, papersRes, liveRes] = await Promise.all([
                interviewService.getInterviews(),
                interviewService.getPapers(),
                interviewService.getLiveStatus()
            ]);
            setInterviews(interviewsRes.data || []);
            setPapers(papersRes.data || []);

            // Store live count for stats
            const liveCount = liveRes.data?.length || 0;
            return liveCount;
        } catch (err) {
            setError('Failed to fetch dashboard data');
            console.error(err);
            return 0;
        } finally {
            setLoading(false);
        }
    };

    const stats = [
        { name: 'Total Interviews', value: interviews.length, icon: Calendar, color: 'bg-brand-orange/10 text-brand-orange' },
        { name: 'Active Papers', value: papers.length, icon: BookOpen, color: 'bg-blue-50 text-blue-600' },
        { name: 'Live Now', value: liveCount, icon: Clock, color: 'bg-emerald-50 text-emerald-600 animate-pulse' },
    ];

    if (loading) return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
            <div className="w-12 h-12 border-4 border-brand-orange border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 font-medium tracking-wide">Synthesizing Dashboard...</p>
        </div>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Modals */}
            <CreatePaperModal
                isOpen={isPaperModalOpen}
                onClose={() => setIsPaperModalOpen(false)}
                onCreated={fetchData}
            />
            <ScheduleInterviewModal
                isOpen={isScheduleModalOpen}
                onClose={() => setIsScheduleModalOpen(false)}
                onScheduled={fetchData}
            />

            {/* Welcome Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
                    <p className="text-gray-500 mt-1">Manage your interview pipeline and assessment papers.</p>
                </div>
                <button
                    onClick={() => setIsScheduleModalOpen(true)}
                    className="btn-primary flex items-center gap-2 shadow-lg shadow-brand-orange/20"
                >
                    <Plus size={18} />
                    <span>New Interview</span>
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {stats.map((stat) => (
                    <motion.div
                        key={stat.name}
                        whileHover={{ y: -4 }}
                        className="card flex items-center gap-6"
                    >
                        <div className={`p-4 rounded-2xl ${stat.color}`}>
                            <stat.icon size={28} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">{stat.name}</p>
                            <p className="text-3xl font-bold text-gray-900 mt-1">{stat.value}</p>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Main Content Areas */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Recent Interviews Table */}
                <div className="xl:col-span-2 space-y-4">
                    <div className="flex justify-between items-center px-2">
                        <h2 className="text-xl font-bold text-gray-800">Recent Interviews</h2>
                        <button
                            onClick={() => navigate('/admin/schedules')}
                            className="text-brand-orange text-sm font-semibold hover:underline"
                        >
                            View All
                        </button>
                    </div>

                    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-gray-50/50 border-b border-gray-100">
                                    <tr>
                                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Candidate</th>
                                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Scheduled</th>
                                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                                        <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider"></th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50">
                                    {interviews.length > 0 ? interviews
                                        .sort((a, b) => new Date(b.schedule_time || b.scheduled_at) - new Date(a.schedule_time || a.scheduled_at))
                                        .slice(0, 5)
                                        .map((interview) => (
                                        <tr key={interview.id} className="hover:bg-gray-50/50 transition-colors group">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-9 h-9 bg-brand-orange/5 rounded-full flex items-center justify-center text-brand-orange font-bold text-xs border border-brand-orange/10">
                                                        {(interview.candidate?.full_name || 'U').charAt(0)}
                                                    </div>
                                                    <div>
                                                        <p className="font-semibold text-gray-900">{interview.candidate?.full_name || 'Unknown'}</p>
                                                        <p className="text-xs text-gray-400">{interview.candidate?.email || 'N/A'}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <StatusBadge status={interview.status} />
                                            </td>
                                            <td className="px-6 py-4">
                                                <p className="text-sm text-gray-600">{format(new Date(interview.scheduled_at || interview.schedule_time), 'MMM d, h:mm a')}</p>
                                            </td>
                                            <td className="px-6 py-4">
                                                {interview.total_score !== null && interview.total_score !== undefined ? (
                                                    <div className="flex items-center gap-1.5">
                                                        <span className="font-bold text-gray-900">{interview.total_score}</span>
                                                        <span className="text-xs text-gray-400">/ 100</span>
                                                    </div>
                                                ) : (
                                                    <span className="text-xs text-gray-300 italic">No Score</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button className="p-2 text-gray-400 hover:text-brand-orange hover:bg-brand-orange/5 rounded-lg">
                                                    <ChevronRight size={18} />
                                                </button>
                                            </td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="5" className="px-6 py-12 text-center text-gray-400 bg-white">
                                                No interviews scheduled yet.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Papers Quick List */}
                <div className="space-y-4">
                    <div className="flex justify-between items-center px-2">
                        <h2 className="text-xl font-bold text-gray-800">Question Papers</h2>
                        <button
                            onClick={() => setIsPaperModalOpen(true)}
                            className="text-brand-orange text-sm font-semibold hover:underline flex items-center gap-1"
                        >
                            <Plus size={14} /> New
                        </button>
                    </div>

                    <div className="space-y-3">
                        {papers.slice(0, 4).map((paper) => (
                            <div key={paper.id} className="p-4 bg-white border border-gray-100 rounded-xl shadow-sm hover:border-brand-orange/30 transition-all cursor-pointer group">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="font-bold text-gray-900 group-hover:text-brand-orange transition-colors">{paper.name}</h3>
                                        <p className="text-xs text-gray-500 mt-1">{paper.question_count} Questions • Created {format(new Date(paper.created_at), 'MMM d')}</p>
                                    </div>
                                    <div className="p-1 px-2 bg-gray-50 rounded text-[10px] font-bold text-gray-400 uppercase tracking-tighter">
                                        {paper.description || 'No Description'}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {papers.length === 0 && (
                            <div className="p-8 text-center bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl">
                                <BookOpen size={32} className="mx-auto text-gray-300 mb-2" />
                                <p className="text-sm text-gray-400">Add assessment papers to begin scheduling.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

// Inline Component for Badge
const StatusBadge = ({ status }) => {
    const styles = {
        scheduled: 'bg-blue-50 text-blue-600 border-blue-100',
        invited: 'bg-purple-50 text-purple-600 border-purple-100',
        live: 'bg-brand-orange/10 text-brand-orange border-brand-orange/20',
        completed: 'bg-emerald-50 text-emerald-600 border-emerald-100',
        cancelled: 'bg-red-50 text-red-600 border-red-100',
        expired: 'bg-gray-50 text-gray-600 border-gray-100'
    };

    const current = styles[status?.toLowerCase()] || styles.scheduled;

    return (
        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${current}`}>
            {status}
        </span>
    );
};

export default AdminDashboard;
