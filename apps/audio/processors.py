import tempfile
import os
from .models import AudioRecording, TranscriptionSegment

try:
    import whisper
    from pydub import AudioSegment
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    # For development/migration purposes when these packages aren't installed
    AUDIO_PROCESSING_AVAILABLE = False

class WhisperProcessor:
    def __init__(self, model_name='base'):
        if not AUDIO_PROCESSING_AVAILABLE:
            raise ImportError("Audio processing packages not available")
        self.model = whisper.load_model(model_name)
    
    def transcribe_audio(self, audio_recording):
        """Transcribe audio using Whisper and save segments"""
        try:
            # Convert audio to format suitable for Whisper
            audio_file_path = audio_recording.audio_file.path
            
            # Load and process audio
            result = self.model.transcribe(audio_file_path, word_timestamps=True)
            
            # Create transcription segments
            for segment in result['segments']:
                TranscriptionSegment.objects.create(
                    recording=audio_recording,
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=segment['text'],
                    confidence=segment.get('avg_logprob')
                )
            
            audio_recording.is_processed = True
            audio_recording.save()
            
            return True
            
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return False
    
    def merge_audio_files(self, recordings):
        """Merge multiple audio recordings from same meeting"""
        if not recordings:
            return None
        
        combined = AudioSegment.empty()
        
        for recording in recordings:
            try:
                audio = AudioSegment.from_file(recording.audio_file.path)
                combined += audio
            except Exception as e:
                print(f"Error merging audio file {recording.id}: {str(e)}")
                continue
        
        return combined