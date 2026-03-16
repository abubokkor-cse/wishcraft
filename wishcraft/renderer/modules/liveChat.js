/**
 * EduMind Live Chat Module
 * Real-time voice conversation using Gemini Live API
 * Based on Google's Live API Web Console implementation
 */

// Audio processing utilities
function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

function base64ToArrayBuffer(base64) {
    const binaryString = window.atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

// Simple EventEmitter implementation
class EventEmitter {
    constructor() {
        this.events = {};
    }

    on(event, listener) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(listener);
        return this;
    }

    off(event, listener) {
        if (!this.events[event]) return this;
        this.events[event] = this.events[event].filter(l => l !== listener);
        return this;
    }

    emit(event, ...args) {
        if (!this.events[event]) return;
        this.events[event].forEach(listener => listener(...args));
    }
}

/**
 * Audio Recorder for capturing microphone input
 */
export class LiveAudioRecorder extends EventEmitter {
    constructor(sampleRate = 16000) {
        super();
        this.sampleRate = sampleRate;
        this.stream = null;
        this.audioContext = null;
        this.source = null;
        this.processor = null;
        this.recording = false;
    }

    async start() {
        if (this.recording) return;

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: this.sampleRate,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: this.sampleRate
            });

            this.source = this.audioContext.createMediaStreamSource(this.stream);

            // Use ScriptProcessor for audio processing (works in all browsers)
            // Smaller buffer = lower latency (2048 = 128ms at 16kHz vs 4096 = 256ms)
            this.processor = this.audioContext.createScriptProcessor(2048, 1, 1);

            this.processor.onaudioprocess = (e) => {
                if (!this.recording) return;

                const inputData = e.inputBuffer.getChannelData(0);

                const int16Array = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                const base64 = arrayBufferToBase64(int16Array.buffer);
                this.emit('data', base64);

                // Calculate volume for visualization
                let sum = 0;
                for (let i = 0; i < inputData.length; i++) {
                    sum += inputData[i] * inputData[i];
                }
                const volume = Math.sqrt(sum / inputData.length);
                this.emit('volume', volume);
            };

            this.source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);

            this.recording = true;
            console.log('🎙️ Live audio recorder started');

        } catch (error) {
            console.error('Failed to start audio recorder:', error);
            throw error;
        }
    }

    stop() {
        this.recording = false;

        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        console.log('🛑 Live audio recorder stopped');
    }
}

/**
 * Audio Streamer for playing received audio
 */
export class LiveAudioStreamer {
    constructor(sampleRate = 24000) {
        this.sampleRate = sampleRate;
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.scheduledTime = 0;
        this.bufferSize = 4800;          // 200ms at 24kHz (reduced from 320ms for lower latency)
        this.initialBufferTime = 0.02;   // 20ms — faster first audio playback
        this.onComplete = () => { };

        this.activeSources = [];

        // AnalyserNode-based amplitude for lip sync (reliable real-time)
        this.onAmplitude = null;  // Callback: (amplitude) => {} where amplitude is 0-1
        this.analyserNode = null;
        this.gainNode = null;
        this._amplitudeRAF = null;
        this._lastAmplitude = 0;
    }

