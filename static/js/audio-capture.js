// Audio Capture and Processing
class AudioCapture {
    constructor(meetingId, sessionId) {
        this.meetingId = meetingId;
        this.sessionId = sessionId;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.qualityAnalyzer = null;
    }
    
    async startRecording() {
        try {
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000,
                    channelCount: 1
                }
            });
            
            const options = {
                mimeType: this.getSupportedMimeType(),
                audioBitsPerSecond: 16000
            };
            
            this.mediaRecorder = new MediaRecorder(this.audioStream, options);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            this.mediaRecorder.start(5000); // Collect data every 5 seconds
            this.isRecording = true;
            
            // Start quality analysis
            this.startQualityAnalysis();
            
            console.log('Recording started');
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            throw error;
        }
    }
    
    async stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
                this.audioStream = null;
            }
            
            this.isRecording = false;
            this.stopQualityAnalysis();
            
            console.log('Recording stopped');
        }
    }
    
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/wav'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return 'audio/webm'; // fallback
    }
    
    async processRecording() {
        if (this.audioChunks.length === 0) return;
        
        try {
            const audioBlob = new Blob(this.audioChunks, { 
                type: this.getSupportedMimeType() 
            });
            
            await this.uploadAudio(audioBlob);
            this.audioChunks = [];
            
        } catch (error) {
            console.error('Failed to process recording:', error);
        }
    }
    
    async uploadAudio(audioBlob) {
        const formData = new FormData();
        formData.append('meeting_id', this.meetingId);
        formData.append('session_id', this.sessionId);
        formData.append('audio_file', audioBlob, `recording_${Date.now()}.webm`);
        
        try {
            const response = await fetch('/api/upload-audio/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Audio uploaded successfully:', result.recording_id);
            } else {
                console.error('Failed to upload audio:', response.statusText);
            }
            
        } catch (error) {
            console.error('Upload error:', error);
        }
    }
    
    startQualityAnalysis() {
        if (!this.audioStream || !window.AudioContext) return;
        
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(this.audioStream);
            
            source.connect(analyser);
            analyser.fftSize = 256;
            
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            this.qualityAnalyzer = {
                analyser,
                dataArray,
                bufferLength,
                audioContext
            };
            
            this.analyzeAudioQuality();
            
        } catch (error) {
            console.error('Failed to start quality analysis:', error);
        }
    }
    
    analyzeAudioQuality() {
        if (!this.qualityAnalyzer || !this.isRecording) return;
        
        const { analyser, dataArray } = this.qualityAnalyzer;
        
        analyser.getByteFrequencyData(dataArray);
        
        // Calculate volume level
        const volume = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        const normalizedVolume = volume / 255;
        
        // Calculate background noise (low frequencies)
        const lowFreqNoise = dataArray.slice(0, 10).reduce((sum, value) => sum + value, 0) / 10 / 255;
        
        // Calculate clarity (high frequencies)
        const highFreqClarity = dataArray.slice(-10).reduce((sum, value) => sum + value, 0) / 10 / 255;
        
        const qualityMetrics = {
            volume_level: normalizedVolume,
            background_noise: lowFreqNoise,
            clarity_score: highFreqClarity,
            proximity_score: normalizedVolume > 0.1 ? 0.8 : 0.3 // Simplified proximity
        };
        
        // Send quality update via WebSocket
        if (window.huddleApp && window.huddleApp.websocketClient) {
            window.huddleApp.websocketClient.sendQualityUpdate(qualityMetrics);
        }
        
        // Continue analysis
        setTimeout(() => this.analyzeAudioQuality(), 2000); // Every 2 seconds
    }
    
    stopQualityAnalysis() {
        if (this.qualityAnalyzer) {
            this.qualityAnalyzer.audioContext.close();
            this.qualityAnalyzer = null;
        }
    }
    
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        return cookieValue ? cookieValue.split('=')[1] : '';
    }
    
    cleanup() {
        this.stopRecording();
        this.stopQualityAnalysis();
    }
}

window.AudioCapture = AudioCapture;