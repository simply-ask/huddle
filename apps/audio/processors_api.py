"""
Audio processing using OpenAI API instead of local Whisper
This is much lighter and works better on DigitalOcean App Platform
"""
import tempfile
import os
from .models import AudioRecording, TranscriptionSegment
from decouple import config

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class OpenAIProcessor:
    """Use OpenAI's Whisper API for transcription (no local model needed)"""
    
    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available")
        
        api_key = config('OPENAI_API_KEY', default='')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
            
        self.client = OpenAI(api_key=api_key)
    
    def transcribe_audio(self, audio_recording):
        """Transcribe audio using OpenAI Whisper API"""
        try:
            # Open the audio file
            audio_file_path = audio_recording.audio_file.path
            
            with open(audio_file_path, 'rb') as audio_file:
                # Call OpenAI Whisper API
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # Process segments if available
            if hasattr(response, 'segments'):
                for segment in response.segments:
                    TranscriptionSegment.objects.create(
                        recording=audio_recording,
                        start_time=segment.get('start', 0),
                        end_time=segment.get('end', 0),
                        text=segment.get('text', ''),
                        confidence=None  # API doesn't provide confidence scores
                    )
            else:
                # If no segments, create one segment with full text
                TranscriptionSegment.objects.create(
                    recording=audio_recording,
                    start_time=0,
                    end_time=audio_recording.duration_seconds or 0,
                    text=response.text
                )
            
            audio_recording.is_processed = True
            audio_recording.save()
            
            return True
            
        except Exception as e:
            print(f"Error transcribing audio via API: {str(e)}")
            return False

# Use API processor by default
WhisperProcessor = OpenAIProcessor