    async init() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: this.sampleRate
            });
        }
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }

        if (!this.analyserNode) {
            this.analyserNode = this.audioContext.createAnalyser();
            this.analyserNode.fftSize = 256;
            this.analyserNode.smoothingTimeConstant = 0.3;
            this.gainNode = this.audioContext.createGain();
            this.gainNode.gain.value = 1.0;
            this.gainNode.connect(this.analyserNode);
            this.analyserNode.connect(this.audioContext.destination);
            console.log('🔊 AnalyserNode created for lip sync');
        }

        console.log('🔊 AudioStreamer initialized, state:', this.audioContext.state);
        return this;
    }

    /**
     * Start real-time amplitude monitoring using AnalyserNode
     * This polls the actual audio output - guaranteed to work when audio plays
     */
    startAmplitudeMonitoring() {
        if (!this.analyserNode || !this.onAmplitude) return;
        if (this._amplitudeRAF) return; // Already monitoring

        console.log('🎤 Starting AnalyserNode amplitude monitoring for lip sync');
        const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);

        const poll = () => {
            this._amplitudeRAF = requestAnimationFrame(poll);

            this.analyserNode.getByteTimeDomainData(dataArray);

            // Calculate RMS from waveform data (centered at 128)
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                const sample = (dataArray[i] - 128) / 128;  // Normalize to -1..1
                sum += sample * sample;
            }
            const rms = Math.sqrt(sum / dataArray.length);
            const amplitude = Math.min(1, rms * 4);  // Scale up for visibility

            // Smooth
            const smoothed = this._lastAmplitude * 0.3 + amplitude * 0.7;
            this._lastAmplitude = smoothed;

            if (this.onAmplitude) {
                this.onAmplitude(smoothed);
            }
        };

        poll();
    }

    /**
     * Stop amplitude monitoring
     */
    stopAmplitudeMonitoring() {
        if (this._amplitudeRAF) {
            cancelAnimationFrame(this._amplitudeRAF);
            this._amplitudeRAF = null;
            this._lastAmplitude = 0;
            console.log('🎤 Stopped amplitude monitoring');
        }
    }

    addPCM16(chunk) {
        if (this.audioContext && this.audioContext.state === 'suspended') {
            console.log('🔊 AudioContext suspended, resuming...');
            this.audioContext.resume();
        }

        if (!this.audioContext) {
            console.error('❌ AudioContext not initialized!');
            return;
        }

        const chunkBuffer = chunk.buffer.slice(chunk.byteOffset, chunk.byteOffset + chunk.byteLength);

        const float32Array = new Float32Array(chunk.length / 2);
        const dataView = new DataView(chunkBuffer);

        for (let i = 0; i < chunk.length / 2; i++) {
            const int16 = dataView.getInt16(i * 2, true);
            float32Array[i] = int16 / 32768;
        }

        let processingBuffer = float32Array;
        while (processingBuffer.length >= this.bufferSize) {
            const buffer = processingBuffer.slice(0, this.bufferSize);
            this.audioQueue.push(buffer);
            processingBuffer = processingBuffer.slice(this.bufferSize);
        }

        if (processingBuffer.length > 0) {
            this.audioQueue.push(processingBuffer);
        }

        if (!this.isPlaying) {
            this.isPlaying = true;
            this.scheduledTime = this.audioContext.currentTime + this.initialBufferTime;
            this.scheduleNextBuffer();

            this.startAmplitudeMonitoring();
        }
    }

    scheduleNextBuffer() {
        const SCHEDULE_AHEAD_TIME = 0.1;  // 100ms — tighter scheduling for lower latency

        while (
            this.audioQueue.length > 0 &&
            this.scheduledTime < this.audioContext.currentTime + SCHEDULE_AHEAD_TIME
        ) {
            const audioData = this.audioQueue.shift();
            const audioBuffer = this.audioContext.createBuffer(1, audioData.length, this.sampleRate);
            audioBuffer.getChannelData(0).set(audioData);

            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            if (this.gainNode) {
                source.connect(this.gainNode);
            } else {
                source.connect(this.audioContext.destination);
            }

            this.activeSources.push(source);
            source.onended = () => {
                const idx = this.activeSources.indexOf(source);
                if (idx !== -1) this.activeSources.splice(idx, 1);
                if (this.audioQueue.length === 0 && this.activeSources.length === 0) {
                    this.isPlaying = false;
                    this.onComplete();
                }
            };

            const startTime = Math.max(this.scheduledTime, this.audioContext.currentTime);
            source.start(startTime);
            this.scheduledTime = startTime + audioBuffer.duration;
        }

        if (this.audioQueue.length > 0) {
            requestAnimationFrame(() => this.scheduleNextBuffer());
        }
    }

    stop() {
        this.audioQueue = [];
        this.isPlaying = false;
        for (const source of this.activeSources) {
            try { source.stop(); } catch (e) { /* already stopped */ }
        }
        this.activeSources = [];
        this.stopAmplitudeMonitoring();
    }

    resume() {
        if (this.audioContext) {
            console.log('🔊 resume() called, AudioContext state:', this.audioContext.state);
            if (this.audioContext.state === 'suspended') {
                this.audioContext.resume().then(() => {
                    console.log('🔊 AudioContext resumed successfully, new state:', this.audioContext.state);
                });
            }
        } else {
            console.error('❌ resume() called but AudioContext is null!');
        }
    }
}

