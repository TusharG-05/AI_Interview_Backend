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
    const audioLevelsRef = useRef(Array(20).fill(10));
    const [, forceVisUpdate] = useState(0); // Force visualizer re-renders
    const questionAudioRef = useRef(null);
    
    // WebRTC Proctoring Refs
    const pcRef = useRef(null); // RTCPeerConnection
    const [webrtcStatus, setWebrtcStatus] = useState('idle'); // idle, connecting, connected, failed
    const [proctoringActive, setProctoringActive] = useState(false);

    // 0. Sync Media Stream to Video Ref
    useEffect(() => {
        if (videoRef.current && mediaStream) {
            videoRef.current.srcObject = mediaStream;
        }
    }, [status, mediaStream]);

    // 1. Verify Token on Mount
    useEffect(() => {
        verifyToken();
        const handleStop = () => stopMedia();
        return handleStop;
    }, [token]);

    // Countdown Effect
    useEffect(() => {
        let timer;
        const updateTimer = () => {
            if (!sessionData?.schedule_time) return;
            const now = new Date();
            const start = new Date(sessionData.schedule_time);
            const diff = start - now;

            if (diff <= 30000 && status === 'waiting') {
                setStatus('selfie');
            }

            if (diff <= 0) {
                if (timer) clearInterval(timer);
                if (status === 'waiting') setStatus('selfie');
                setTimeLeft(0);
            } else {
                setTimeLeft(diff);
            }
        };

        if (status === 'waiting' || status === 'selfie') {
            updateTimer(); // Run once immediately
            timer = setInterval(updateTimer, 1000);
        }
        return () => clearInterval(timer);
    }, [status, sessionData]);

    const verifyToken = async () => {
        try {
            const res = await interviewService.getInterviewAccess(token);
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
        setLoading(true);
        setError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            setMediaStream(stream);
            console.log("Media stream obtained successfully");
            // If we are in 'permission' mode, move to 'ready'
            if (status === 'permission') {
                setStatus('ready');
            }
        } catch (err) {
            console.error("Camera/Mic Permission Error:", err);
            if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                setError("Hardware Error: Camera or Microphone not found. Please connect your hardware.");
            } else if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                setError("Permission Denied: Please enable camera and microphone access in your browser settings.");
            } else {
                setError(`Hardware Access Failed: ${err.message || "Unknown error"}. Please check your browser's site permissions.`);
            }
        } finally {
            setLoading(false);
        }
    };

    const captureSelfie = async () => {
        if (!videoRef.current || !mediaStream) return;

        const interviewId = sessionData?.interview_id;
        if (!interviewId) {
            setError("Session data is missing. Please refresh and try again.");
            console.error("captureSelfie: sessionData.interview_id is missing!", sessionData);
            return;
        }

        setLoading(true);
        setError(null);
        try {
            const canvas = document.createElement('canvas');
            canvas.width = videoRef.current.videoWidth;
            canvas.height = videoRef.current.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoRef.current, 0, 0);

            // Wrap toBlob in a Promise so we can properly await it & catch errors
            const blob = await new Promise((resolve) => {
                canvas.toBlob(resolve, 'image/jpeg', 0.9);
            });

            if (!blob) throw new Error("Failed to capture image from camera.");

            const formData = new FormData();
            formData.append('interview_id', interviewId);
            formData.append('file', blob, 'selfie.jpg');

            console.log(`📸 Uploading selfie for interview_id: ${interviewId}`);
            await interviewService.uploadSelfie(formData);
            console.log("✅ Selfie uploaded successfully.");

            // Streamline: if mic stream is active, skip the separate permission screen
            if (mediaStream.getAudioTracks().length > 0) {
                setStatus('ready');
            } else {
                setStatus('permission');
            }
        } catch (err) {
            console.error("Selfie upload failed:", err);
            const detail = err?.detail || err?.message || "Failed to verify identity. Please try again.";
            setError(detail);
        } finally {
            setLoading(false);
        }
    };

    const stopMedia = () => {
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            setMediaStream(null);
        }
    };

    // WebRTC Proctoring Setup
    const setupWebRTCProctoring = async () => {
        if (!mediaStream || !sessionData) return;

        try {
            setWebrtcStatus('connecting');
            console.log('🎥 Initializing WebRTC proctoring...');

            // Create RTCPeerConnection
            const configuration = {
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' },
                    { urls: 'stun:stun2.l.google.com:19302' }
                ]
            };
            const pc = new RTCPeerConnection(configuration);
            pcRef.current = pc;

            // Add video and audio tracks from mediaStream
            mediaStream.getTracks().forEach(track => {
                pc.addTrack(track, mediaStream);
                console.log(`✅ Added ${track.kind} track to WebRTC`);
            });

            // Handle remote stream (server sends annotated video back)
            pc.ontrack = (event) => {
                console.log('📹 Receiving remote video track from server');
                if (event.track.kind === 'video' && videoRef.current) {
                    const remoteStream = new MediaStream([event.track]);
                    videoRef.current.srcObject = remoteStream;
                }
            };

            // Handle connection state changes
            pc.onconnectionstatechange = () => {
                console.log(`🔗 WebRTC connection state: ${pc.connectionState}`);
                if (pc.connectionState === 'connected' || pc.connectionState === 'completed') {
                    setWebrtcStatus('connected');
                    setProctoringActive(true);
                    console.log('✅ WebRTC proctoring active!');
                } else if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
                    setWebrtcStatus('failed');
                    setProctoringActive(false);
                    console.warn('⚠️ WebRTC connection failed');
                }
            };

            // Create and send offer
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            console.log('📤 Sending WebRTC offer to backend...');
            const response = await interviewService.offerVideoStream(
                offer.sdp,
                sessionData.interview_id
            );

            const answerSdp = response.data.data.sdp;
            const answer = new RTCSessionDescription({
                type: 'answer',
                sdp: answerSdp
            });

            await pc.setRemoteDescription(answer);
            console.log('✅ WebRTC offer/answer handshake complete');
            setWebrtcStatus('connected');
            setProctoringActive(true);

        } catch (err) {
            console.error('❌ WebRTC setup failed:', err);
            setWebrtcStatus('failed');
            setProctoringActive(false);
            setError('Proctoring setup failed. Interview may still proceed.');
        }
    };

    // Cleanup WebRTC on unmount
    useEffect(() => {
        return () => {
            if (pcRef.current) {
                pcRef.current.close();
                console.log('🔌 WebRTC connection closed');
            }
        };
    }, []);

    // 3. Start Interview
    const startInterview = async () => {
        setLoading(true);
        try {
            // Ideally notify backend we started
            await interviewService.startSession(sessionData.interview_id);
            setStatus('live');
            // Initialize WebRTC proctoring
            await setupWebRTCProctoring();
            fetchNextQuestion();
        } catch (err) {
            setError("Failed to start session.");
        } finally {
            setLoading(false);
        }
    };

    // Question timer countdown
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

    // Audio visualizer animation (only during recording)
    useEffect(() => {
        let interval;
        if (recording) {
            interval = setInterval(() => {
                audioLevelsRef.current = audioLevelsRef.current.map(() => Math.random() * 90 + 10);
                forceVisUpdate(n => n + 1);
            }, 120);
        } else {
            audioLevelsRef.current = Array(20).fill(10);
            forceVisUpdate(n => n + 1);
        }
        return () => clearInterval(interval);
    }, [recording]);

    const playQuestionAudio = (audioUrl) => {
        try {
            if (questionAudioRef.current) {
                questionAudioRef.current.pause();
                questionAudioRef.current.src = '';
            }
            const audio = new Audio(audioUrl);
            questionAudioRef.current = audio;
            audio.play().catch(e => console.warn('Audio autoplay blocked:', e));
        } catch (e) {
            console.warn('Could not play question audio:', e);
        }
    };

    // 4. Fetch Question
    const fetchNextQuestion = async () => {
        setLoading(true);
        setQuestion(null);
        try {
            const res = await interviewService.getNextQuestion(sessionData.interview_id);
            console.log('📋 Next question received:', res.data);
            if (res.data.status === 'finished') {
                finishInterview();
            } else {
                console.log('🔄 Setting question:', res.data.text, 'Index:', res.data.question_index);
                setQuestion(res.data);
                const limit = parseInt(res.data.topic?.split('|')[1]) || 60;
                setQTimeLeft(limit);
                // Use server-generated MP3 audio (better quality than browser TTS)
                if (res.data.audio_url) {
                    playQuestionAudio(`${import.meta.env.VITE_API_BASE_URL || '/api'}${res.data.audio_url}`);
                }
            }
        } catch (err) {
            console.error('❌ Failed to load question:', err);
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
                            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/80 backdrop-blur-sm p-6 text-center">
                                {error && (
                                    <div className="mb-6 max-w-sm flex flex-col items-center gap-3 text-red-400 bg-red-400/10 px-4 py-3 rounded-2xl border border-red-400/20">
                                        <AlertCircle size={24} />
                                        <p className="text-sm font-bold leading-tight">{error}</p>
                                    </div>
                                )}
                                <button
                                    onClick={requestPermissions}
                                    disabled={loading}
                                    className="btn-primary py-3 px-8 flex items-center gap-2"
                                >
                                    {loading ? <Loader2 className="animate-spin" /> : <Camera size={20} />}
                                    {error ? "Try Again" : "Enable Camera"}
                                </button>
                                <p className="mt-4 text-xs text-gray-500 max-w-xs leading-relaxed">
                                    Identity verification requires camera access. Please check your browser address bar for blocked icons.
                                </p>
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

                    <p className="text-center text-xs text-gray-500 uppercase tracking-widest font-black">
                        Verification is mandatory before the interview starts.
                        {timeLeft !== null && (
                            <span className="block mt-2 text-brand-orange-light text-[10px] animate-pulse">
                                Starting in {Math.floor(timeLeft / 1000)}s
                            </span>
                        )}
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
                        {/* Proctoring Status Indicator */}
                        <div className="absolute bottom-2 right-2 px-3 py-1.5 bg-black/70 rounded-lg text-xs font-semibold flex items-center gap-2">
                            {proctoringActive ? (
                                <>
                                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                                    <span className="text-emerald-400">Proctoring ON</span>
                                </>
                            ) : webrtcStatus === 'connecting' ? (
                                <>
                                    <div className="w-2 h-2 bg-yellow-500 rounded-full animate-spin" />
                                    <span className="text-yellow-400">Connecting...</span>
                                </>
                            ) : (
                                <>
                                    <div className="w-2 h-2 bg-red-500 rounded-full" />
                                    <span className="text-red-400">Proctoring OFF</span>
                                </>
                            )}
                        </div>
                    </div>

                    <div className="flex-1 bg-gray-900/50 rounded-xl p-4 border border-gray-800">
                        <h4 className="text-white font-bold text-sm mb-3 flex items-center gap-2">
                            <Volume2 size={16} className="text-brand-orange" /> Audio Level
                        </h4>
                        {/* Audio Visualizer */}
                        <div className="flex items-end justify-between h-12 gap-1">
                            {audioLevelsRef.current.map((level, i) => (
                                <div
                                    key={i}
                                    className="w-1.5 bg-brand-orange/50 rounded-full transition-all duration-100"
                                    style={{
                                        height: `${level}%`,
                                        opacity: recording ? 1 : 0.3
                                    }}
                                />
                            ))}
                        </div>
                        <p className="text-xs text-gray-500 mt-4 text-center">
                            {proctoringActive 
                                ? '✓ Face & Gaze Detection Active. Please stay in frame.' 
                                : '⚠ Proctoring connection establishing...'}
                        </p>
                    </div>
                </aside>
            </div>
        </div>
    );
};

export default InterviewSession;
