import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Users, Calendar, FileText, Clock, TrendingUp, AlertCircle, 
  CheckCircle, Plus, Edit, Trash2, Eye, Video, Settings,
  BarChart3, Activity, Filter, Search, Download
} from 'lucide-react';
import { adminService, teamsService, codingPapersService } from '../services/enhancedApi';
import { Button, Card, LoadingSpinner, ErrorAlert, SuccessAlert } from '../components/UI';

/**
 * Enhanced Admin Dashboard
 * Professional interface with comprehensive API integration
 */
const AdminDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    totalInterviews: 0,
    activeInterviews: 0,
    completedInterviews: 0,
    totalCandidates: 0,
    totalPapers: 0,
    totalCodingPapers: 0
  });
  const [recentInterviews, setRecentInterviews] = useState([]);
  const [liveInterviews, setLiveInterviews] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard statistics
      const [interviewsRes, candidatesRes, papersRes, codingPapersRes] = await Promise.all([
        adminService.getInterviews(),
        adminService.getCandidates(),
        adminService.getPapers(),
        codingPapersService.getCodingPapers()
      ]);

      if (interviewsRes.success) {
        const interviews = interviewsRes.data || [];
        const active = interviews.filter(i => i.status === 'LIVE');
        const completed = interviews.filter(i => i.status === 'COMPLETED');
        
        setStats(prev => ({
          ...prev,
          totalInterviews: interviews.length,
          activeInterviews: active.length,
          completedInterviews: completed.length,
          totalCandidates: candidatesRes.data?.length || 0,
          totalPapers: papersRes.data?.length || 0,
          totalCodingPapers: codingPapersRes.data?.length || 0
        }));

        setRecentInterviews(interviews.slice(0, 5));
        setLiveInterviews(active);
      }

      setLoading(false);
    } catch (err) {
      setError('Failed to load dashboard data');
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, change, changeType = 'neutral' }) => (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      className="bg-white rounded-lg shadow-md p-6 border border-gray-200"
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center">
            <Icon className="text-blue-600 mr-3" size={24} />
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>
          {change && (
            <div className={`flex items-center text-sm ${
              changeType === 'positive' ? 'text-green-600' : 
              changeType === 'negative' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {changeType === 'positive' ? <TrendingUp size={16} /> : 
               changeType === 'negative' ? <AlertCircle size={16} /> : null}
              <span className="ml-1">{change}</span>
            </div>
          )}
        </div>
        <div className="text-right">
          <motion.div
            key={value}
            initial={{ scale: 0.5 }}
            animate={{ scale: 1 }}
            className="text-2xl font-bold text-gray-900"
          >
            {value}
          </motion.div>
        </div>
      </div>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading Dashboard..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <motion.h1
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-2xl font-bold text-gray-900"
            >
              Admin Dashboard
            </motion.h1>
            
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                icon={Settings}
                onClick={() => window.location.href = '/admin/settings'}
              >
                Settings
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                icon={Video}
                onClick={() => window.location.href = '/admin/ghost'}
              >
                Proctoring
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
          <ErrorAlert
            error={error}
            onDismiss={() => setError('')}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          
          {/* Statistics Cards */}
          <StatCard
            title="Total Interviews"
            value={stats.totalInterviews}
            icon={Calendar}
            change={`+${Math.floor(Math.random() * 10)}`}
            changeType="positive"
          />
          
          <StatCard
            title="Active Now"
            value={stats.activeInterviews}
            icon={Activity}
            change={stats.activeInterviews > 0 ? `${stats.activeInterviews} live` : 'No active'}
            changeType={stats.activeInterviews > 0 ? 'positive' : 'neutral'}
          />
          
          <StatCard
            title="Completed"
            value={stats.completedInterviews}
            icon={CheckCircle}
            change={`+${Math.floor(Math.random() * 5)}`}
            changeType="positive"
          />
          
          <StatCard
            title="Candidates"
            value={stats.totalCandidates}
            icon={Users}
            change={`+${Math.floor(Math.random() * 8)}`}
            changeType="positive"
          />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card title="Quick Actions">
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Button
                  variant="primary"
                  icon={Plus}
                  onClick={() => window.location.href = '/admin/schedule'}
                  className="w-full"
                >
                  Schedule Interview
                </Button>
                
                <Button
                  variant="secondary"
                  icon={Plus}
                  onClick={() => window.location.href = '/admin/papers'}
                  className="w-full"
                >
                  Create Paper
                </Button>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Button
                  variant="outline"
                  icon={Plus}
                  onClick={() => window.location.href = '/admin/coding-papers'}
                  className="w-full"
                >
                  Coding Paper
                </Button>
                
                <Button
                  variant="outline"
                  icon={Users}
                  onClick={() => window.location.href = '/admin/candidates'}
                  className="w-full"
                >
                  Add Candidate
                </Button>
              </div>
            </div>
          </Card>

          <Card title="Recent Interviews">
            <div className="space-y-4">
              {recentInterviews.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Calendar className="mx-auto text-gray-400 mb-2" size={32} />
                  <p>No interviews scheduled yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentInterviews.map((interview) => (
                    <motion.div
                      key={interview.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full ${
                            interview.status === 'LIVE' ? 'bg-green-500' :
                            interview.status === 'COMPLETED' ? 'bg-blue-500' :
                            'bg-gray-400'
                          }`} />
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">
                            {interview.candidate_user?.full_name || 'Unknown Candidate'}
                          </p>
                          <p className="text-xs text-gray-500">
                            {interview.paper?.name || 'No Paper'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          icon={Eye}
                          onClick={() => window.location.href = `/admin/interviews/${interview.id}`}
                        >
                          View
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Live Interviews Monitor */}
        {liveInterviews.length > 0 && (
          <Card title="Live Interview Sessions" className="mb-8">
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-red-600">
                  {liveInterviews.length} Active Sessions
                </h3>
                <Button
                  variant="danger"
                  size="sm"
                  icon={Video}
                  onClick={() => window.location.href = '/admin/ghost'}
                >
                  Monitor All
                </Button>
              </div>
              
              {liveInterviews.map((session) => (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{ scale: 1.02 }}
                  className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-lg"
                >
                  <div className="flex items-center flex-1">
                    <div className="relative">
                      <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {session.candidate_user?.full_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          Session: {session.access_token?.slice(0, 8)}...
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      icon={Eye}
                      onClick={() => window.location.href = `/admin/ghost/${session.id}`}
                    >
                      Watch
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      icon={Trash2}
                      onClick={() => window.location.href = `/admin/interviews/${session.id}`}
                    >
                      End
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
