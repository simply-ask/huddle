from celery import shared_task
from .models import AudioRecording
from .processors import WhisperProcessor

@shared_task
def process_audio_recording(recording_id):
    """Background task to process audio recording with Whisper"""
    try:
        recording = AudioRecording.objects.get(id=recording_id)
        processor = WhisperProcessor()
        
        success = processor.transcribe_audio(recording)
        
        if success:
            print(f"Successfully processed recording {recording_id}")
        else:
            print(f"Failed to process recording {recording_id}")
            
        return success
        
    except AudioRecording.DoesNotExist:
        print(f"Recording {recording_id} not found")
        return False