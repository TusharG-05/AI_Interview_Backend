import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, Video, Mic, Shield, User,
    AlertTriangle, Loader2, Eye, EyeOff
} from 'lucide-react';
import { interviewService } from '../services/interviewService';

const AdminGhostMode = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState('initializing'); // initializing, connecting, live, error
    const [error, setError] = useState(null);
    const [candidateData, setCandidateData] = useState(null);

    const videoRef = useRef(null);
    const pcRef = useRef(null);

    useEffect(() => {
        setupGhostMode();
        return () => {
            if (pcRef.current) pcRef.current.close();
        };
    }, [id]);

    const setupGhostMode = async () => {
        try {
            setStatus('connecting');
            setError(null);

            // 1. Create Peer Connection
            const pc = new RTCPeerConnection({
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' },
                    { urls: 'stun:stun2.l.google.com:19302' }
                ]
            });
            pcRef.current = pc;

            // 2. Handle incoming tracks
            pc.ontrack = (event) => {
                console.log('📹 Admin received track:', event.track.kind);
                if (videoRef.current && event.streams[0]) {
                    videoRef.current.srcObject = event.streams[0];
                    setStatus('live');
                }
            };

            // 3. Handle connection state changes
            pc.onconnectionstatechange = () => {
                console.log(`🔗 Admin WebRTC connection state: ${pc.connectionState}`);
                if (pc.connectionState === 'failed') {
                    setError('Connection failed. Retrying...');
                    setTimeout(() => setupGhostMode(), 2000);
                }
            };

            // 4. Create Offer (Recv-Only)
            pc.addTransceiver('video', { direction: 'recvonly' });
            pc.addTransceiver('audio', { direction: 'recvonly' });

            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            console.log('📤 Sending ghost mode watch request...');
            // 5. Send to Backend
            const res = await interviewService.watchInterview(id, {
                sdp: pc.localDescription.sdp,
                type: pc.localDescription.type
            });

            console.log('📥 Watch response:', res.data);

            if (res.data.status === 'WAITING_FOR_CANDIDATE') {
                setStatus('waiting');
                console.log('⏳ Waiting for candidate to connect...');
                // Retry after 3 seconds
                setTimeout(() => setupGhostMode(), 3000);
            } else {
                // 6. Set Remote Answer
                await pc.setRemoteDescription(new RTCSessionDescription({
                    sdp: res.data.sdp,
                    type: res.data.type
                }));
                console.log('✅ Ghost mode connection established');
            }

        } catch (err) {
            console.error("Ghost Mode Error:", err);
            setError(`Failed to establish live connection: ${err.message}`);
            setStatus('error');
        }
    };

    return (
        <div className="min-h-screen bg-gray-950 text-white flex flex-col">
            {/* Top Bar */}
            <div className="h-16 border-b border-gray-800 flex items-center justify-between px-6 bg-black/50 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/admin/schedules')}
                        className="p-2 hover:bg-gray-800 rounded-full transition-colors"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-brand-orange/20 rounded-lg flex items-center justify-center text-brand-orange">
                            <Shield size={18} />
                        </div>
                        <div>
                            <h2 className="text-sm font-bold">Ghost Mode</h2>
                            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Silent Proctoring</p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border border-gray-800 ${status === 'live' ? 'bg-red-500/10 text-red-500 border-red-500/20' : 'bg-gray-800 text-gray-500'
                        }`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${status === 'live' ? 'bg-red-500 animate-pulse' : 'bg-gray-500'}`} />
                        {status === 'live' ? 'Live Session' : 'Offline'}
                    </div>
                </div>
            </div>

            {/* Main View */}
            <div className="flex-1 flex flex-col md:flex-row p-6 gap-6 overflow-hidden">
                {/* Primary Stream */}
                <div className="flex-1 relative bg-black rounded-3xl border border-gray-800 shadow-2xl overflow-hidden group">
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        className="w-full h-full object-contain"
                    />

                    {/* Overlays */}
                    {status === 'connecting' && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-950/80 backdrop-blur-md">
                            <Loader2 className="w-12 h-12 text-brand-orange animate-spin mb-4" />
                            <p className="text-gray-400 font-bold tracking-tight">Establishing Secure Tunnel...</p>
                        </div>
                    )}

                    {status === 'waiting' && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-950/80 backdrop-blur-md">
                            <div className="w-16 h-16 bg-brand-orange/10 rounded-2xl flex items-center justify-center text-brand-orange mb-4">
                                <Video size={32} />
                            </div>
                            <h3 className="text-xl font-bold mb-1">Waiting for Candidate</h3>
                            <p className="text-gray-500 text-sm">Session initialized. Stream will appear once candidate connects.</p>
                        </div>
                    )}

                    {status === 'error' && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-red-950/20 backdrop-blur-md p-6 text-center">
                            <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
                            <h3 className="text-xl font-bold mb-2">Connection Failed</h3>
                            <p className="text-red-200/60 max-w-md mb-6">{error}</p>
                            <button onClick={setupGhostMode} className="btn-primary bg-red-600 border-red-600 px-8">Retry Connection</button>
                        </div>
                    )}

                    <div className="absolute top-6 left-6 flex gap-2">
                        <span className="px-3 py-1 bg-black/60 backdrop-blur-md rounded-lg text-xs font-bold flex items-center gap-2 border border-white/10">
                            <Eye size={14} className="text-brand-orange" /> Silent Observer
                        </span>
                    </div>
                </div>

                {/* Info Panel */}
                <div className="w-full md:w-80 space-y-6">
                    <div className="bg-gray-900/50 border border-gray-800 rounded-3xl p-6 backdrop-blur-md">
                        <h3 className="text-xs font-black text-gray-500 uppercase tracking-widest mb-6">Session Info</h3>

                        <div className="space-y-4">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 bg-gray-800 rounded-xl flex items-center justify-center text-gray-500">
                                    <User size={20} />
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-tighter">Candidate ID</p>
                                    <p className="font-bold"># {id}</p>
                                </div>
                            </div>

                            <div className="p-4 bg-gray-800/50 rounded-2xl border border-white/5 space-y-4">
                                <div>
                                    <div className="flex justify-between text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
                                        <span>Proctoring Health</span>
                                        <span className="text-brand-orange">98%</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-gray-700 rounded-full overflow-hidden">
                                        <div className="h-full bg-brand-orange w-[98%]" />
                                    </div>
                                </div>

                                <div className="flex gap-2">
                                    <div className="flex-1 bg-green-500/10 border border-green-500/20 py-2 rounded-lg text-center">
                                        <p className="text-[10px] font-bold text-green-500 uppercase">Video</p>
                                        <p className="text-[8px] text-green-500/60">ACTIVE</p>
                                    </div>
                                    <div className="flex-1 bg-green-500/10 border border-green-500/20 py-2 rounded-lg text-center">
                                        <p className="text-[10px] font-bold text-green-500 uppercase">Audio</p>
                                        <p className="text-[8px] text-green-500/60">ACTIVE</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-orange-500/5 border border-orange-500/10 rounded-3xl p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <AlertTriangle className="text-orange-500" size={18} />
                            <h4 className="text-xs font-bold text-orange-500 uppercase tracking-widest">Notice</h4>
                        </div>
                        <p className="text-xs text-orange-200/60 leading-relaxed">
                            You are in **Silent Observer** mode. The candidate cannot see or hear you. All interactions are logged for compliance.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminGhostMode;
