"""
AI-powered transcript processing using OpenAI GPT-4
Handles transcript cleanup, minutes generation, and action item extraction.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from django.conf import settings
from django.utils import timezone
from openai import OpenAI

logger = logging.getLogger(__name__)


class MeetingAIProcessor:
    """AI processor for meeting transcripts using OpenAI GPT-4"""

    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    def process_meeting_transcript(self, meeting_summary) -> bool:
        """
        Main processing function - cleans transcript and generates minutes

        Args:
            meeting_summary: MeetingSummary instance

        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Starting AI processing for meeting {meeting_summary.meeting.meeting_id}")

            # Mark processing as started
            meeting_summary.ai_processing_started_at = timezone.now()
            meeting_summary.save()

            if not meeting_summary.raw_transcript:
                logger.error("No raw transcript available for processing")
                return False

            # Step 1: Clean the transcript
            clean_transcript = self._clean_transcript(meeting_summary.raw_transcript)

            # Step 2: Generate meeting analysis
            analysis = self._analyze_meeting(clean_transcript, meeting_summary.meeting)

            # Step 3: Update the summary
            meeting_summary.clean_transcript = clean_transcript
            meeting_summary.executive_summary = analysis['executive_summary']
            meeting_summary.key_points = analysis['key_points']
            meeting_summary.action_items = analysis['action_items']
            meeting_summary.decisions_made = analysis['decisions_made']
            meeting_summary.participants_summary = analysis['participants_summary']

            # Mark as completed
            meeting_summary.is_ai_processed = True
            meeting_summary.ai_processing_completed_at = timezone.now()
            meeting_summary.save()

            logger.info(f"AI processing completed for meeting {meeting_summary.meeting.meeting_id}")
            return True

        except Exception as e:
            logger.error(f"AI processing failed for meeting {meeting_summary.meeting.meeting_id}: {e}")
            return False

    def _clean_transcript(self, raw_transcript: str) -> str:
        """Clean and format the raw transcript"""

        system_prompt = """You are a professional transcript editor. Your job is to clean up meeting transcripts while preserving all important content and speaker identification.

Guidelines:
1. Remove filler words (um, uh, ah, like, you know)
2. Fix grammar and add proper punctuation
3. Format as clear paragraphs with proper speaker labels
4. Preserve all meaningful content - don't summarize
5. Keep technical terms and specific details intact
6. Use "Speaker 1:", "Speaker 2:" format consistently
7. Make it readable while staying true to what was said

Return only the cleaned transcript."""

        user_prompt = f"""Please clean this meeting transcript:

{raw_transcript}

Make it professional and readable while preserving all important information."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective for cleanup tasks
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent formatting
                max_tokens=4000
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Transcript cleaning failed: {e}")
            return raw_transcript  # Return original if cleaning fails

    def _analyze_meeting(self, clean_transcript: str, meeting) -> Dict:
        """Analyze the meeting and extract structured information"""

        # Get agenda items with assigned participants
        agenda_context = self._build_agenda_context(meeting)

        meeting_context = f"""
Meeting Title: {meeting.title or 'Untitled Meeting'}
Meeting Date: {meeting.created_at.strftime('%Y-%m-%d')}
Host: {meeting.host.get_full_name() if meeting.host else 'Unknown'}
Duration: {self._estimate_duration(meeting)}

Agenda Items:
{agenda_context}
"""

        system_prompt = """You are an AI meeting assistant specialized in analyzing meeting transcripts and generating professional meeting minutes.

Your task is to analyze the transcript and extract:
1. Executive Summary (2-3 sentences)
2. Key Discussion Points (organized by agenda items when possible)
3. Action Items (specific tasks with smart owner assignment)
4. Decisions Made (concrete decisions reached)
5. Participant Analysis (general engagement patterns)

IMPORTANT - Action Item Assignment Logic:
- If discussion happens during a specific agenda item, assign related action items to that agenda item's owner
- If no agenda context, look for explicit mentions in transcript ("John will handle...", "Sarah, can you...")
- If no clear owner, leave as "TBD" for admin review
- Consider the context and relevance when making assignments

Return your analysis in valid JSON format with these exact keys:
- executive_summary (string)
- key_points (array of strings, organize by agenda topics when clear)
- action_items (array of objects with: task, owner, due_date, priority, agenda_item)
- decisions_made (array of strings)
- participants_summary (object with general stats, no speaker identification needed)

Be specific and actionable. Use agenda context to intelligently assign action items."""

        user_prompt = f"""Meeting Context:
{meeting_context}

Transcript:
{clean_transcript}

Please analyze this meeting and provide structured output in JSON format."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use full GPT-4 for complex analysis
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )

            # Parse JSON response
            analysis_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()

            analysis = json.loads(analysis_text)

            # Validate required fields
            required_fields = ['executive_summary', 'key_points', 'action_items', 'decisions_made', 'participants_summary']
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = [] if field != 'executive_summary' and field != 'participants_summary' else {}

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI analysis JSON: {e}")
            return self._get_default_analysis()
        except Exception as e:
            logger.error(f"Meeting analysis failed: {e}")
            return self._get_default_analysis()

    def _estimate_duration(self, meeting) -> str:
        """Estimate meeting duration based on available data"""
        if meeting.started_at and meeting.ended_at:
            duration = meeting.ended_at - meeting.started_at
            minutes = int(duration.total_seconds() / 60)
            return f"{minutes} minutes"
        elif meeting.recordings.exists():
            # Estimate from recording timestamps
            first_recording = meeting.recordings.earliest('created_at')
            last_recording = meeting.recordings.latest('created_at')
            duration = last_recording.created_at - first_recording.created_at
            minutes = int(duration.total_seconds() / 60)
            return f"~{minutes} minutes"
        else:
            return "Duration unknown"

    def _get_default_analysis(self) -> Dict:
        """Return default analysis structure if AI processing fails"""
        return {
            'executive_summary': 'Meeting analysis could not be completed automatically. Please review transcript manually.',
            'key_points': [],
            'action_items': [],
            'decisions_made': [],
            'participants_summary': {}
        }