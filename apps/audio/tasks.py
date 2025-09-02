from celery import shared_task
from .models import AudioRecording

@shared_task
def process_audio_recording(recording_id):
    """Background task to process audio recording with Whisper API"""
    try:
        # Try API processor first (lightweight)
        try:
            from .processors_api import OpenAIProcessor
            processor = OpenAIProcessor()
        except ImportError:
            # Fall back to local processor if available
            try:
                from .processors import WhisperProcessor
                processor = WhisperProcessor()
            except ImportError:
                print(f"No audio processor available for recording {recording_id}")
                return False
        
        recording = AudioRecording.objects.get(id=recording_id)
        success = processor.transcribe_audio(recording)
        
        if success:
            print(f"Successfully processed recording {recording_id}")
        else:
            print(f"Failed to process recording {recording_id}")
            
        return success
        
    except AudioRecording.DoesNotExist:
        print(f"Recording {recording_id} not found")
        return False