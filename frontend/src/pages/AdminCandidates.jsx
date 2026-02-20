import React, { useState, useEffect } from 'react';
import { Search, Plus, Edit2, Trash2, Users, AlertCircle, Loader2, User, ChevronLeft, ChevronRight, Mail, Lock } from 'lucide-react';
import { interviewService } from '../services/interviewService';
import { authService } from '../services/authService';

const AdminCandidates = () => {
    const currentUser = authService.getCurrentUser();
    const [candidates, setCandidates] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Pagination & Search
    const [skip, setSkip] = useState(0);
    const limit = 20;
    const [searchTerm, setSearchTerm] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');

    // Modal States
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingCandidate, setEditingCandidate] = useState(null);
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        password: '',
        role: 'candidate'
    });
    const [saving, setSaving] = useState(false);

    // Debounce search
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedSearch(searchTerm);
            setSkip(0); // Reset pagination on new search
        }, 500);
        return () => clearTimeout(handler);
    }, [searchTerm]);

    useEffect(() => {
        fetchCandidates();
    }, [skip, debouncedSearch]);

    const fetchCandidates = async () => {
        try {
            setLoading(true);
            const res = await interviewService.getCandidates(skip, limit, debouncedSearch);
            setCandidates(res.data.items || []);
            setTotal(res.data.total || 0);
            setError(null);
        } catch (err) {
            console.error(err);
            setError("Failed to load candidates");
        } finally {
            setLoading(false);
        }
    };

    const handleOpenModal = (candidate = null) => {
        if (candidate) {
            setEditingCandidate(candidate);
            setFormData({
                full_name: candidate.full_name || '',
                email: candidate.email || '',
                password: '', // Kept empty for edit
                role: 'candidate'
            });
        } else {
            setEditingCandidate(null);
            setFormData({
                full_name: '',
                email: '',
                password: '',
                role: 'candidate'
            });
        }
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setEditingCandidate(null);
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            if (editingCandidate) {
                // Determine update payload
                const updatePayload = {
                    full_name: formData.full_name,
                    email: formData.email,
                    role: formData.role
                };
                if (formData.password) {
                    updatePayload.password = formData.password;
                }
                await interviewService.updateCandidate(editingCandidate.id, updatePayload);
            } else {
                await interviewService.createCandidate(formData);
            }
            handleCloseModal();
            fetchCandidates();
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to save candidate");
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this candidate? This will remove all their interview data.")) return;
        try {
            await interviewService.deleteCandidate(id);
            // If deleting the last item on a page goes back a page
            if (candidates.length === 1 && skip > 0) {
                setSkip(skip - limit);
            } else {
                fetchCandidates();
            }
        } catch (err) {
            alert(err.response?.data?.detail || "Failed to delete candidate");
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-12">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Candidates</h1>
                    <p className="text-gray-500 mt-1">Manage and register interview candidates.</p>
                </div>
                <button
                    onClick={() => handleOpenModal()}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus size={18} />
                    <span>Add Candidate</span>
                </button>
            </div>

            {/* Filters & Search */}
            <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row gap-4 items-center justify-between">
                <div className="relative w-full md:max-w-md group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-brand-orange transition-colors">
                        <Search size={18} />
                    </div>
                    <input
                        type="text"
                        placeholder="Search candidates by name or email..."
                        className="block w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-4 focus:ring-brand-orange/10 focus:border-brand-orange outline-none transition-all font-medium text-gray-900"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="text-sm font-semibold text-gray-500 flex gap-2 items-center">
                    <span className="hidden md:inline">Total Candidates:</span>
                    <span className="text-gray-900 bg-gray-100 px-3 py-1 rounded-full">{total}</span>
                </div>
            </div>

            {/* List */}
            {loading ? (
                <div className="flex flex-col items-center justify-center py-16 gap-4">
                    <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
                    <p className="text-gray-500 font-medium">Loading candidates...</p>
                </div>
            ) : error ? (
                <div className="bg-red-50 text-red-600 p-6 rounded-2xl flex items-center gap-3">
                    <AlertCircle size={24} />
                    <p className="font-semibold">{error}</p>
                </div>
            ) : candidates.length === 0 ? (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-12 text-center">
                    <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center text-blue-500 mx-auto mb-4">
                        <Users size={28} />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">No candidates found</h3>
                    <p className="text-gray-500 max-w-sm mx-auto mb-6">
                        {debouncedSearch ? "Try adjusting your search criteria." : "Start by registering your first candidate manually."}
                    </p>
                    {!debouncedSearch && (
                        <button onClick={() => handleOpenModal()} className="btn-primary">
                            Register Candidate
                        </button>
                    )}
                </div>
            ) : (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden pt-2">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-gray-50/50 border-y border-gray-100/50 hidden md:table-header-group">
                                <tr>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">User</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Email</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Role</th>
                                    <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {candidates.map(candidate => (
                                    <tr key={candidate.id} className="hover:bg-gray-50/50 transition-colors group flex flex-col md:table-row">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3 shrink-0">
                                                <div className="w-10 h-10 rounded-full bg-brand-orange/10 text-brand-orange flex items-center justify-center font-bold">
                                                    {candidate.full_name?.[0]?.toUpperCase() || 'U'}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-gray-900 inline-block">{candidate.full_name || 'Unknown'}</p>
                                                    <p className="text-sm text-gray-500 md:hidden">{candidate.email}</p>
                                                    <p className="text-xs text-brand-orange uppercase font-bold md:hidden mt-0.5">{candidate.role}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 hidden md:table-cell">
                                            <div className="flex items-center gap-2 text-gray-600 font-medium">
                                                <Mail size={16} className="text-gray-400" />
                                                {candidate.email}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 hidden md:table-cell">
                                            <span className={`px-3 py-1 text-xs font-bold uppercase rounded-lg ${candidate.role === 'admin' ? 'bg-blue-50 text-blue-600' : 'bg-gray-100 text-gray-600'}`}>
                                                {candidate.role}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => handleOpenModal(candidate)}
                                                    className="p-2 text-gray-400 hover:text-brand-orange hover:bg-brand-orange/10 rounded-lg transition-colors"
                                                    title="Edit User"
                                                >
                                                    <Edit2 size={16} />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(candidate.id)}
                                                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                                    title="Delete User"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {total > limit && (
                        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50/50">
                            <span className="text-sm font-semibold text-gray-500">
                                Showing {skip + 1} to {Math.min(skip + limit, total)} of {total}
                            </span>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setSkip(Math.max(0, skip - limit))}
                                    disabled={skip === 0}
                                    className="p-2 rounded-xl border border-gray-200 bg-white text-gray-600 disabled:opacity-50 hover:bg-gray-50 transition-colors"
                                >
                                    <ChevronLeft size={18} />
                                </button>
                                <button
                                    onClick={() => setSkip(skip + limit)}
                                    disabled={skip + limit >= total}
                                    className="p-2 rounded-xl border border-gray-200 bg-white text-gray-600 disabled:opacity-50 hover:bg-gray-50 transition-colors"
                                >
                                    <ChevronRight size={18} />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Form Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <h3 className="text-xl font-bold text-gray-900">
                                {editingCandidate ? 'Edit User' : 'Register User'}
                            </h3>
                            <button
                                onClick={handleCloseModal}
                                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                X
                            </button>
                        </div>

                        <div className="p-6 overflow-y-auto">
                            <form id="candidate-form" onSubmit={handleSave} className="space-y-4">
                                {currentUser?.role === 'super_admin' && (
                                    <div>
                                        <label className="block text-sm font-bold text-gray-700 mb-1.5 ml-1">User Role</label>
                                        <select
                                            className="block w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-4 focus:ring-brand-orange/10 focus:border-brand-orange outline-none transition-all font-medium text-gray-900"
                                            value={formData.role}
                                            onChange={e => setFormData({ ...formData, role: e.target.value })}
                                        >
                                            <option value="candidate">Candidate</option>
                                            <option value="admin">Admin</option>
                                            {currentUser?.role === 'super_admin' && <option value="super_admin">Super Admin</option>}
                                        </select>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1.5 ml-1">Full Name</label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-brand-orange transition-colors">
                                            <User size={18} />
                                        </div>
                                        <input
                                            required
                                            type="text"
                                            className="block w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-4 focus:ring-brand-orange/10 focus:border-brand-orange outline-none transition-all font-medium text-gray-900"
                                            placeholder="Jane Doe"
                                            value={formData.full_name}
                                            onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1.5 ml-1">Email Address</label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-brand-orange transition-colors">
                                            <Mail size={18} />
                                        </div>
                                        <input
                                            required
                                            type="email"
                                            className="block w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-4 focus:ring-brand-orange/10 focus:border-brand-orange outline-none transition-all font-medium text-gray-900"
                                            placeholder="jane@example.com"
                                            value={formData.email}
                                            onChange={e => setFormData({ ...formData, email: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-bold text-gray-700 mb-1.5 ml-1">
                                        {editingCandidate ? 'New Password (Optional)' : 'Initial Password'}
                                    </label>
                                    <div className="relative group">
                                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-brand-orange transition-colors">
                                            <Lock size={18} />
                                        </div>
                                        <input
                                            required={!editingCandidate}
                                            type="password"
                                            className="block w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-4 focus:ring-brand-orange/10 focus:border-brand-orange outline-none transition-all font-medium text-gray-900"
                                            placeholder="••••••••"
                                            value={formData.password}
                                            onChange={e => setFormData({ ...formData, password: e.target.value })}
                                        />
                                    </div>
                                    {editingCandidate && (
                                        <p className="text-xs text-gray-500 mt-1 ml-1 font-semibold">Leave blank to keep current password</p>
                                    )}
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
                                form="candidate-form"
                                disabled={saving}
                                className="btn-primary flex items-center gap-2"
                            >
                                {saving ? <><Loader2 size={18} className="animate-spin" /> Saving...</> : 'Save User'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminCandidates;
