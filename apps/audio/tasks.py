from celery import shared_task
from .models import AudioRecording
from .processors import AudioProcessor

@shared_task
def process_audio_recording(recording_id):
    """Background task to process audio recording with Deepgram"""
    try:
        recording = AudioRecording.objects.get(id=recording_id)
        
        # Process with Deepgram
        processor = AudioProcessor()
        success = processor.transcribe_audio(recording)
        
        if success:
            print(f"Successfully processed recording {recording_id} via Deepgram")
        else:
            print(f"Failed to process recording {recording_id} - will retry if configured")
            
        return success
        
    except AudioRecording.DoesNotExist:
        print(f"Recording {recording_id} not found")
        return False
    except ValueError as e:
        print(f"Configuration error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error processing recording {recording_id}: {e}")
        return False