/**
 * Fetch API key - supports server endpoint or direct key
 * @param {string} serverUrl - Optional server URL to fetch from (e.g., 'http://localhost:3001')
 */
async function fetchLiveApiKey(serverUrl) {
    // 1. Try from a provided server URL (Cloud Run backend)
    if (serverUrl) {
        try {
            const response = await fetch(`${serverUrl}/api/gemini-key`);
            if (response.ok) {
                const data = await response.json();
                console.log('🔑 Live API key fetched from Cloud Run backend');
                return data;
            }
        } catch (e) {
            console.warn('Could not fetch from server:', e.message);
        }
    }

    // 2. Try from relative path (web server like EduMind)
    try {
        const response = await fetch('/api/live-token');
        if (response.ok) {
            const data = await response.json();
            console.log('🔑 Live API key fetched from web server');
            return data;
        }
    } catch (e) {
        // Expected to fail in Electron's file:// protocol
    }

    // 3. Fallback: check localStorage
    const storedKey = localStorage.getItem('geminiApiKey');
    if (storedKey) {
        console.log('🔑 Live API key from localStorage');
        return { apiKey: storedKey };
    }

    // 4. Prompt user to enter API key
    const userKey = prompt('Enter your Gemini API key:');
    if (userKey) {
        localStorage.setItem('geminiApiKey', userKey);
        console.log('🔑 Live API key saved to localStorage');
        return { apiKey: userKey };
    }

    throw new Error('No API key available. Set it in localStorage or Cloud Run backend.');
}

/**
 * Screen Share Stream — captures screen at ~1 FPS via Electron desktopCapturer
 * Sends JPEG frames to Live API via realtimeInput.video
 */
class ScreenShareStream {
    constructor() {
        this.interval = null;
        this.isStreaming = false;
        this.fps = 1;
        this.sendFn = null;
    }

    start(sendFn, fps = 1) {
        if (this.isStreaming) return;
        this.sendFn = sendFn;
        this.fps = fps;
        this.isStreaming = true;

        const captureFrame = async () => {
            if (!this.isStreaming || !this.sendFn) return;
            try {
                const base64 = await window.wishcraft.takeScreenshot();
                if (base64 && this.sendFn) {
                    this.sendFn(base64, 'image/jpeg');
                }
            } catch (e) {
                console.warn('Screen capture frame failed:', e);
            }
        };

        // Capture first frame immediately, then at interval
        captureFrame();
        this.interval = setInterval(captureFrame, 1000 / this.fps);
        console.log('🖥️ Screen sharing started at', this.fps, 'FPS');
    }

    stop() {
        this.isStreaming = false;
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        this.sendFn = null;
        console.log('🖥️ Screen sharing stopped');
    }
}

/**
 * Webcam Stream — captures camera frames at ~1 FPS via getUserMedia
 * Sends JPEG frames to Live API via realtimeInput.video
 */
class WebcamStream {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.mediaStream = null;
        this.interval = null;
        this.isStreaming = false;
        this.fps = 1;
        this.sendFn = null;
    }

    async start(sendFn, options = {}) {
        if (this.isStreaming) return;

        const { fps = 1, width = 640, height = 480, quality = 0.7 } = options;
        this.fps = fps;
        this.sendFn = sendFn;

        this.mediaStream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: width }, height: { ideal: height }, facingMode: 'user' }
        });

        this.video = document.createElement('video');
        this.video.srcObject = this.mediaStream;
        this.video.autoplay = true;
        this.video.playsInline = true;
        this.video.muted = true;

        this.canvas = document.createElement('canvas');
        this.canvas.width = width;
        this.canvas.height = height;
        this.ctx = this.canvas.getContext('2d');

        await new Promise(resolve => { this.video.onloadedmetadata = resolve; });
        this.video.play();

        this.isStreaming = true;

        const captureFrame = () => {
            if (!this.isStreaming || !this.sendFn) return;
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            this.canvas.toBlob(blob => {
                if (!blob || !this.sendFn) return;
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64 = reader.result.split(',')[1];
                    if (this.sendFn) this.sendFn(base64, 'image/jpeg');
                };
                reader.readAsDataURL(blob);
            }, 'image/jpeg', quality);
        };

        captureFrame();
        this.interval = setInterval(captureFrame, 1000 / this.fps);
        console.log('📹 Webcam streaming started at', this.fps, 'FPS');
    }

    stop() {
        this.isStreaming = false;
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(t => t.stop());
            this.mediaStream = null;
        }
        if (this.video) {
            this.video.srcObject = null;
            this.video = null;
        }
        this.canvas = null;
        this.ctx = null;
        this.sendFn = null;
        console.log('📹 Webcam streaming stopped');
    }

    getVideoElement() {
        return this.video;
    }
}

