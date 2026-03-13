import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle, AlertCircle, Download, Eye, TrendingUp, Users,
  FileText, Clock, BarChart3, Award, Calendar, Play, Volume2
} from 'lucide-react';
import { adminService, interviewService } from '../services/enhancedApi';
import { Button, Card, LoadingSpinner, ErrorAlert, SuccessAlert } from '../components/UI';

/**
 * Enhanced Results and Evaluation Page
 * Professional interface with comprehensive API integration
 */
const InterviewResults = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [interviewResults, setInterviewResults] = useState(null);
  const [interviewId, setInterviewId] = useState(null);

  useEffect(() => {
    // Get interview ID from URL
    const pathParts = window.location.pathname.split('/');
    const id = pathParts[pathParts.length - 1];
    if (id && id !== 'result') {
      setInterviewId(id);
      loadInterviewResults(id);
    }
  }, []);

  const loadInterviewResults = async (id) => {
    try {
      setLoading(true);
      
      const response = await adminService.getResult(id);
      
      if (response.success) {
        setInterviewResults(response.data);
      } else {
        setError(response.message || 'Failed to load interview results');
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to load interview results');
      setLoading(false);
    }
  };

  const downloadReport = async () => {
    if (!interviewResults) return;
    
    try {
      const response = await adminService.getResponseAudio(interviewResults.interview_result.id);
      
      if (response.success) {
        // Create download link
        const blob = new Blob([response.data], { type: 'audio/wav' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `interview_${interviewId}_response.wav`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to download audio:', err);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    if (score >= 4) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreGrade = (score) => {
    if (score >= 9) return 'A+';
    if (score >= 8) return 'A';
    if (score >= 7) return 'B+';
    if (score >= 6) return 'B';
    if (score >= 5) return 'C+';
    if (score >= 4) return 'C';
    if (score >= 3) return 'D';
    return 'F';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading Results..." />
      </div>
    );
  }

  if (error && !interviewResults) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto p-6">
          <ErrorAlert
            error={error}
            onDismiss={() => setError('')}
          />
        </div>
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
              Interview Results
            </motion.h1>
            
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                icon={Download}
                onClick={downloadReport}
                disabled={!interviewResults}
              >
                Download Report
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                icon={BarChart3}
                onClick={() => window.location.href = '/admin/results'}
              >
                All Results
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

      {/* Results Content */}
      {interviewResults && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Interview Overview */}
            <div className="lg:col-span-2">
              <Card title="Interview Overview">
                <div className="space-y-6">
                  {/* Candidate Info */}
                  <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center mb-3">
                        <Users className="text-blue-600 mr-3" size={24} />
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900">
                            {interviewResults.interview.candidate_user?.full_name || 'Unknown Candidate'}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {interviewResults.interview.candidate_user?.email || 'No email'}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      {interviewResults.interview.candidate_user?.profile_image && (
                        <img
                          src={interviewResults.interview.candidate_user.profile_image}
                          alt="Profile"
                          className="w-16 h-16 rounded-full object-cover"
                        />
                      )}
                    </div>
                  </div>

                  {/* Interview Details */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div className="flex items-center text-sm text-gray-600">
                        <Calendar className="mr-2" size={16} />
                        <span>Date:</span>
                      </div>
                      <p className="font-medium text-gray-900">
                        {new Date(interviewResults.interview.schedule_time).toLocaleDateString()}
                      </p>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center text-sm text-gray-600">
                        <Clock className="mr-2" size={16} />
                        <span>Duration:</span>
                      </div>
                      <p className="font-medium text-gray-900">
                        {interviewResults.interview.duration_minutes} minutes
                      </p>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center text-sm text-gray-600">
                        <FileText className="mr-2" size={16} />
                        <span>Paper:</span>
                      </div>
                      <p className="font-medium text-gray-900">
                        {interviewResults.interview.paper?.name || 'No paper'}
                      </p>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center text-sm text-gray-600">
                        <Award className="mr-2" size={16} />
                        <span>Status:</span>
                      </div>
                      <p className="font-medium text-gray-900">
                        {interviewResults.interview.status}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Score Overview */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Score Overview</h4>
                  
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <motion.div
                        initial={{ scale: 0.5 }}
                        animate={{ scale: 1 }}
                        className="text-center"
                      >
                        <div className={`text-3xl font-bold ${getScoreColor(interviewResults.total_score)}`}>
                          {interviewResults.total_score || 0}
                        </div>
                        <div className={`text-lg font-semibold ${getScoreColor(interviewResults.total_score)}`}>
                          {getScoreGrade(interviewResults.total_score)}
                        </div>
                        <p className="text-sm text-gray-600">Total Score</p>
                      </motion.div>
                    </div>
                    
                    <div>
                      <motion.div
                        initial={{ scale: 0.5 }}
                        animate={{ scale: 1 }}
                        className="text-center"
                      >
                        <div className="text-2xl font-bold text-blue-600">
                          {interviewResults.interview_responses?.length || 0}
                        </div>
                        <p className="text-sm text-gray-600">Questions</p>
                      </motion.div>
                    </div>
                    
                    <div>
                      <motion.div
                        initial={{ scale: 0.5 }}
                        animate={{ scale: 1 }}
                        className="text-center"
                      >
                        <div className="text-2xl font-bold text-green-600">
                          {interviewResults.interview_responses?.filter(r => r.score >= 6).length || 0}
                        </div>
                        <p className="text-sm text-gray-600">Correct</p>
                      </motion.div>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Detailed Answers */}
            <div className="lg:col-span-1">
              <Card title="Detailed Answers">
                <div className="space-y-4">
                  {interviewResults.interview_responses?.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <FileText className="mx-auto text-gray-400 mb-2" size={32} />
                      <p>No answers recorded</p>
                    </div>
                  ) : (
                    interviewResults.interview_responses?.map((response, index) => (
                      <motion.div
                        key={response.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="border border-gray-200 rounded-lg p-4 space-y-4"
                      >
                        {/* Question */}
                        <div className="bg-gray-50 rounded p-3">
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="font-medium text-gray-900">
                              Question {response.sort_order + 1}
                            </h5>
                            <div className={`px-2 py-1 rounded text-xs font-medium ${
                              response.score >= 8 ? 'bg-green-100 text-green-800' :
                              response.score >= 6 ? 'bg-yellow-100 text-yellow-800' :
                              response.score >= 4 ? 'bg-orange-100 text-orange-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {response.score || 0} points
                            </div>
                          </div>
                          
                          <div className="text-sm text-gray-700">
                            {response.question?.text || response.question?.code ? (
                              <div>
                                <p className="font-medium mb-2">Question:</p>
                                {response.question.text && (
                                  <p>{response.question.text}</p>
                                )}
                                {response.question.code && (
                                  <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-x-auto">
                                    {response.question.code}
                                  </pre>
                                )}
                              </div>
                            ) : (
                              <p className="text-gray-500">Question not available</p>
                            )}
                          </div>
                        </div>

                        {/* Answer */}
                        <div className="bg-white rounded p-3">
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="font-medium text-gray-900">Candidate Answer</h5>
                            <div className={`px-2 py-1 rounded text-xs font-medium ${
                              response.score >= 8 ? 'bg-green-100 text-green-800' :
                              response.score >= 6 ? 'bg-yellow-100 text-yellow-800' :
                              response.score >= 4 ? 'bg-orange-100 text-orange-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {response.score || 0} points
                            </div>
                          </div>
                          
                          <div className="text-sm text-gray-700">
                            {response.candidate_answer ? (
                              <div>
                                <p className="font-medium mb-2">Answer:</p>
                                <p>{response.candidate_answer}</p>
                              </div>
                            ) : (
                              <p className="text-gray-500">No answer provided</p>
                            )}
                          </div>
                        </div>

                        {/* Feedback */}
                        <div className="bg-blue-50 rounded p-3">
                          <div className="flex items-center mb-2">
                            <Volume2 className="text-blue-600 mr-2" size={16} />
                            <h5 className="font-medium text-blue-900">AI Feedback</h5>
                          </div>
                          
                          <div className="text-sm text-gray-700">
                            {response.feedback ? (
                              <p>{response.feedback}</p>
                            ) : (
                              <p className="text-gray-500">No feedback available</p>
                            )}
                          </div>
                        </div>

                        {/* Audio Playback */}
                        {response.audio_path && (
                          <div className="mt-3">
                            <Button
                              variant="outline"
                              size="sm"
                              icon={Play}
                              onClick={() => {
                                const audio = new Audio(`/api/admin/results/audio/${response.id}`);
                                audio.play();
                              }}
                            >
                              Play Answer
                            </Button>
                          </div>
                        )}
                      </motion.div>
                    ))
                  )}
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewResults;
