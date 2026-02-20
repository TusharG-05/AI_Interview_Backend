import React, { useState, useEffect } from 'react';
import {
    Calendar, Search, Filter, ChevronRight, ArrowLeft, Trash2, Video
} from 'lucide-react';
import { format } from 'date-fns';
import { interviewService } from '../services/interviewService';
import { useNavigate } from 'react-router-dom';

const AdminSchedules = () => {
    const navigate = useNavigate();
    const [interviews, setInterviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const res = await interviewService.getInterviews();
            setInterviews(res.data || []);
        } catch (err) {
            setError('Failed to fetch schedules');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this interview schedule?")) return;
        try {
            await interviewService.deleteInterview(id);
            setInterviews(prev => prev.filter(i => i.id !== id));
        } catch (err) {
            console.error("Delete failed", err);
            alert("Failed to delete interview. Be sure it's not live or completed.");
        }
    };

    const filteredInterviews = interviews.filter(i => {
        if (filter === 'all') return true;
        return i.status.toLowerCase() === filter;
    });

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

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 hover:bg-gray-100 rounded-full text-gray-500 transition-colors"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Interview Schedules</h1>
                        <p className="text-gray-500 text-sm">Manage and track all scheduled interview sessions.</p>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex items-center gap-2 bg-white p-1 rounded-xl border border-gray-200 shadow-sm">
                    {['all', 'scheduled', 'completed', 'live'].map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${filter === f
                                ? 'bg-brand-orange text-white shadow-md'
                                : 'text-gray-500 hover:bg-gray-50'
                                }`}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* List */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden min-h-[400px]">
                {loading ? (
                    <div className="flex items-center justify-center h-64 text-gray-400">
                        <div className="w-6 h-6 border-2 border-brand-orange border-t-transparent rounded-full animate-spin mr-3" />
                        Loading schedules...
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-gray-50/50 border-b border-gray-100">
                                <tr>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Candidate</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Time</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {filteredInterviews.length > 0 ? filteredInterviews.map((interview) => (
                                    <tr key={interview.id} className="hover:bg-gray-50/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 bg-brand-orange/5 rounded-full flex items-center justify-center text-brand-orange font-bold text-xs">
                                                    {(interview.candidate?.full_name || 'U').charAt(0)}
                                                </div>
                                                <div>
                                                    <p className="font-semibold text-gray-900 text-sm">{interview.candidate?.full_name || 'Unknown'}</p>
                                                    <p className="text-xs text-gray-400">{interview.candidate?.email || 'No Email'}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <StatusBadge status={interview.status} />
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                                <Calendar size={14} className="text-gray-400" />
                                                {format(new Date(interview.scheduled_at || interview.schedule_time), 'MMM d, h:mm a')}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            {interview.total_score !== null ? (
                                                <button
                                                    onClick={() => navigate(`/interview/result/${interview.id}`)}
                                                    className="font-bold text-gray-900 hover:text-brand-orange transition-colors flex items-center gap-1"
                                                >
                                                    {interview.total_score}%
                                                    <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                                                </button>
                                            ) : (
                                                <span className="text-xs text-gray-300">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                {interview.status.toLowerCase() === 'live' && (
                                                    <button
                                                        onClick={() => navigate(`/admin/ghost/${interview.id}`)}
                                                        className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-orange text-white rounded-lg text-xs font-bold hover:bg-brand-orange-dark shadow-sm transition-all animate-pulse"
                                                    >
                                                        <Video size={14} />
                                                        Watch Live
                                                    </button>
                                                )}
                                                <button
                                                    onClick={() => handleDelete(interview.id)}
                                                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                                >
                                                    <Trash2 size={18} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                )) : (
                                    <tr>
                                        <td colSpan="5" className="px-6 py-12 text-center text-gray-400">
                                            No interviews found matching filter.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminSchedules;
