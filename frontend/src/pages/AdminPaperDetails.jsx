import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Plus, Edit2, Trash2, BookOpen, Clock, FileAudio, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { interviewService } from '../services/interviewService';
import { format } from 'date-fns';

const AdminPaperDetails = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    // Check if we received the paper object from the navigation state to avoid an unnecessary API call
    const initialPaper = location.state?.paper || null;

    const [paper, setPaper] = useState(initialPaper);
    const [loading, setLoading] = useState(!initialPaper);
    const [error, setError] = useState(null);

    // Modal States
    const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false);
    const [editingQuestion, setEditingQuestion] = useState(null);
    const [questionForm, setQuestionForm] = useState({
        content: '',
        topic: '',
        time_limit: 60, // Default 60 seconds
        difficulty: 'Medium',
        marks: 1,
        response_type: 'audio'
    });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (!initialPaper) {
            fetchPaperDetails();
        }
    }, [id]);

    const fetchPaperDetails = async () => {
        try {
            setLoading(true);
            const res = await interviewService.getPaper(id);
            setPaper(res.data);
            setError(null);
        } catch (err) {
            console.error(err);
            setError("Failed to load paper details");
        } finally {
            setLoading(false);
        }
    };

    const handleOpenModal = (question = null) => {
        if (question) {
            setEditingQuestion(question);
            setQuestionForm({
                content: question.content,
                topic: question.topic || '',
                time_limit: parseInt(question.topic?.split('|')[1]) || 60,
                difficulty: question.difficulty || 'Medium',
                marks: question.marks || 1,
                response_type: question.response_type || 'audio'
            });
        } else {
            setEditingQuestion(null);
            setQuestionForm({
                content: '',
                topic: '',
                time_limit: 60,
                difficulty: 'Medium',
                marks: 1,
                response_type: 'audio'
            });
        }
        setIsQuestionModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsQuestionModalOpen(false);
        setEditingQuestion(null);
    };

    const handleSaveQuestion = async (e) => {
        e.preventDefault();
        const payload = {
            ...questionForm,
            topic: `${questionForm.topic.split('|')[0] || ''}|${questionForm.time_limit}`
        };
        try {
            if (editingQuestion) {
                await interviewService.updateQuestion(editingQuestion.id, payload);
            } else {
                await interviewService.addQuestion(id, payload);
            }
            handleCloseModal();
            fetchPaperDetails(); // Refresh list
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to save question");
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteQuestion = async (qId) => {
        if (!window.confirm("Are you sure you want to delete this question?")) return;
        try {
            await interviewService.deleteQuestion(qId);
            fetchPaperDetails(); // Refresh list
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to delete question");
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
                <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
                <p className="text-gray-500 font-medium">Loading paper details...</p>
            </div>
        );
    }

    if (error || !paper) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center">
                <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center text-red-500 mb-2">
                    <AlertCircle size={32} />
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Paper Not Found</h2>
                <p className="text-gray-500 max-w-md">{error}</p>
                <button onClick={() => navigate('/admin/papers')} className="btn-primary mt-4">
                    Back to Papers
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-12">
            {/* Header / Breadcrumb */}
            <div>
                <button
                    onClick={() => navigate('/admin/papers')}
                    className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-gray-900 transition-colors mb-4"
                >
                    <ArrowLeft size={16} /> Back to Papers
                </button>
                <div className="flex justify-between items-start">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
                                <BookOpen size={20} />
                            </div>
                            <h1 className="text-3xl font-bold text-gray-900">{paper.name}</h1>
                        </div>
                        <p className="text-gray-500">{paper.description || "No description provided."}</p>
                    </div>
                    <button
                        onClick={() => handleOpenModal()}
                        className="btn-primary flex items-center gap-2 shadow-sm"
                    >
                        <Plus size={18} />
                        <span>Add Question</span>
                    </button>
                </div>
            </div>

            {/* Questions List */}
            <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
                    <h2 className="text-lg font-bold text-gray-900">Questions ({paper.questions?.length || 0})</h2>
                </div>

                <div className="divide-y divide-gray-50">
                    {paper.questions && paper.questions.length > 0 ? (
                        paper.questions.map((q, index) => (
                            <div key={q.id} className="p-6 hover:bg-gray-50/50 transition-colors group">
                                <div className="flex justify-between items-start gap-6">
                                    <div className="flex gap-4 flex-1">
                                        <div className="w-8 h-8 rounded-full bg-brand-orange/10 text-brand-orange flex items-center justify-center font-bold text-sm shrink-0">
                                            {index + 1}
                                        </div>
                                        <div className="flex-1 space-y-3">
                                            <p className="text-gray-900 font-medium text-lg leading-snug">
                                                {q.content}
                                            </p>
                                            <div className="flex flex-wrap items-center gap-3">
                                                <span className="px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide bg-gray-100 text-gray-600">
                                                    {q.topic?.split('|')[0] || 'General'}
                                                </span>
                                                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide bg-amber-50 text-amber-600">
                                                    <Clock size={14} />
                                                    {q.topic?.split('|')[1] || '60'}s
                                                </span>
                                                <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide
                                                    ${q.difficulty === 'Easy' ? 'bg-emerald-50 text-emerald-600' :
                                                        q.difficulty === 'Hard' ? 'bg-red-50 text-red-600' :
                                                            'bg-blue-50 text-blue-600'}`}
                                                >
                                                    {q.difficulty}
                                                </span>
                                                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide bg-purple-50 text-purple-600">
                                                    {q.response_type === 'audio' ? <FileAudio size={14} /> : React.Fragment}
                                                    {q.response_type === 'text' ? <FileText size={14} /> : React.Fragment}
                                                    {q.response_type === 'both' ? <><FileAudio size={12} />+<FileText size={12} /></> : React.Fragment}
                                                    {q.response_type}
                                                </span>
                                                <span className="text-xs font-bold text-gray-400">
                                                    {q.marks} Mark{q.marks !== 1 && 's'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                                        <button
                                            onClick={() => handleOpenModal(q)}
                                            className="p-2 text-gray-400 hover:text-brand-orange hover:bg-brand-orange/10 rounded-lg transition-colors"
                                            title="Edit Question"
                                        >
                                            <Edit2 size={18} />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteQuestion(q.id)}
                                            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                            title="Delete Question"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="p-12 text-center">
                            <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <BookOpen size={24} className="text-gray-300" />
                            </div>
                            <h3 className="text-lg font-bold text-gray-900 mb-1">No Questions Yet</h3>
                            <p className="text-gray-500 mb-6 max-w-sm mx-auto">This assessment paper is currently empty. Add questions manually to start building your assessment.</p>
                            <button onClick={() => handleOpenModal()} className="btn-primary">
                                Add First Question
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Add/Edit Question Modal */}
            {isQuestionModalOpen && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <h3 className="text-xl font-bold text-gray-900">
                                {editingQuestion ? 'Edit Question' : 'Add New Question'}
                            </h3>
                            <button
                                onClick={handleCloseModal}
                                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                X
                            </button>
                        </div>

                        <div className="p-6 overflow-y-auto">
                            <form id="question-form" onSubmit={handleSaveQuestion} className="space-y-5">
                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1.5">Question Content *</label>
                                    <textarea
                                        required
                                        className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none transition-all min-h-[120px] resize-y"
                                        placeholder="E.g., Explain the difference between React Native and standard React."
                                        value={questionForm.content}
                                        onChange={e => setQuestionForm({ ...questionForm, content: e.target.value })}
                                    />
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1.5">Topic / Category</label>
                                        <input
                                            type="text"
                                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none transition-all"
                                            placeholder="E.g., Frontend, System Design"
                                            value={questionForm.topic.split('|')[0]}
                                            onChange={e => setQuestionForm({ ...questionForm, topic: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1.5">Time Limit (Seconds)</label>
                                        <input
                                            type="number"
                                            min="10"
                                            max="600"
                                            required
                                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none transition-all"
                                            value={questionForm.time_limit}
                                            onChange={e => setQuestionForm({ ...questionForm, time_limit: parseInt(e.target.value) || 60 })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1.5">Marks</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="100"
                                            required
                                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none transition-all"
                                            value={questionForm.marks}
                                            onChange={e => setQuestionForm({ ...questionForm, marks: parseInt(e.target.value) || 1 })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1.5">Difficulty</label>
                                        <select
                                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none transition-all bg-white"
                                            value={questionForm.difficulty}
                                            onChange={e => setQuestionForm({ ...questionForm, difficulty: e.target.value })}
                                        >
                                            <option value="Easy">Easy</option>
                                            <option value="Medium">Medium</option>
                                            <option value="Hard">Hard</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1.5">Expected Response Type</label>
                                        <select
                                            className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange outline-none transition-all bg-white"
                                            value={questionForm.response_type}
                                            onChange={e => setQuestionForm({ ...questionForm, response_type: e.target.value })}
                                        >
                                            <option value="audio">Audio (Spoken)</option>
                                            <option value="text">Text (Written code/essay)</option>
                                            <option value="both">Both</option>
                                        </select>
                                    </div>
                                </div>
                            </form>
                        </div>

                        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex justify-end gap-3 rounded-b-2xl">
                            <button
                                type="button"
                                onClick={handleCloseModal}
                                className="px-5 py-2.5 rounded-xl font-bold text-gray-600 hover:bg-gray-200 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                form="question-form"
                                disabled={saving}
                                className="btn-primary flex items-center gap-2"
                            >
                                {saving ? <><Loader2 size={18} className="animate-spin" /> Saving...</> : 'Save Question'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminPaperDetails;