/**
 * Gemini Live API Client
 */
export class GeminiLiveClient extends EventEmitter {
    constructor(apiKey) {
        super();
        this.apiKey = apiKey;
        this.ws = null;
        this.status = 'disconnected';
        this.model = 'models/gemini-2.5-flash-native-audio-preview-12-2025';
        this.config = null;
        this.currentTranscript = '';
        this.userTranscript = '';
    }

    async connect(config = {}) {
        if (this.status === 'connected' || this.status === 'connecting') {
            return false;
        }

        this.status = 'connecting';
        this.config = config;

        const wsUrl = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=${this.apiKey}`;

        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(wsUrl);

                // Store resolve/reject for use in handleMessage
                this._connectResolve = resolve;
                this._connectReject = reject;

                this.ws.onopen = () => {
                    console.log('🔗 WebSocket connected');

                    const setupMessage = {
                        setup: {
                            model: this.model,
                            generationConfig: {
                                responseModalities: ["AUDIO"],
                                speechConfig: {
                                    voiceConfig: {
                                        prebuiltVoiceConfig: {
                                            voiceName: config.voiceName || "Aoede"
                                        }
                                    }
                                }
                            },
                            realtimeInputConfig: {
                                automaticActivityDetection: {
                                    disabled: false,
                                    startOfSpeechSensitivity: "START_SENSITIVITY_HIGH",
                                    endOfSpeechSensitivity: "END_SENSITIVITY_UNSPECIFIED",
                                    prefixPaddingMs: 300,
                                    silenceDurationMs: 700
                                },
                                activityHandling: "START_OF_ACTIVITY_INTERRUPTS"
                            },
                            inputAudioTranscription: {},
                            outputAudioTranscription: {},
                            systemInstruction: {
                                parts: [{
                                    text: config.systemInstruction || `You are EduMind, a friendly AI teacher.

IMPORTANT - YOU HAVE FUNCTION CALLING TOOLS:
- When student asks for quiz/practice/test → ALWAYS call generate_quiz function
- When student asks to draw/show/visualize/image → ALWAYS call generate_image function
- When student asks for flashcards → ALWAYS call generate_flashcards function
- When student asks about progress → ALWAYS call show_student_progress function

NEVER say "I cannot generate images" or "I cannot create quizzes" - you CAN by calling the functions.

Be warm, explain simply, keep responses concise.`
                                }]
                            },
                            tools: config.tools || []
                        }
                    };

                    console.log('📤 Setup sent, tools count:', (config.tools || []).length);
                    this.ws.send(JSON.stringify(setupMessage));
                };

                this.ws.onmessage = async (event) => {
                    try {
                        let text;
                        if (event.data instanceof Blob) {
                            text = await event.data.text();
                        } else {
                            text = event.data;
                        }
                        console.log('📩 Raw message received, length:', text.length);
                        const data = JSON.parse(text);
                        console.log('📩 Parsed message keys:', Object.keys(data));
                        this.handleMessage(data);
                    } catch (e) {
                        console.error('Failed to parse message:', e);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.status = 'disconnected';
                    this.emit('error', error);
                    reject(error);
                };

                this.ws.onclose = (event) => {
                    console.log('WebSocket closed:', event.reason);
                    this.status = 'disconnected';
                    this.emit('close', event);
                    if (this._connectReject) {
                        this._connectReject(new Error(event.reason || 'WebSocket closed'));
                        this._connectReject = null;
                    }
                };

            } catch (error) {
                this.status = 'disconnected';
                reject(error);
            }
        });
    }

    handleMessage(data) {
        if (data.setupComplete) {
            console.log('✅ Live API setup complete');
            this.status = 'connected';
            this.emit('open');
            this.emit('setupcomplete');
            if (this._connectResolve) {
                this._connectResolve(true);
                this._connectResolve = null;
            }
            return;
        }

        // Server content
        if (data.serverContent) {
            const content = data.serverContent;
            console.log('📩 serverContent keys:', Object.keys(content));

            // Interrupted
            if (content.interrupted) {
                console.log('⚠️ Response interrupted');
                this.emit('interrupted');
                return;
            }

            // Turn complete
            if (content.turnComplete) {
                console.log('✅ Turn complete');
                this.emit('turncomplete');

                if (this.userTranscript) {
                    this.emit('usertranscript', this.userTranscript);
                    this.userTranscript = '';
                }
                // Then emit AI transcript
                if (this.currentTranscript) {
                    this.emit('aitranscript', this.currentTranscript);
                    this.currentTranscript = '';
                }
                return;
            }

            // Input transcription (what user said)
            if (content.inputTranscription && content.inputTranscription.text) {
                console.log('🎤 User said:', content.inputTranscription.text);
                this.userTranscript += content.inputTranscription.text;
                this.emit('userinput', content.inputTranscription.text);
            }

            // Output transcription (what AI said - text version of audio)
            if (content.outputTranscription && content.outputTranscription.text) {
                console.log('🤖 AI said:', content.outputTranscription.text);
                this.currentTranscript += content.outputTranscription.text;
                this.emit('aioutput', content.outputTranscription.text);
            }

            // Model turn with content
            if (content.modelTurn && content.modelTurn.parts) {
                for (const part of content.modelTurn.parts) {
                    // Audio data - only emit audio, NOT text (text comes from outputTranscription)
                    if (part.inlineData && part.inlineData.mimeType?.startsWith('audio/')) {
                        const audioData = base64ToArrayBuffer(part.inlineData.data);
                        this.emit('audio', audioData);
                    }

                    // if (part.text) { ... } - deliberately removed to avoid showing "Crafting Bengali Response" etc.
                }
            }
        }

        // Tool call
        if (data.toolCall) {
            const fnNames = (data.toolCall.functionCalls || []).map(f => f.name).join(', ');
            console.log('🔧 Tool call:', fnNames);
            this.emit('toolcall', data.toolCall);
        }
    }

    /**
     * Send realtime audio input
     */
    sendAudio(base64Audio) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                realtimeInput: {
                    audio: {
                        mimeType: "audio/pcm;rate=16000",
                        data: base64Audio
                    }
                }
            };
            this.ws.send(JSON.stringify(message));
        }
    }

    /**
     * Send text message
     */
    sendText(text) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                clientContent: {
                    turns: [{
                        role: "user",
                        parts: [{ text }]
                    }],
                    turnComplete: true
                }
            };
            this.ws.send(JSON.stringify(message));
        }
    }

    /**
     * Send image with optional text
     * useRealtimeInput=true: for screenshots/webcam (small JPEG frames)
     * useRealtimeInput=false: for uploaded images (all formats, uses clientContent like EduMind)
     */
    sendImage(base64Image, mimeType = 'image/jpeg', text = '', useRealtimeInput = false) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            if (useRealtimeInput) {
                // realtimeInput.video — for screenshots/webcam frames (small JPEG only)
                if (text) this.sendText(text);
                const message = {
                    realtimeInput: {
                        video: {
                            mimeType: mimeType,
                            data: base64Image
                        }
                    }
                };
                this.ws.send(JSON.stringify(message));
                console.log('📤 Sent image via realtimeInput.video');
            } else {
                // clientContent — for uploaded images (all formats, any size <4MB)
                const parts = [];
                if (text) {
                    parts.push({ text });
                }
                parts.push({
                    inlineData: {
                        mimeType,
                        data: base64Image
                    }
                });
                const message = {
                    clientContent: {
                        turns: [{
                            role: "user",
                            parts
                        }],
                        turnComplete: true
                    }
                };
                this.ws.send(JSON.stringify(message));
                console.log('📤 Sent image via clientContent.inlineData');
            }
        }
    }

    /**
     * Send tool response
     */
    sendToolResponse(functionResponses) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                toolResponse: {
                    functionResponses
                }
            };
            this.ws.send(JSON.stringify(message));
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.status = 'disconnected';
        console.log('🔌 Disconnected from Live API');
    }

    isConnected() {
        return this.status === 'connected' && this.ws?.readyState === WebSocket.OPEN;
    }
}

/**
 * EduMind Live Chat Controller
 * Manages the Live API session with audio streaming
 */
export class LiveChatController {
    constructor(apiKey, options = {}) {
        this.apiKey = apiKey;
        this.options = options;

        this.client = null;
        this.audioRecorder = new LiveAudioRecorder();
        this.audioStreamer = new LiveAudioStreamer();
        this.screenShare = new ScreenShareStream();
        this.webcam = new WebcamStream();

        this.isActive = false;
        this.isMuted = false;
        this.isAISpeaking = false;
        this.streamStarted = false;
        this.streamReady = false;
        this.pendingAudioChunks = [];

        // Callbacks
        this.onUserSpeaking = options.onUserSpeaking || (() => { });
        this.onAIResponse = options.onAIResponse || (() => { });
        this.onStatusChange = options.onStatusChange || (() => { });
        this.onVolumeChange = options.onVolumeChange || (() => { });
        this.onTranscript = options.onTranscript || (() => { });
        this.onUserTranscript = options.onUserTranscript || (() => { });
        this.onAITranscript = options.onAITranscript || (() => { });
        this.onError = options.onError || (() => { });
        this.onToolCall = options.onToolCall || null;  // Tool/function calling callback

        // Lip sync callbacks for TalkingHead integration
        this.onAudioChunk = options.onAudioChunk || null;  // Raw PCM for lip sync
        this.onAmplitude = options.onAmplitude || null;  // Audio amplitude (0-1) for real-time lip sync
        this.onStreamStart = options.onStreamStart || (async () => { });  // Async callback
        this.onStreamEnd = options.onStreamEnd || (() => { });
        this.onInterrupted = options.onInterrupted || (() => { });  // Called when user interrupts AI
    }

    async start() {
        if (this.isActive) return;

        try {
            this.onStatusChange('connecting');

            let apiKey = this.apiKey;
            if (!apiKey) {
                console.log('🔑 Fetching Live API key...');
                const tokenData = await fetchLiveApiKey(this.options.serverUrl);
                apiKey = tokenData.apiKey;
            }

            this.client = new GeminiLiveClient(apiKey);

            await this.audioStreamer.init();

            if (this.onAmplitude) {
                this.audioStreamer.onAmplitude = this.onAmplitude;
                console.log('✅ Amplitude callback set on audioStreamer');
            } else {
                console.log('⚠️ No onAmplitude callback provided in options');
            }

            this.client.on('open', () => {
                console.log('🎉 Live chat connected');
                this.isActive = true;
                this.onStatusChange('connected');
            });

            this.client.on('audio', async (data) => {
                this.isAISpeaking = true;

                if (!this.streamStarted) {
                    this.streamStarted = true;
                    this.streamReady = false;
                    this.pendingAudioChunks = [data];

                    try {
                        await this.onStreamStart();
                        this.streamReady = true;
                        for (const chunk of this.pendingAudioChunks) {
                            const pcm = new Uint8Array(chunk);
                            if (this.onAudioChunk) this.onAudioChunk(pcm);
                            else this.audioStreamer.addPCM16(pcm);
                        }
                        this.pendingAudioChunks = [];
                    } catch (e) {
                        console.error('Stream init failed:', e);
                        this.streamReady = true;
                    }
                    return;
                }

                if (!this.streamReady) {
                    this.pendingAudioChunks.push(data);
                    return;
                }

                const pcm = new Uint8Array(data);
                if (this.onAudioChunk) {
                    this.onAudioChunk(pcm);
                } else {
                    this.audioStreamer.addPCM16(pcm);
                }
            });

            this.client.on('content', (content) => {
                if (content.text) {
                    this.onAIResponse(content.text, false);
                }
            });

            // User input transcription (real-time)
            this.client.on('userinput', (text) => {
                this.onUserTranscript(text, false);
            });

            // AI output transcription (real-time)
            this.client.on('aioutput', (text) => {
                this.onAITranscript(text, false);
            });

            // Complete user transcript
            this.client.on('usertranscript', (transcript) => {
                this.onUserTranscript(transcript, true);
            });

            // Complete AI transcript
            this.client.on('aitranscript', (transcript) => {
                this.onTranscript(transcript);
                this.onAITranscript(transcript, true);
                this.onAIResponse(transcript, true);
            });

            this.client.on('turncomplete', () => {
                this.isAISpeaking = false;
                if (this.streamStarted) {
                    this.streamStarted = false;
                    this.streamReady = false;
                    this.pendingAudioChunks = [];
                    this.onStreamEnd();
                }
            });

            this.client.on('interrupted', () => {
                this.audioStreamer.stop();
                this.isAISpeaking = false;
                // Immediately stop on interruption (not graceful end)
                if (this.streamStarted) {
                    this.streamStarted = false;
                    this.streamReady = false;
                    this.pendingAudioChunks = [];
                    this.onInterrupted();
                }
            });

            this.client.on('error', (error) => {
                console.error('Live API error:', error);
                this.onError(error);
            });

            this.client.on('close', () => {
                this.isActive = false;
                this.onStatusChange('disconnected');
            });

            // Tool/function call from AI
            this.client.on('toolcall', async (toolCall) => {
                if (this.onToolCall) {
                    await this.onToolCall(toolCall);
                }
            });

            // Audio streamer complete callback
            this.audioStreamer.onComplete = () => {
                this.isAISpeaking = false;
            };

            // Connect to Live API with tools
            await this.client.connect({
                systemInstruction: this.options.systemInstruction,
                voiceName: this.options.voiceName || "Aoede",
                tools: this.options.tools || []
            });

            this.audioRecorder.on('data', (base64) => {
                if (!this.isMuted && this.isActive) {
                    this.client.sendAudio(base64);
                }
            });

            this.audioRecorder.on('volume', (volume) => {
                this.onVolumeChange(volume);
                if (volume > 0.01 && !this.isMuted) {
                    this.onUserSpeaking(true);
                }
            });

            await this.audioRecorder.start();

        } catch (error) {
            console.error('Failed to start live chat:', error);
            this.onError(error);
            this.onStatusChange('error');
            throw error;
        }
    }

    stop() {
        this.isActive = false;

        this.screenShare.stop();
        this.webcam.stop();
        this.audioRecorder.stop();
        this.audioStreamer.stop();

        if (this.client) {
            this.client.disconnect();
            this.client = null;
        }

        this.onStatusChange('disconnected');
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        return this.isMuted;
    }

    setMuted(muted) {
        this.isMuted = muted;
    }

    /**
     * Send a text message in Live mode
     */
    sendText(text) {
        if (this.client && this.isActive) {
            this.client.sendText(text);
        }
    }

    /**
     * Send an image with optional text
     * useRealtimeInput: true for screenshots/webcam, false for uploaded files
     */
    sendImage(base64Image, mimeType = 'image/jpeg', text = '', useRealtimeInput = false) {
        if (this.client && this.isActive) {
            this.client.sendImage(base64Image, mimeType, text, useRealtimeInput);
        }
    }

    /**
     * Send tool/function call responses back to the AI
     */
    sendToolResponse(functionResponses) {
        if (this.client && this.isActive) {
            this.client.sendToolResponse(functionResponses);
        }
    }

    /**
     * Resume audio context (needed after user interaction)
     */
    resumeAudio() {
        this.audioStreamer.resume();
    }

    /**
     * Start continuous screen sharing at ~1 FPS
     */
    startScreenShare(fps = 1) {
        if (!this.client || !this.isActive) return false;
        const sendFn = (base64, mimeType) => {
            if (this.client && this.isActive) {
                this.client.sendImage(base64, mimeType, '', true); // realtimeInput for streaming frames
            }
        };
        this.screenShare.start(sendFn, fps);
        return true;
    }

    stopScreenShare() {
        this.screenShare.stop();
    }

    isScreenSharing() {
        return this.screenShare.isStreaming;
    }

    /**
     * Start webcam streaming at ~1 FPS
     */
    async startWebcam(options = {}) {
        if (!this.client || !this.isActive) return false;
        const sendFn = (base64, mimeType) => {
            if (this.client && this.isActive) {
                this.client.sendImage(base64, mimeType, '', true); // realtimeInput for streaming frames
            }
        };
        await this.webcam.start(sendFn, { fps: 1, ...options });
        return true;
    }

    stopWebcam() {
        this.webcam.stop();
    }

    isWebcamActive() {
        return this.webcam.isStreaming;
    }
}

// Export default instance creator
export function createLiveChatController(apiKey, options) {
    return new LiveChatController(apiKey, options);
}
