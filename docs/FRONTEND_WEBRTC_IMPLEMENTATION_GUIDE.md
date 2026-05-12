# Frontend WebRTC Implementation Guide

This guide provides a detailed technical reference for implementing real-time AI proctoring using WebRTC. 

## 1. Overview
WebRTC is the preferred method for video proctoring in this platform. It provides lower latency and better performance compared to traditional WebSocket binary streaming.

**The Workflow:**
1.  **Candidate** captures camera and sends an SDP **Offer** to `/video/offer`.
2.  **Server** processes the offer, attaches AI logic, and returns an SDP **Awnswer**.
3.  **Peer-to-Peer** connection is established for the video stream.
4.  **Server** pushes real-time AI results back to the candidate via a **Data Channel**.

---

## 2. Prerequisites
- **HTTPS**: Browsers require a secure context to access the camera.
- **Interview ID**: A valid session ID is required in the request body.
- **Authentication**: A valid JWT token must be provided in the headers.

---

## 3. Implementation Steps (JavaScript)

### Step 1: Capture Camera
Access the candidate's camera stream.

```javascript
const stream = await navigator.mediaDevices.getUserMedia({ 
    video: { width: 640, height: 480, frameRate: 15 }, 
    audio: false 
});
```

### Step 2: Initialize PeerConnection
Create the connection with STUN servers for NAT traversal.

```javascript
const configuration = {
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
};

const pc = new RTCPeerConnection(configuration);

// Add camera tracks to the connection
stream.getTracks().forEach(track => pc.addTrack(track, stream));
```

### Step 3: Listen for AI Updates (Data Channel)
The server automatically creates a data channel named `"proctoring"`. You must handle the `ondatachannel` event to receive real-time AI warnings and coordinates.

```javascript
pc.ondatachannel = (event) => {
    const channel = event.channel;
    if (channel.label === "proctoring") {
        channel.onmessage = (e) => {
            const results = JSON.parse(e.data);
            handleAIUpdate(results);
        };
    }
};

function handleAIUpdate(data) {
    // Example response: { "faces": 1, "gaze": "Center", "warning": "" }
    if (data.warning) {
        showWarningToast(data.warning);
    }
}
```

### Step 4: Perform the Signaling Handshake
This is the core interaction with the `/video/offer` API.

```javascript
async function startProctoring(interviewId) {
    // 1. Create Local Offer
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    // 2. Send to Server
    const response = await fetch('/video/offer', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({
            sdp: pc.localDescription.sdp,
            type: pc.localDescription.type,
            interview_id: interviewId
        })
    });

    const result = await response.json();
    
    if (result.status_code === 200) {
        // 3. Set Remote Answer
        const answer = new RTCSessionDescription(result.data);
        await pc.setRemoteDescription(answer);
        console.log("WebRTC Proctoring Active");
    } else {
        console.error("Failed to start proctoring:", result.message);
    }
}
```

---

## 4. Data Channel Format (Incoming)

The server pushes JSON updates through the `proctoring` data channel at regular intervals (usually every time a frame is processed).

```json
{
    "faces": 1,
    "gaze": "Gazing Center",
    "warning": "",
    "detectors": {
        "face": true,
        "gaze": true
    },
    "timestamp": 1715423456.789
}
```

### Possible Warnings:
- `MULTIPLE FACES DETECTED`
- `NO FACE DETECTED`
- `SECURITY ALERT: UNAUTHORIZED PERSON`
- `WARNING: Gazing Away`

---

## 5. Admin Ghost Mode (Automatic)
When using WebRTC, the server stores a reference to the video track in memory. This enables the **Admin Dashboard** to "Watch Live" without the candidate doing anything extra. The server simply clones the incoming track and sends it to the admin via a separate `/video/watch` handshake.

---

## 6. Troubleshooting
- **ICE Connection Failed**: Usually caused by strict corporate firewalls. Ensure UDP ports are open or use a TURN server if needed.
- **`aiortc not installed`**: If the server returns a 533 error, it means the backend environment is missing the native WebRTC libraries.
- **Identity Check Failed**: Ensure the candidate's face was properly registered (embedded) during their profile setup.
