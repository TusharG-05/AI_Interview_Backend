import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Search, Plus, MoreVertical, Edit2, Trash2, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { interviewService } from '../services/interviewService';
import { format } from 'date-fns';
import CreatePaperModal from '../components/CreatePaperModal';

const AdminPapers = () => {
    const navigate = useNavigate();
    const [papers, setPapers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [editingPaper, setEditingPaper] = useState(null);
    const [deletingPaperId, setDeletingPaperId] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const res = await interviewService.getPapers();
            setPapers(res.data || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure? This will delete the paper and all its questions.")) return;

        try {
            await interviewService.deletePaper(id);
            setPapers(papers.filter(p => p.id !== id));
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to delete paper");
        }
    };

    const handleUpdate = async (e) => {
        e.preventDefault();
        try {
            await interviewService.updatePaper(editingPaper.id, {
                name: editingPaper.name,
                description: editingPaper.description
            });
            setEditingPaper(null);
            fetchData();
        } catch (err) {
            alert("Failed to update paper");
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Assessment Papers</h1>
                    <p className="text-gray-500 mt-1">Manage your question banks and assessments.</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus size={18} />
                    <span>Create Paper</span>
                </button>
            </div>

            {/* Content */}
            {loading ? (
                <div className="text-center py-12 text-gray-400">Loading papers...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {papers.map(paper => (
                        <div
                            key={paper.id}
                            onClick={() => navigate(`/admin/papers/${paper.id}`, { state: { paper } })}
                            className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm hover:shadow-md hover:border-brand-orange/30 transition-all group relative cursor-pointer"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600">
                                    <BookOpen size={24} />
                                </div>
                                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); setEditingPaper(paper); }}
                                        className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-brand-orange"
                                        title="Edit Paper Details"
                                    >
                                        <Edit2 size={16} />
                                    </button>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleDelete(paper.id); }}
                                        className="p-2 hover:bg-red-50 rounded-lg text-gray-500 hover:text-red-600"
                                        title="Delete Paper"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>

                            <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-brand-orange transition-colors">{paper.name}</h3>
                            <p className="text-gray-500 text-sm mb-4 line-clamp-2 min-h-[40px]">
                                {paper.description || "No description provided."}
                            </p>

                            <div className="flex items-center gap-4 text-xs font-bold text-gray-400 uppercase tracking-wider border-t border-gray-50 pt-4">
                                <span>{paper.question_count} Questions</span>
                                <span className="w-1 h-1 bg-gray-300 rounded-full" />
                                <span>{format(new Date(paper.created_at), 'MMM d, yyyy')}</span>
                            </div>
                        </div>
                    ))}

                    {papers.length === 0 && (
                        <div className="col-span-full py-12 text-center bg-gray-50 rounded-3xl border-2 border-dashed border-gray-200">
                            <p className="text-gray-400">No papers created yet.</p>
                        </div>
                    )}
                </div>
            )}

            {/* Edit Modal (Inline for simplicity) */}
            {editingPaper && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold">Edit Paper</h3>
                            <button onClick={() => setEditingPaper(null)}><X size={20} className="text-gray-400" /></button>
                        </div>
                        <form onSubmit={handleUpdate} className="space-y-4">
                            <div>
                                <label className="text-sm font-bold text-gray-700">Name</label>
                                <input
                                    className="w-full p-3 border rounded-xl mt-1"
                                    value={editingPaper.name}
                                    onChange={e => setEditingPaper({ ...editingPaper, name: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="text-sm font-bold text-gray-700">Description</label>
                                <textarea
                                    className="w-full p-3 border rounded-xl mt-1"
                                    value={editingPaper.description || ''}
                                    onChange={e => setEditingPaper({ ...editingPaper, description: e.target.value })}
                                />
                            </div>
                            <button type="submit" className="btn-primary w-full py-3 rounded-xl font-bold">Save Changes</button>
                        </form>
                    </div>
                </div>
            )}

            <CreatePaperModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onCreated={fetchData}
            />
        </div>
    );
};

export default AdminPapers;
