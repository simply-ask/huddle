"""
Audio processing using Deepgram for transcription with speaker diarization
"""
import os
import logging
from django.utils import timezone
from .models import AudioRecording, TranscriptionSegment, MeetingSummary
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Process audio using Deepgram API with speaker diarization"""
    
    def __init__(self):
        # Initialize Deepgram client
        self.deepgram_api_key = os.environ.get('DEEPGRAM_API_KEY', '')
        if not self.deepgram_api_key:
            raise ValueError("DEEPGRAM_API_KEY not configured in environment variables")
        
        self.deepgram_client = DeepgramClient(self.deepgram_api_key)
    
    def transcribe_audio(self, audio_recording):
        """Transcribe audio using Deepgram with speaker diarization"""
        # Mark processing started
        audio_recording.processing_started_at = timezone.now()
        audio_recording.save()
        
        try:
            success = self._transcribe_with_deepgram(audio_recording)
            
            if success:
                audio_recording.is_processed = True
                audio_recording.processing_completed_at = timezone.now()
                audio_recording.save()
                
                # Generate meeting summary if all recordings are processed
                self._check_and_generate_summary(audio_recording.meeting)
            
            return success
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return False
    
    def _transcribe_with_deepgram(self, audio_recording, retry_count=0):
        """Transcribe audio using Deepgram API with retry logic"""
        max_retries = 3
        
        try:
            logger.info(f"Starting Deepgram transcription for recording {audio_recording.id} (attempt {retry_count + 1})")
            
            # Read the audio file using Django storage API (works with both local and cloud storage)
            logger.info(f"🎵 Reading file using Django storage: {audio_recording.audio_file.name}")

            from django.core.files.storage import default_storage

            # Check if file exists in storage
            if not default_storage.exists(audio_recording.audio_file.name):
                logger.error(f"🎵 File not found in storage: {audio_recording.audio_file.name}")

                # Try alternative names with suffix
                import os
                dir_path = os.path.dirname(audio_recording.audio_file.name)
                base_name = os.path.basename(audio_recording.audio_file.name).replace('.webm', '')

                try:
                    _, files = default_storage.listdir(dir_path)
                    for f in files:
                        if base_name in f and f.endswith('.webm'):
                            alternative_path = os.path.join(dir_path, f)
                            logger.info(f"🎵 Found alternative file: {alternative_path}")
                            audio_recording.audio_file.name = alternative_path
                            audio_recording.save()
                            break
                except Exception as e:
                    logger.error(f"🎵 Cannot list directory: {e}")
                    raise FileNotFoundError(f"Audio file not found in storage: {audio_recording.audio_file.name}")

            # Read the file from storage (works with local files, S3, Spaces, etc.)
            try:
                with default_storage.open(audio_recording.audio_file.name, 'rb') as audio_file:
                    buffer_data = audio_file.read()
                logger.info(f"🎵 Successfully read {len(buffer_data) / 1024:.1f} KB from storage")
            except Exception as e:
                logger.error(f"🎵 Failed to read from storage: {e}")
                raise
            
            payload: FileSource = {
                "buffer": buffer_data,
            }
            
            # Configure Deepgram options for best results
            options = PrerecordedOptions(
                model="nova-2",  # Best model for accuracy
                language="en",
                smart_format=True,  # Better formatting
                punctuate=True,  # Add punctuation
                paragraphs=True,  # Paragraph formatting
                diarize=True,  # Enable speaker diarization
                utterances=True,  # Group by utterances
                numerals=True,  # Format numbers
            )
            
            # Make the API request
            logger.info("Calling Deepgram API...")
            response = self.deepgram_client.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )
            
            # Store raw response for debugging
            audio_recording.transcription_raw = response.to_dict()
            audio_recording.transcription_service = 'deepgram'
            
            # Get the results
            results = response.results
            if not results or not results.channels:
                logger.error("No results from Deepgram")
                
                # Retry if we haven't exceeded max retries
                if retry_count < max_retries - 1:
                    logger.info(f"Retrying transcription... (attempt {retry_count + 2})")
                    return self._transcribe_with_deepgram(audio_recording, retry_count + 1)
                
                return False
            
            channel = results.channels[0]
            
            # Store request ID if available
            if hasattr(response, 'metadata') and hasattr(response.metadata, 'request_id'):
                audio_recording.deepgram_request_id = response.metadata.request_id
            
            # Process utterances with speaker diarization
            segments_created = 0
            if hasattr(channel, 'alternatives') and channel.alternatives:
                alternative = channel.alternatives[0]
                
                # Process paragraphs/utterances with speakers
                if hasattr(alternative, 'paragraphs') and alternative.paragraphs:
                    for paragraph in alternative.paragraphs.paragraphs:
                        for sentence in paragraph.sentences:
                            # Create segment with speaker info
                            speaker_id = f"speaker_{sentence.speaker}" if hasattr(sentence, 'speaker') else None
                            
                            TranscriptionSegment.objects.create(
                                recording=audio_recording,
                                start_time=sentence.start,
                                end_time=sentence.end,
                                text=sentence.text,
                                confidence=None,
                                speaker_id=speaker_id,
                                speaker_name=self._identify_speaker(audio_recording.meeting, speaker_id)
                            )
                            
                            segments_created += 1
                            
                            if segments_created <= 3:  # Log first few segments
                                logger.info(f"Created segment: Speaker {speaker_id}: {sentence.text[:50]}...")
            
            audio_recording.save()
            logger.info(f"Deepgram transcription completed for recording {audio_recording.id} - {segments_created} segments created")

            # Trigger AI processing after successful transcription
            self._trigger_ai_processing_if_ready(audio_recording.meeting)

            return True
            
        except Exception as e:
            logger.error(f"Deepgram transcription error: {str(e)}")
            
            # Retry on failure if we haven't exceeded max retries
            if retry_count < max_retries - 1:
                logger.info(f"Retrying after error... (attempt {retry_count + 2})")
                return self._transcribe_with_deepgram(audio_recording, retry_count + 1)
            
            logger.error(f"Failed after {max_retries} attempts")
            return False
    
    def _identify_speaker(self, meeting, speaker_id):
        """Identify speaker based on voice profiles or speaker number"""
        if not speaker_id:
            return "Unknown Speaker"
        
        # Extract speaker number
        speaker_num = speaker_id.replace("speaker_", "")
        
        # TODO: In the future, we can match this with voice profiles
        # For now, return a friendly speaker label
        return f"Speaker {int(speaker_num) + 1}"  # Use 1-based numbering for users
    
    def _check_and_generate_summary(self, meeting):
        """Check if all recordings are processed and generate summary"""
        try:
            # Check if all recordings for this meeting are processed
            all_recordings = meeting.recordings.all()
            if not all_recordings.exists():
                return
            
            if not all(r.is_processed for r in all_recordings):
                logger.info(f"Not all recordings processed for meeting {meeting.meeting_id}")
                return
            
            # Generate full transcript
            logger.info(f"Generating meeting summary for {meeting.meeting_id}")
            
            # Collect all segments ordered by time
            all_segments = []
            for recording in all_recordings:
                segments = recording.segments.all().order_by('start_time')
                all_segments.extend(segments)
            
            # Sort all segments by start time
            all_segments.sort(key=lambda x: x.start_time)
            
            # Build full transcript with speaker labels
            transcript_lines = []
            current_speaker = None
            
            for segment in all_segments:
                speaker = segment.speaker_name or "Unknown"
                if speaker != current_speaker:
                    transcript_lines.append(f"\n{speaker}:")
                    current_speaker = speaker
                transcript_lines.append(segment.text)
            
            full_transcript = " ".join(transcript_lines)
            
            # Create or update meeting summary
            summary, created = MeetingSummary.objects.get_or_create(
                meeting=meeting,
                defaults={'full_transcript': full_transcript}
            )
            
            if not created:
                summary.full_transcript = full_transcript
                summary.save()
            
            # TODO: Generate AI summary using GPT-4 if needed for summaries/action items
            # This would require OpenAI API key but only for AI summaries, not transcription
            
            logger.info(f"Meeting summary {'created' if created else 'updated'} for {meeting.meeting_id}")
            
        except Exception as e:
            logger.error(f"Error generating meeting summary: {str(e)}")
    def _trigger_ai_processing_if_ready(self, meeting):
        """Trigger AI processing if all recordings for meeting are processed"""
        try:
            total_recordings = meeting.recordings.count()
            processed_recordings = meeting.recordings.filter(is_processed=True).count()

            logger.info(f"Meeting {meeting.meeting_id}: {processed_recordings}/{total_recordings} recordings processed")

            # If all recordings are processed, trigger AI analysis
            if processed_recordings > 0 and processed_recordings == total_recordings:
                logger.info(f"All recordings processed for meeting {meeting.meeting_id}, triggering AI analysis")

                # Import here to avoid circular imports
                from .tasks import process_meeting_ai_analysis

                # Queue AI processing
                process_meeting_ai_analysis.delay(meeting.meeting_id)

        except Exception as e:
            logger.error(f"Error checking AI processing readiness: {e}")
