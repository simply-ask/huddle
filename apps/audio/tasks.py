from celery import shared_task
from .models import AudioRecording, MeetingSummary
from .processors import AudioProcessor
from .ai_processor import MeetingAIProcessor

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


@shared_task
def process_meeting_ai_analysis(meeting_id):
    """Background task to process meeting with AI for cleanup and minutes generation"""
    try:
        from apps.meetings.models import Meeting

        meeting = Meeting.objects.get(meeting_id=meeting_id)

        # Get or create meeting summary
        summary, created = MeetingSummary.objects.get_or_create(
            meeting=meeting,
            defaults={'raw_transcript': ''}  # Will be populated below
        )

        # If already processed, skip
        if summary.is_ai_processed:
            print(f"Meeting {meeting_id} already AI processed")
            return True

        # Compile full transcript from all processed recordings
        transcript_parts = []
        for recording in meeting.recordings.filter(is_processed=True):
            for segment in recording.segments.all().order_by('start_time'):
                speaker = segment.speaker_name or 'Unknown Speaker'
                transcript_parts.append(f"{speaker}: {segment.text}")

        if not transcript_parts:
            print(f"No processed recordings found for meeting {meeting_id}")
            return False

        # Set raw transcript
        summary.raw_transcript = '\n'.join(transcript_parts)
        summary.save()

        # Process with AI
        ai_processor = MeetingAIProcessor()
        success = ai_processor.process_meeting_transcript(summary)

        if success:
            print(f"Successfully AI processed meeting {meeting_id}")
            # Auto-complete the meeting if it was active
            if meeting.is_active:
                meeting.end_meeting()
                print(f"Auto-completed meeting {meeting_id}")
        else:
            print(f"Failed to AI process meeting {meeting_id}")

        return success

    except Meeting.DoesNotExist:
        print(f"Meeting {meeting_id} not found")
        return False
    except Exception as e:
        print(f"Unexpected error AI processing meeting {meeting_id}: {e}")
        return False