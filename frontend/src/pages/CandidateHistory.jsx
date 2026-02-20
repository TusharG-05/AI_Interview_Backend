import React, { useState, useEffect } from 'react';
import { Calendar, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { interviewService } from '../services/interviewService';

import { useNavigate } from 'react-router-dom';

const CandidateHistory = () => {
    const navigate = useNavigate();
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await interviewService.getMyInterviews();
                // Filter for completed/expired
                const past = (res.data || []).filter(i =>
                    i.status && ['completed', 'expired', 'cancelled'].includes(i.status.toLowerCase())
                );
                setHistory(past);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    const StatusIcon = ({ status }) => {
        if (!status) return <AlertCircle className="text-gray-400" size={20} />;
        switch (status.toLowerCase()) {
            case 'completed': return <CheckCircle2 className="text-emerald-500" size={20} />;
            case 'expired': return <Clock className="text-gray-400" size={20} />;
            default: return <AlertCircle className="text-red-500" size={20} />;
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Interview History</h1>
                <p className="text-gray-500 mt-1">Review your past assessments and results.</p>
            </div>

            {loading ? (
                <div className="text-center py-12 text-gray-400">Loading history...</div>
            ) : (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                    {history.length > 0 ? (
                        <div className="divide-y divide-gray-100">
                            {history.map((interview) => (
                                <div
                                    key={interview.interview_id}
                                    className="p-6 border-b border-gray-100 last:border-0 flex items-center justify-between group"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${interview.status === 'completed' ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-400'
                                            }`}>
                                            <StatusIcon status={interview.status} />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-gray-900">
                                                {interview.paper_name || 'Assessment Interview'}
                                            </h3>
                                            <p className="text-sm text-gray-500">
                                                {interview.date}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="text-right">
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${interview.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-400'
                                            }`}>
                                            {interview.status}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="p-12 text-center text-gray-400">
                            No past interviews found.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default CandidateHistory;
