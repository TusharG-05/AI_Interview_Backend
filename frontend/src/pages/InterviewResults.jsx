import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { interviewService } from '../services/interviewService';
import { ChevronLeft, CheckCircle2, XCircle, Play, Pause, FileText, Clock, Award } from 'lucide-react';
import { format } from 'date-fns';

const InterviewResults = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [playingAudio, setPlayingAudio] = useState(null);

    useEffect(() => {
        const fetchResult = async () => {
            try {
                // If ID is token-like (UUID), it might be from the interview session end
                // But this page expects a numeric ID or we need to handle both
                // For now assuming numeric ID from history or admin list.
                const res = await interviewService.getInterviewResult(id);
                setResult(res.data);
            } catch (err) {
                console.error(err);
                setError("Failed to load interview results.");
            } finally {
                setLoading(false);
            }
        };
        fetchResult();
    }, [id]);

    const toggleAudio = (url) => {
        const audio = document.getElementById('answer-audio');
        if (!audio) return;

        if (playingAudio === url) {
            audio.pause();
            setPlayingAudio(null);
        } else {
            audio.src = url;
            audio.play();
            setPlayingAudio(url);
            audio.onended = () => setPlayingAudio(null);
        }
    };

    if (loading) return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            <div className="w-12 h-12 border-4 border-brand-orange border-t-transparent rounded-full animate-spin" />
            <p className="mt-4 text-gray-500 font-medium">Analyzing Performance...</p>
        </div>
    );

    if (error) return (
        <div className="flex flex-col items-center justify-center min-h-screen text-center p-6">
            <XCircle size={64} className="text-red-500 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900">Error Loading Results</h2>
            <p className="text-gray-500 mt-2 mb-6">{error}</p>
            <button onClick={() => navigate(-1)} className="btn-primary px-8 py-3">Go Back</button>
        </div>
    );

    if (!result) return null;

    return (
        <div className="max-w-5xl mx-auto p-6 md:p-12 space-y-12 animate-in fade-in duration-700">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start gap-6">
                <button
                    onClick={() => navigate(-1)}
                    className="group flex items-center gap-2 text-gray-400 hover:text-brand-orange transition-colors"
                >
                    <div className="p-2 rounded-full bg-gray-50 group-hover:bg-brand-orange/10 transition-colors">
                        <ChevronLeft size={20} />
                    </div>
                    <span className="font-bold">Back to Dashboard</span>
                </button>
                <div className="text-right">
                    <h1 className="text-4xl font-black text-gray-900">{result.interview?.paper?.name || 'Interview Result'}</h1>
                    <p className="text-gray-500 font-medium mt-1">
                        Completed on {format(new Date(result.interview?.end_time || Date.now()), 'PPP p')}
                    </p>
                </div>
            </div>

            {/* Score Card */}
            <div className="relative overflow-hidden rounded-[2.5rem] bg-gray-900 text-white p-12 shadow-2xl">
                <div className="absolute top-0 right-0 w-96 h-96 bg-brand-orange/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-12">
                    <div className="text-center md:text-left space-y-2">
                        <p className="text-brand-orange font-bold tracking-widest uppercase">Overall Score</p>
                        <div className="text-8xl font-black tracking-tighter">
                            {Math.round(result.total_score || 0)}<span className="text-4xl text-gray-600">%</span>
                        </div>
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/10 text-sm font-medium">
                            <Award size={16} className="text-brand-orange" />
                            <span>{result.total_score >= 80 ? 'Excellent Performance' : result.total_score >= 60 ? 'Good Effort' : 'Needs Improvement'}</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-8 md:gap-12">
                        <div className="text-center">
                            <div className="w-16 h-16 mx-auto bg-white/5 rounded-2xl flex items-center justify-center mb-3">
                                <Clock size={32} className="text-blue-400" />
                            </div>
                            <div className="text-3xl font-bold">{result.interview?.duration_minutes || 0}m</div>
                            <div className="text-xs text-gray-400 uppercase font-bold tracking-wider">Duration</div>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 mx-auto bg-white/5 rounded-2xl flex items-center justify-center mb-3">
                                <FileText size={32} className="text-purple-400" />
                            </div>
                            <div className="text-3xl font-bold">{result.interview_response?.length || 0}</div>
                            <div className="text-xs text-gray-400 uppercase font-bold tracking-wider">Questions</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Questions Breakdown */}
            <div className="space-y-8">
                <h2 className="text-2xl font-bold text-gray-900">Detailed Analysis</h2>
                <div className="grid gap-6">
                    {result.interview_response?.map((answer, index) => {
                        const audioUrl = interviewService.getAudioUrl(answer.id);
                        return (
                            <div key={index} className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                                <div className="flex gap-4 mb-6">
                                    <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg bg-gray-100 text-gray-500 font-bold text-sm">
                                        {index + 1}
                                    </span>
                                    <div>
                                        <h3 className="text-lg font-bold text-gray-900">{answer.question?.question_text || answer.question?.content}</h3>
                                        <p className="text-sm text-gray-400 mt-1 font-mono">Topic: {answer.question?.topic?.split('|')[0] || 'General'}</p>
                                    </div>
                                </div>

                                <div className="grid md:grid-cols-2 gap-8">
                                    {/* Transcription */}
                                    <div className="bg-gray-50 p-6 rounded-2xl space-y-4">
                                        <div className="flex items-center justify-between">
                                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Your Answer</h4>
                                            {answer.audio_path && (
                                                <button
                                                    onClick={() => toggleAudio(audioUrl)}
                                                    className="text-brand-orange hover:bg-white p-2 rounded-full transition-all"
                                                >
                                                    {playingAudio === audioUrl ? <Pause size={20} /> : <Play size={20} />}
                                                </button>
                                            )}
                                        </div>
                                        <p className="text-gray-700 leading-relaxed italic">
                                            "{answer.transcribed_text || answer.candidate_answer || 'No transcription available.'}"
                                        </p>
                                    </div>

                                    {/* AI Feedback */}
                                    <div className="space-y-4">
                                        <div>
                                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Relevance Score</h4>
                                            <div className="h-3 w-full bg-gray-100 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-brand-orange rounded-full"
                                                    style={{ width: `${answer.score || 0}%` }}
                                                />
                                            </div>
                                            <div className="text-right text-xs font-bold text-gray-500 mt-1">{Math.round(answer.score || 0)}/100</div>
                                        </div>
                                        <div>
                                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Feedback</h4>
                                            <p className="text-sm text-gray-600">
                                                {answer.feedback || "AI analysis pending..."}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Hidden Audio Element */}
            <audio id="answer-audio" className="hidden" />
        </div>
    );
};

export default InterviewResults;
