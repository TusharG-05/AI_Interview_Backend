import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Mic, MicOff, Camera, CameraOff, Upload, Send, Clock,
  AlertCircle, CheckCircle, FileText, Volume2, Monitor, Play,
  Pause, Square, Code, Type, Loader2, Eye, EyeOff
} from 'lucide-react';
import { interviewService, candidateService } from '../services/enhancedApi';
import { Button, Card, LoadingSpinner, ErrorAlert, SuccessAlert, FileUpload, Textarea } from '../components/UI';

/**
 * Enhanced Interview Interface
 * Professional interface with complete API integration
 */
const InterviewSession = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [interviewData, setInterviewData] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [answer, setAnswer] = useState('');
  const [timeLeft, setTimeLeft] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [hasSelfie, setHasSelfie] = useState(false);
  const [warningCount, setWarningCount] = useState(0);
  const [warnings, setWarnings] = useState([]);
  
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Get interview token from URL
  const getTokenFromUrl = () => {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
  };

  useEffect(() => {
    const token = getTokenFromUrl();
    if (token) {
      loadInterviewData(token);
    } else {
      setError('Invalid interview link');
      setLoading(false);
    }
  }, []);

  const loadInterviewData = async (token) => {
    try {
      setLoading(true);
      
      const response = await interviewService.accessInterview(token);
      
      if (response.success) {
        setInterviewData(response.data);
        setWarningCount(response.data.warning_count || 0);
        setWarnings(response.data.warnings || []);
        
        // Check if selfie is required
        if (response.data.candidate_user?.profile_image) {
          setHasSelfie(true);
        }
        
        // Load first question
        await loadNextQuestion(response.data.id);
        
        setLoading(false);
      } else {
        setError(response.message || 'Failed to load interview');
        setLoading(false);
      }
    } catch (err) {
      setError(err.message || 'Failed to load interview');
      setLoading(false);
    }
  };

  const loadNextQuestion = async (interviewId) => {
    try {
      const response = await interviewService.getNextQuestion(interviewId);
      
      if (response.success) {
        setCurrentQuestion(response.data);
        setAnswer(''); // Clear previous answer
        setTimeLeft(90); // Reset timer for new question
      }
    } catch (err) {
      console.error('Failed to load next question:', err);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true, 
        video: false 
      });
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      setError('Failed to start recording');
      console.error('Recording error:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Create audio blob
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      submitAudioAnswer(audioBlob);
    }
  };

  const submitAudioAnswer = async (audioBlob) => {
    if (!currentQuestion || !interviewData) return;
    
    try {
      setLoading(true);
      
      const formData = new FormData();
      formData.append('interview_id', interviewData.id);
      formData.append('question_id', currentQuestion.question?.id);
      formData.append('audio', audioBlob, 'audio.wav');
      
      const response = await interviewService.submitAnswerAudio(
        interviewData.id, 
        currentQuestion.question?.id, 
        audioBlob
      );
      
      if (response.success) {
        setSuccess('Audio answer submitted successfully!');
        await loadNextQuestion(interviewData.id);
      } else {
        setError(response.message || 'Failed to submit audio answer');
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to submit audio answer');
      setLoading(false);
    }
  };

  const submitTextAnswer = async () => {
    if (!currentQuestion || !interviewData) return;
    
    try {
      setLoading(true);
      
      const response = await interviewService.submitAnswerText(
        interviewData.id,
        currentQuestion.question?.id,
        answer
      );
      
      if (response.success) {
        setSuccess('Answer submitted successfully!');
        await loadNextQuestion(interviewData.id);
      } else {
        setError(response.message || 'Failed to submit answer');
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to submit answer');
      setLoading(false);
    }
  };

  const submitSelfie = async (file) => {
    try {
      setLoading(true);
      
      const response = await interviewService.uploadSelfie(interviewData.id, file);
      
      if (response.success) {
        setSuccess('Selfie uploaded successfully!');
        setHasSelfie(true);
      } else {
        setError(response.message || 'Failed to upload selfie');
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to upload selfie');
      setLoading(false);
    }
  };

  const finishInterview = async () => {
    if (!interviewData) return;
    
    try {
      setLoading(true);
      
      const response = await interviewService.finishInterview(interviewData.id);
      
      if (response.success) {
        setSuccess('Interview completed successfully!');
        setTimeout(() => {
          window.location.href = `/interview/result/${interviewData.id}`;
        }, 2000);
      } else {
        setError(response.message || 'Failed to finish interview');
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to finish interview');
      setLoading(false);
    }
  };

  // Timer effect
  useEffect(() => {
    if (timeLeft > 0) {
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
      return () => clearInterval(timer);
    }
  }, [timeLeft]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading Interview..." />
      </div>
    );
  }

  if (error && !interviewData) {
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <motion.h1
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-2xl font-bold text-gray-900"
            >
              AI Interview Session
            </motion.h1>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full ${
                  interviewData?.status === 'LIVE' ? 'bg-green-500' : 'bg-gray-400'
                }`} />
                <span className="ml-2 text-sm text-gray-600">
                  {interviewData?.status === 'LIVE' ? 'Live' : 'Offline'}
                </span>
              </div>
              
              <div className="text-sm text-gray-600">
                Time: <span className="font-medium">{Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}</span>
              </div>
              
              <div className="text-sm text-gray-600">
                Warnings: <span className="font-medium text-red-600">{warningCount}</span>/3
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Success Alert */}
      {success && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
          <SuccessAlert
            message={success}
            onDismiss={() => setSuccess('')}
          />
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
          <ErrorAlert
            error={error}
            onDismiss={() => setError('')}
          />
        </div>
      )}

      {/* Main Interview Content */}
      {interviewData && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Question Panel */}
            <div className="lg:col-span-2">
              <Card className="h-full">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Question {currentQuestion?.question?.sort_order + 1 || 1}
                  </h3>
                  <div className="flex items-center space-x-2">
                    {currentQuestion?.question?.audio_path && (
                      <Button
                        variant="outline"
                        size="sm"
                        icon={Play}
                        onClick={() => {
                          const audio = new Audio(`/api/interview/audio/question/${currentQuestion.question.id}`);
                          audio.play();
                        }}
                      >
                        Play Audio
                      </Button>
                    )}
                  </div>
                </div>
                
                <div className="space-y-6">
                  {/* Question Text */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h4 className="font-medium text-gray-900 mb-3">
                      {currentQuestion?.question?.text || 'No question available'}
                    </h4>
                    {currentQuestion?.question?.code && (
                      <div className="mt-4 p-4 bg-gray-900 rounded-lg overflow-x-auto">
                        <pre className="text-green-400 text-sm">
                          {currentQuestion.question.code}
                        </pre>
                      </div>
                    )}
                  </div>

                  {/* Answer Input */}
                  {currentQuestion?.question?.type === 'TEXT' && (
                    <div>
                      <Textarea
                        label="Your Answer"
                        placeholder="Type your answer here..."
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                        rows={6}
                        className="min-h-[150px]"
                      />
                      
                      <div className="flex justify-end mt-4">
                        <Button
                          onClick={submitTextAnswer}
                          loading={loading}
                          disabled={!answer.trim()}
                          icon={Send}
                        >
                          Submit Answer
                        </Button>
                      </div>
                    </div>
                  )}

                  {currentQuestion?.question?.type === 'AUDIO' && (
                    <div>
                      <div className="text-center mb-4">
                        <Button
                          variant={isRecording ? 'danger' : 'primary'}
                          size="lg"
                          icon={isRecording ? MicOff : Mic}
                          onClick={isRecording ? stopRecording : startRecording}
                          className="w-full h-16"
                        >
                          {isRecording ? 'Stop Recording' : 'Start Recording'}
                        </Button>
                      </div>
                      
                      {isRecording && (
                        <div className="flex items-center justify-center mt-4">
                          <Volume2 className="text-red-600 animate-pulse mr-2" size={20} />
                          <span className="text-red-600 font-medium">Recording...</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </Card>
            </div>

            {/* Side Panel */}
            <div className="space-y-6">
              {/* Selfie Upload */}
              {!hasSelfie && (
                <Card title="Identity Verification">
                  <div className="text-center mb-4">
                    <Camera className="mx-auto text-gray-400 mb-2" size={32} />
                    <p className="text-sm text-gray-600 mb-4">
                      Upload your selfie for identity verification
                    </p>
                  </div>
                  
                  <FileUpload
                    label="Select Selfie"
                    onFileSelect={submitSelfie}
                    accept="image/*"
                    loading={loading}
                    error={error.toLowerCase().includes('selfie')}
                  />
                </Card>
              )}

              {/* Interview Info */}
              <Card title="Interview Information">
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-700">Status</span>
                    <span className={`text-sm font-bold ${
                      interviewData.status === 'LIVE' ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {interviewData.status}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-700">Candidate</span>
                    <span className="text-sm text-gray-900">
                      {interviewData.candidate_user?.full_name || 'Loading...'}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-700">Paper</span>
                    <span className="text-sm text-gray-900">
                      {interviewData.paper?.name || 'No paper assigned'}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-700">Duration</span>
                    <span className="text-sm text-gray-900">
                      {interviewData.duration_minutes} minutes
                    </span>
                  </div>
                </div>
              </Card>

              {/* Actions */}
              <Card title="Actions">
                <div className="space-y-3">
                  <Button
                    variant="outline"
                    icon={Eye}
                    onClick={() => window.location.href = `/admin/ghost/${interviewData.id}`}
                    className="w-full"
                  >
                    Proctoring View
                  </Button>
                  
                  <Button
                    variant="danger"
                    icon={Square}
                    onClick={finishInterview}
                    loading={loading}
                    className="w-full"
                  >
                    Finish Interview
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewSession;
