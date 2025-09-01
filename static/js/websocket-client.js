// WebSocket Client for Real-time Communication
class WebSocketClient {
    constructor(meetingId, sessionId) {
        this.meetingId = meetingId;
        this.sessionId = sessionId;
        this.socket = null;
        this.coordinationSocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
    }
    
    async connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/meeting/${this.meetingId}/`;
            const coordinationUrl = `${protocol}//${window.location.host}/ws/coordination/${this.meetingId}/`;
            
            this.socket = new WebSocket(wsUrl);
            this.coordinationSocket = new WebSocket(coordinationUrl);
            
            this.setupEventHandlers(this.socket, 'meeting');
            this.setupEventHandlers(this.coordinationSocket, 'coordination');
            
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Connection timeout'));
                }, 10000);
                
                this.socket.onopen = () => {
                    clearTimeout(timeout);
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    console.log('Connected to meeting WebSocket');
                    
                    // Send participant joined message
                    this.sendMessage({
                        type: 'participant_joined',
                        session_id: this.sessionId,
                        user_agent: navigator.userAgent
                    });
                    
                    resolve();
                };
                
                this.socket.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('WebSocket connection error:', error);
                    reject(error);
                };
            });
            
        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            throw error;
        }
    }
    
    setupEventHandlers(socket, type) {
        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data, type);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        socket.onclose = (event) => {
            console.log(`${type} WebSocket closed:`, event.code, event.reason);
            this.isConnected = false;
            
            if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.attemptReconnect();
            }
        };
        
        socket.onerror = (error) => {
            console.error(`${type} WebSocket error:`, error);
        };
    }
    
    handleMessage(data, socketType) {
        switch (data.type) {
            case 'participant_joined_message':
                this.handleParticipantJoined(data);
                break;
                
            case 'audio_quality_message':
                this.handleAudioQualityUpdate(data);
                break;
                
            case 'recording_status_message':
                this.handleRecordingStatusUpdate(data);
                break;
                
            case 'quality_update_message':
                this.handleCoordinationQualityUpdate(data);
                break;
                
            case 'coordination_decision_message':
                this.handleCoordinationDecision(data);
                break;
                
            default:
                console.log(`Unknown message type: ${data.type}`, data);
        }
    }
    
    handleParticipantJoined(data) {
        console.log('Participant joined:', data.session_id);
        this.updateParticipantsList();
    }
    
    handleAudioQualityUpdate(data) {
        console.log('Audio quality update:', data);
        // Update UI with quality information
    }
    
    handleRecordingStatusUpdate(data) {
        console.log('Recording status update:', data);
        // Update UI with recording status
    }
    
    handleCoordinationQualityUpdate(data) {
        console.log('Coordination quality update:', data);
    }
    
    handleCoordinationDecision(data) {
        console.log('Coordination decision:', data);
        
        if (data.decision) {
            const { primary_recorder, backup_recorders } = data.decision;
            
            if (primary_recorder === this.sessionId) {
                this.becomePrimaryRecorder();
            } else if (backup_recorders.includes(this.sessionId)) {
                this.becomeBackupRecorder();
            } else {
                this.becomePassiveParticipant();
            }
        }
    }
    
    becomePrimaryRecorder() {
        console.log('Becoming primary recorder');
        this.updateStatus('You are the primary recorder');
        // Ensure high-quality recording
    }
    
    becomeBackupRecorder() {
        console.log('Becoming backup recorder');
        this.updateStatus('You are a backup recorder');
        // Continue recording as backup
    }
    
    becomePassiveParticipant() {
        console.log('Becoming passive participant');
        this.updateStatus('Other devices are handling recording');
        // Optionally stop recording
    }
    
    sendMessage(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, queuing message:', message);
        }
    }
    
    sendCoordinationMessage(message) {
        if (this.coordinationSocket && this.coordinationSocket.readyState === WebSocket.OPEN) {
            this.coordinationSocket.send(JSON.stringify(message));
        }
    }
    
    sendQualityUpdate(qualityMetrics) {
        this.sendCoordinationMessage({
            type: 'quality_update',
            session_id: this.sessionId,
            quality_metrics: qualityMetrics
        });
    }
    
    requestCoordination() {
        this.sendCoordinationMessage({
            type: 'request_coordination',
            session_id: this.sessionId
        });
    }
    
    updateRecordingStatus(isRecording) {
        this.sendMessage({
            type: 'recording_status',
            session_id: this.sessionId,
            is_recording: isRecording
        });
    }
    
    async updateParticipantsList() {
        try {
            const response = await fetch(`/api/meeting/${this.meetingId}/status/`);
            if (response.ok) {
                const data = await response.json();
                this.renderParticipantsList(data.participants);
            }
        } catch (error) {
            console.error('Failed to fetch participants:', error);
        }
    }
    
    renderParticipantsList(participants) {
        const container = document.getElementById('participants-container');
        if (!container) return;
        
        if (participants.length === 0) {
            container.innerHTML = '<div class="text-sm text-gray-500">No participants</div>';
            return;
        }
        
        const participantElements = participants.map(participant => {
            const isCurrentUser = participant.session_id === this.sessionId;
            const recordingStatus = participant.is_recording ? 'Recording' : 'Not recording';
            const qualityScore = participant.audio_quality_score ? 
                `Quality: ${Math.round(participant.audio_quality_score * 100)}%` : 
                'Quality: Unknown';
            
            return `
                <div class="flex items-center justify-between py-2 px-3 ${isCurrentUser ? 'bg-blue-50 rounded' : ''}">
                    <div>
                        <div class="text-sm font-medium">
                            ${isCurrentUser ? 'You' : `Participant ${participant.session_id.slice(-4)}`}
                        </div>
                        <div class="text-xs text-gray-500">${qualityScore}</div>
                    </div>
                    <div class="text-xs">
                        <span class="inline-flex px-2 py-1 text-xs rounded-full ${
                            participant.is_recording ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                        }">
                            ${recordingStatus}
                        </span>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = participantElements;
    }
    
    attemptReconnect() {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect().catch((error) => {
                console.error('Reconnect failed:', error);
            });
        }, this.reconnectDelay * this.reconnectAttempts);
    }
    
    updateStatus(message) {
        const statusEl = document.getElementById('status-text');
        if (statusEl) {
            statusEl.textContent = message;
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        
        if (this.coordinationSocket) {
            this.coordinationSocket.close();
            this.coordinationSocket = null;
        }
        
        this.isConnected = false;
    }
}

window.WebSocketClient = WebSocketClient;