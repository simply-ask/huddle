"""
Audio processing using OpenAI Whisper API
"""
import os
from .models import AudioRecording, TranscriptionSegment
from openai import OpenAI

class AudioProcessor:
    """Process audio using OpenAI's Whisper API"""
    
    def __init__(self):
        api_key = os.environ.get('OPENAI_API_KEY', '')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured in environment variables")
            
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