// Huddle PWA Main Application
class HuddleApp {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.isRecording = false;
        this.audioCapture = null;
        this.websocketClient = null;
        
        this.init();
    }
    
    init() {
        console.log('Initializing Huddle PWA');
        this.setupEventListeners();
        this.checkPWASupport();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeUI();
        });
        
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        window.addEventListener('online', () => {
            console.log('Connection restored');
            this.handleConnectionChange(true);
        });
        
        window.addEventListener('offline', () => {
            console.log('Connection lost');
            this.handleConnectionChange(false);
        });
    }
    
    initializeUI() {
        const requestPermissionBtn = document.getElementById('request-permission-btn');
        const toggleRecordingBtn = document.getElementById('toggle-recording');
        
        if (requestPermissionBtn) {
            requestPermissionBtn.addEventListener('click', () => {
                this.requestMicrophonePermission();
            });
        }
        
        if (toggleRecordingBtn) {
            toggleRecordingBtn.addEventListener('click', () => {
                this.toggleRecording();
            });
        }
    }
    
    checkPWASupport() {
        if ('serviceWorker' in navigator && 'mediaDevices' in navigator) {
            console.log('PWA features supported');
            return true;
        } else {
            console.warn('Some PWA features may not be supported');
            return false;
        }
    }
    
    async requestMicrophonePermission() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: { 
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            stream.getTracks().forEach(track => track.stop());
            
            this.showElement('meeting-controls');
            this.hideElement('permission-request');
            
            if (window.MEETING_ID) {
                this.joinMeeting(window.MEETING_ID);
            }
            
        } catch (error) {
            console.error('Microphone permission denied:', error);
            this.showError('Microphone access is required to participate in meetings.');
        }
    }
    
    async joinMeeting(meetingId) {
        try {
            if (!this.websocketClient && window.WebSocketClient) {
                this.websocketClient = new WebSocketClient(meetingId, this.sessionId);
                await this.websocketClient.connect();
            }
            
            if (!this.audioCapture && window.AudioCapture) {
                this.audioCapture = new AudioCapture(meetingId, this.sessionId);
            }
            
            this.updateStatus('Connected to meeting');
            this.hideElement('join-status');
            
        } catch (error) {
            console.error('Failed to join meeting:', error);
            this.showError('Failed to join meeting. Please try again.');
        }
    }
    
    async toggleRecording() {
        if (!this.audioCapture) {
            this.showError('Audio capture not initialized');
            return;
        }
        
        const toggleBtn = document.getElementById('toggle-recording');
        
        try {
            if (!this.isRecording) {
                await this.audioCapture.startRecording();
                this.isRecording = true;
                toggleBtn.innerHTML = `
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                        <rect x="6" y="6" width="12" height="12" rx="2"></rect>
                    </svg>
                    <span class="ml-2">Stop Recording</span>
                `;
                toggleBtn.className = 'bg-gray-500 text-white py-3 px-6 rounded-full hover:bg-gray-600 transition-colors';
                this.updateStatus('Recording...');
            } else {
                await this.audioCapture.stopRecording();
                this.isRecording = false;
                toggleBtn.innerHTML = `
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"></circle>
                    </svg>
                    <span class="ml-2">Start Recording</span>
                `;
                toggleBtn.className = 'bg-red-500 text-white py-3 px-6 rounded-full hover:bg-red-600 transition-colors';
                this.updateStatus('Recording stopped');
            }
        } catch (error) {
            console.error('Failed to toggle recording:', error);
            this.showError('Failed to toggle recording. Please try again.');
        }
    }
    
    updateStatus(message) {
        const statusEl = document.getElementById('status-text');
        if (statusEl) {
            statusEl.textContent = message;
        }
    }
    
    showError(message) {
        const errorEl = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        if (errorEl && errorText) {
            errorText.textContent = message;
            errorEl.classList.remove('hidden');
        }
    }
    
    hideError() {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.classList.add('hidden');
        }
    }
    
    showElement(id) {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove('hidden');
        }
    }
    
    hideElement(id) {
        const el = document.getElementById(id);
        if (el) {
            el.classList.add('hidden');
        }
    }
    
    handleConnectionChange(isOnline) {
        if (isOnline) {
            this.updateStatus('Connection restored');
            this.hideError();
        } else {
            this.showError('Connection lost. Some features may not work.');
        }
    }
    
    cleanup() {
        if (this.audioCapture) {
            this.audioCapture.cleanup();
        }
        if (this.websocketClient) {
            this.websocketClient.disconnect();
        }
    }
}

// Initialize the application
window.huddleApp = new HuddleApp();