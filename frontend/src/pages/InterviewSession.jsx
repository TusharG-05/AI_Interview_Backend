import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Loader2, Mic, Square, CheckCircle2, AlertCircle,
    Camera, Video, Volume2, ArrowRight, Clock, Timer
} from 'lucide-react';
import { interviewService } from '../services/interviewService';

const InterviewSession = () => {
    const { token } = useParams();
    const navigate = useNavigate();

    // State
    const [loading, setLoading] = useState(true);
    const [sessionData, setSessionData] = useState(null);
    const [status, setStatus] = useState('verifying'); // verifying, permission, ready, live, finished, error
    const [question, setQuestion] = useState(null);
    const [recording, setRecording] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [mediaStream, setMediaStream] = useState(null);
    const [audioBlob, setAudioBlob] = useState(null);
    const [error, setError] = useState(null);
    const [timeLeft, setTimeLeft] = useState(null); // ms remaining
    const [qTimeLeft, setQTimeLeft] = useState(0); // seconds remaining for current question

    // Refs
    const videoRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    // 1. Verify Token on Mount
    useEffect(() => {
        verifyToken();
        return () => stopMedia(); // Cleanup on unmount
    }, [token]);

    // Countdown Effect
    useEffect(() => {
        let timer;
        if (status === 'waiting' && sessionData?.schedule_time) {
            timer = setInterval(() => {
                const now = new Date();
                const start = new Date(sessionData.schedule_time);
                const diff = start - now;

                if (diff <= 30000 && status === 'waiting') {
                    setStatus('selfie');
                }

                if (diff <= 0) {
                    clearInterval(timer);
                    if (status === 'waiting') setStatus('selfie');
                } else {
                    setTimeLeft(diff);
                }
            }, 1000);
        }
        return () => clearInterval(timer);
    }, [status, sessionData]);

    const verifyToken = async () => {
        try {
            const res = await interviewService.getInterviewAccess(token);
            setSessionData(res.data);
            setSessionData(res.data);
            if (res.data.message === 'WAIT') {
                setStatus('waiting');
            } else {
                setStatus('selfie');
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Invalid Interview Link");
            setStatus('error');
        } finally {
            setLoading(false);
        }
    };

    // 2. Request Permissions
    const requestPermissions = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            setMediaStream(stream);
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            setStatus('ready');
        } catch (err) {
            setError("Camera and Microphone access is required to proceed.");
        }
    };

    const captureSelfie = async () => {
        if (!videoRef.current || !mediaStream) return;

        setLoading(true);
        try {
            const canvas = document.createElement('canvas');
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoRef.current, 0, 0);

            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('file', blob, 'selfie.jpg');
                await interviewService.uploadSelfie(formData);
                setStatus('permission');
                setLoading(false);
            }, 'image/jpeg', 0.9);
        } catch (err) {
            setError("Failed to verify identity. Please try again.");
            setLoading(false);
        }
    };

    const stopMedia = () => {
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            setMediaStream(null);
        }
    };

    // 3. Start Interview
    const startInterview = async () => {
        setLoading(true);
        try {
            // Ideally notify backend we started
            await interviewService.startSession(sessionData.interview_id);
            setStatus('live');
            fetchNextQuestion();
        } catch (err) {
            setError("Failed to start session.");
        } finally {
            setLoading(false);
        }
    };

    // Countdown Effect
    useEffect(() => {
        let timer;
        if (status === 'live' && question && recording && qTimeLeft > 0) {
            timer = setInterval(() => {
                setQTimeLeft(prev => {
                    if (prev <= 1) {
                        clearInterval(timer);
                        stopRecording();
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }
        return () => clearInterval(timer);
    }, [status, question, recording, qTimeLeft]);

    const speakQuestion = (text) => {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
    };

    // 4. Fetch Question
    const fetchNextQuestion = async () => {
        setLoading(true);
        setQuestion(null);
        try {
            const res = await interviewService.getNextQuestion(sessionData.interview_id);
            if (res.data.status === 'finished') {
                finishInterview();
            } else {
                setQuestion(res.data);
                const limit = parseInt(res.data.topic?.split('|')[1]) || 60;
                setQTimeLeft(limit);
                speakQuestion(res.data.content);
            }
        } catch (err) {
            setError("Failed to load question.");
        } finally {
            setLoading(false);
        }
    };

    // 5. Audio Recording Logic
    const startRecording = () => {
        if (!mediaStream) return;

        chunksRef.current = [];
        const recorder = new MediaRecorder(mediaStream);

        recorder.ondataavailable = (e) => {
            if (e.data.size > 0) chunksRef.current.push(e.data);
        };

        recorder.onstop = () => {
            const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
            setAudioBlob(blob);
        };

        recorder.start();
        setRecording(true);
        mediaRecorderRef.current = recorder;
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && recording) {
            mediaRecorderRef.current.stop();
            setRecording(false);
        }
    };

    // 6. Submit Answer
    const submitAnswer = async () => {
        if (!audioBlob) return;
        setSubmitting(true);

        const formData = new FormData();
        formData.append('interview_id', sessionData.interview_id);
        formData.append('question_id', question.question_id);
        formData.append('audio', audioBlob, 'answer.webm');

        try {
            await interviewService.submitAnswerAudio(formData);
            setAudioBlob(null);
            chunksRef.current = [];
            fetchNextQuestion(); // Proceed to next
        } catch (err) {
            alert("Failed to submit answer. Please try again.");
            console.error(err);
        } finally {
            setSubmitting(false);
        }
    };

    // 7. Finish
    const finishInterview = async () => {
        try {
            await interviewService.finishInterview(sessionData.interview_id);
            stopMedia();
            setStatus('finished');
        } catch (err) {
            console.error("Failed to mark finished", err);
        }
    };

    // --- RENDERERS ---

    if (loading && !question && status !== 'live') return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
        </div>
    );

    if (status === 'selfie') {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-4 text-white">
                <div className="max-w-2xl w-full space-y-8 animate-in fade-in zoom-in">
                    <div className="text-center">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-orange/10 text-brand-orange rounded-full text-xs font-bold uppercase tracking-widest mb-4 border border-brand-orange/20">
                            <span className="w-2 h-2 bg-brand-orange rounded-full animate-pulse" />
                            Identity Verification
                        </div>
                        <h1 className="text-3xl font-black mb-2">Live Selfie Check</h1>
                        <p className="text-gray-400">Please look at the camera to verify your identity for proctoring.</p>
                    </div>

                    <div className="relative aspect-video bg-black rounded-3xl overflow-hidden border border-gray-700 shadow-2xl ring-1 ring-white/10">
                        <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover transform scale-x-[-1]" />
                        {!mediaStream && (
                            <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm">
                                <button onClick={requestPermissions} className="btn-primary py-3 px-8">
                                    Enable Camera
                                </button>
                            </div>
                        )}
                        <div className="absolute bottom-6 inset-x-0 flex justify-center">
                            {mediaStream && (
                                <button
                                    onClick={captureSelfie}
                                    disabled={loading}
                                    className="bg-brand-orange hover:bg-brand-orange-dark text-white p-5 rounded-full shadow-2xl shadow-brand-orange/40 transition-all hover:scale-110 active:scale-95 disabled:opacity-50"
                                >
                                    {loading ? <Loader2 className="animate-spin" size={32} /> : <Camera size={32} />}
                                </button>
                            )}
                        </div>
                    </div>

                    <p className="text-center text-xs text-gray-500">
                        Verification is mandatory before the interview starts.
                        Remaining Time: {Math.floor(timeLeft / 1000)}s
                    </p>
                </div>
            </div>
        );
    }

    if (status === 'error') return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            <div className="max-w-md w-full bg-white p-8 rounded-2xl shadow-xl text-center">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-gray-900 mb-2">
                    {error.includes("completed") ? "Interview Finished" :
                        error.includes("expired") ? "Link Expired" : "Access Denied"}
                </h2>
                <p className="text-gray-500 mb-6">{error}</p>
                <button onClick={() => navigate('/login')} className="btn-primary w-full">Return to Login</button>
            </div>
        </div>
    );

    if (status === 'waiting') {
        const seconds = Math.floor((timeLeft / 1000) % 60);
        const minutes = Math.floor((timeLeft / 1000 / 60) % 60);
        const hours = Math.floor((timeLeft / (1000 * 60 * 60)) % 24);

        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white p-4">
                <div className="max-w-md w-full bg-gray-800 p-10 rounded-[2.5rem] shadow-2xl text-center border border-gray-700">
                    <div className="w-20 h-20 bg-brand-orange/20 rounded-3xl flex items-center justify-center text-brand-orange mx-auto mb-8 animate-pulse">
                        <Timer size={40} />
                    </div>
                    <h2 className="text-3xl font-black mb-2 tracking-tight">Hang Tight!</h2>
                    <p className="text-gray-400 mb-8">Your interview is scheduled and will begin shortly.</p>

                    <div className="grid grid-cols-3 gap-4 mb-10">
                        <div className="bg-gray-900/50 p-4 rounded-2xl border border-gray-700">
                            <div className="text-3xl font-black text-brand-orange">{hours}</div>
                            <div className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">Hours</div>
                        </div>
                        <div className="bg-gray-900/50 p-4 rounded-2xl border border-gray-700">
                            <div className="text-3xl font-black text-brand-orange">{minutes}</div>
                            <div className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">Mins</div>
                        </div>
                        <div className="bg-gray-900/50 p-4 rounded-2xl border border-gray-700">
                            <div className="text-3xl font-black text-brand-orange">{seconds}</div>
                            <div className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">Secs</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 justify-center text-sm text-gray-500 bg-gray-900/30 py-3 rounded-xl border border-gray-700/50">
                        <Clock size={16} />
                        <span>Starts at {new Date(sessionData?.schedule_time).toLocaleTimeString()}</span>
                    </div>
                </div>
            </div>
        );
    }

    if (status === 'finished') return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            <div className="max-w-md w-full bg-white p-8 rounded-2xl shadow-xl text-center animate-in fade-in zoom-in">
                <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Comparison Complete</h2>
                <p className="text-gray-500 mb-6">Your responses have been recorded and submitted for AI analysis.</p>
                <button onClick={() => navigate('/candidate')} className="btn-primary w-full">Back to Dashboard</button>
            </div>
        </div>
    );

    if (status === 'permission' || status === 'ready') return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-4 text-white">
            <div className="max-w-2xl w-full space-y-8">
                <div className="text-center">
                    <h1 className="text-3xl font-bold mb-2">System Check</h1>
                    <p className="text-gray-400">We need to check your camera and microphone before starting.</p>
                </div>

                <div className="relative aspect-video bg-black rounded-2xl overflow-hidden border border-gray-700 shadow-2xl">
                    <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover transform scale-x-[-1]" />
                    {!mediaStream && (
                        <div className="absolute inset-0 flex items-center justify-center flex-col gap-4 bg-gray-800/50">
                            <div className="flex gap-4">
                                <span className="p-4 bg-gray-700 rounded-full"><Camera size={32} /></span>
                                <span className="p-4 bg-gray-700 rounded-full"><Mic size={32} /></span>
                            </div>
                            <p className="font-medium text-gray-300">Grant permissions to continue</p>
                        </div>
                    )}
                </div>

                <div className="flex gap-4 justify-center">
                    {status === 'permission' ? (
                        <button onClick={requestPermissions} className="btn-primary py-3 px-8 text-lg">
                            Enable Camera & Microphone
                        </button>
                    ) : (
                        <button onClick={startInterview} className="btn-primary py-3 px-12 text-lg bg-emerald-500 hover:bg-emerald-600 border-emerald-500">
                            Start Interview Now
                        </button>
                    )}
                </div>
            </div>
        </div>
    );

    // LIVE INTERVIEW UI
    return (
        <div className="min-h-screen bg-gray-100 flex flex-col">
            {/* Header */}
            <header className="bg-white px-6 py-4 flex justify-between items-center shadow-sm z-10">
                <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" />
                    <span className="font-bold text-red-600 text-sm tracking-wider">LIVE SESSION</span>
                </div>
                <div className="text-sm font-medium text-gray-500">
                    Question {question?.question_index || 1} / {question?.total_questions || '-'}
                </div>
            </header>

            <div className="flex-1 flex flex-col md:flex-row h-[calc(100vh-64px)] overflow-hidden">
                {/* Main Content: Question & Controls */}
                <main className="flex-1 p-8 flex flex-col justify-center max-w-4xl mx-auto w-full">
                    <div className="mb-12">
                        <h2 className="text-2xl md:text-4xl font-bold text-gray-900 leading-tight">
                            {question?.text || "Loading Question..."}
                        </h2>
                    </div>

                    {/* Audio Waveform / Controls Placeholder */}
                    <div className="flex flex-col items-center gap-6">
                        {audioBlob ? (
                            <div className="flex flex-col items-center gap-4 animate-in fade-in slide-in-from-bottom-4">
                                <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100 text-emerald-700 flex items-center gap-3">
                                    <CheckCircle2 />
                                    <span className="font-bold">Answer Recorded</span>
                                    <span className="text-xs text-emerald-600 ml-2">({(audioBlob.size / 1024).toFixed(1)} KB)</span>
                                </div>
                                <div className="flex gap-3">
                                    <button
                                        onClick={() => setAudioBlob(null)}
                                        className="px-6 py-3 rounded-xl font-bold text-gray-500 hover:bg-gray-200 transition-colors"
                                    >
                                        Retake
                                    </button>
                                    <button
                                        onClick={submitAnswer}
                                        disabled={submitting}
                                        className="btn-primary px-8 py-3 rounded-xl flex items-center gap-2 font-bold"
                                    >
                                        {submitting ? <Loader2 className="animate-spin" /> : <ArrowRight />}
                                        Submit Answer
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center gap-6">
                                {recording && (
                                    <div className="flex flex-col items-center gap-2">
                                        <div className={`text-4xl font-black ${qTimeLeft < 10 ? 'text-red-500 animate-pulse' : 'text-gray-900'}`}>
                                            {Math.floor(qTimeLeft / 60)}:{(qTimeLeft % 60).toString().padStart(2, '0')}
                                        </div>
                                        <p className="text-[10px] uppercase font-bold text-gray-400 tracking-widest">Time Remaining</p>
                                    </div>
                                )}
                                <div className="flex flex-col items-center gap-4">
                                    <button
                                        onClick={recording ? stopRecording : startRecording}
                                        className={`w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-xl ${recording
                                            ? 'bg-red-500 text-white scale-110 ring-4 ring-red-200'
                                            : 'bg-brand-orange text-white hover:bg-brand-orange-dark hover:scale-105'
                                            }`}
                                    >
                                        {recording ? <Square fill="currentColor" size={32} /> : <Mic size={36} />}
                                    </button>
                                    <p className="text-gray-500 font-medium">
                                        {recording ? "Recording... Click to Stop" : "Tap to Answer"}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </main>

                {/* Sidebar: Proctoring Feed */}
                <aside className="w-full md:w-80 bg-black p-4 flex flex-col">
                    <div className="relative aspect-video bg-gray-900 rounded-xl overflow-hidden border border-gray-800 shadow-lg mb-4">
                        <video
                            ref={videoRef}
                            autoPlay
                            muted
                            playsInline
                            className="w-full h-full object-cover transform scale-x-[-1]"
                        />
                        <div className="absolute top-2 left-2 px-2 py-0.5 bg-red-600/80 rounded text-[10px] font-bold text-white flex items-center gap-1">
                            <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" /> REC
                        </div>
                    </div>

                    <div className="flex-1 bg-gray-900/50 rounded-xl p-4 border border-gray-800">
                        <h4 className="text-white font-bold text-sm mb-3 flex items-center gap-2">
                            <Volume2 size={16} className="text-brand-orange" /> Audio Level
                        </h4>
                        {/* Fake Audio Visualizer */}
                        <div className="flex items-end justify-between h-12 gap-1">
                            {[...Array(20)].map((_, i) => (
                                <div
                                    key={i}
                                    className="w-1.5 bg-brand-orange/50 rounded-full transition-all duration-75"
                                    style={{
                                        height: recording ? `${Math.random() * 100}%` : '10%',
                                        opacity: recording ? 1 : 0.3
                                    }}
                                />
                            ))}
                        </div>
                        <p className="text-xs text-gray-500 mt-4 text-center">
                            Proctoring Active. Please stay in frame.
                        </p>
                    </div>
                </aside>
            </div>
        </div>
    );
};

export default InterviewSession;
