"""
Temporary debug command to check audio file paths and fix processing issues.
Run: python manage.py debug_audio_files
"""

from django.core.management.base import BaseCommand
from apps.audio.models import AudioRecording
from apps.audio.tasks import process_audio_recording
import os
import glob
from pathlib import Path


class Command(BaseCommand):
    help = 'Debug audio file paths and process recordings'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("🔍 AUDIO FILE DEBUG TOOL")
        self.stdout.write("=" * 60)

        # Get latest recording
        try:
            recording = AudioRecording.objects.latest('created_at')
        except AudioRecording.DoesNotExist:
            self.stdout.write(self.style.ERROR('No recordings found!'))
            return

        self.stdout.write(f"\n📀 Latest Recording:")
        self.stdout.write(f"  ID: {recording.id}")
        self.stdout.write(f"  Created: {recording.created_at}")
        self.stdout.write(f"  Processed: {recording.is_processed}")
        self.stdout.write(f"  Meeting: {recording.meeting.meeting_id}")

        self.stdout.write(f"\n📁 File Information:")
        self.stdout.write(f"  DB Name: {recording.audio_file.name}")
        self.stdout.write(f"  DB Path: {recording.audio_file.path}")
        self.stdout.write(f"  DB URL: {recording.audio_file.url}")

        # Check if file exists at the path
        file_exists = os.path.exists(recording.audio_file.path)
        self.stdout.write(f"  File exists at DB path: {file_exists}")

        # Check the media directory
        self.stdout.write(f"\n🗂️ Directory Scan:")
        base_path = Path(recording.audio_file.path).parent
        self.stdout.write(f"  Looking in: {base_path}")

        if os.path.exists(base_path):
            files = list(base_path.glob("*"))
            if files:
                self.stdout.write(f"  Found {len(files)} file(s):")
                for f in files:
                    size = os.path.getsize(f) / 1024  # Convert to KB
                    self.stdout.write(f"    - {f.name} ({size:.1f} KB)")
            else:
                self.stdout.write(self.style.WARNING("  Directory exists but is empty!"))
        else:
            self.stdout.write(self.style.ERROR(f"  Directory does not exist: {base_path}"))

        # Try to find the actual file
        self.stdout.write(f"\n🔎 Searching for actual file:")
        file_path = Path(recording.audio_file.path)
        directory = file_path.parent
        base_name = file_path.stem
        extension = file_path.suffix

        # Try different patterns
        patterns = [
            str(directory / f"{base_name}{extension}"),
            str(directory / f"{base_name}_*{extension}"),
            str(directory / f"*{base_name}*{extension}"),
        ]

        actual_file = None
        for pattern in patterns:
            self.stdout.write(f"  Trying pattern: {pattern}")
            matches = glob.glob(pattern)
            if matches:
                actual_file = matches[0]
                self.stdout.write(self.style.SUCCESS(f"  ✅ Found file: {actual_file}"))
                break

        if not actual_file:
            self.stdout.write(self.style.ERROR("  ❌ Could not find audio file!"))

            # Check if we can find it using Django's storage
            self.stdout.write(f"\n💾 Django Storage Check:")
            try:
                with recording.audio_file.open('rb') as f:
                    size = len(f.read()) / 1024
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Django can access file! Size: {size:.1f} KB"))
                    actual_file = "DJANGO_STORAGE"
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Django storage error: {e}"))

        # Process the recording if not processed and file found
        if not recording.is_processed and actual_file:
            self.stdout.write(f"\n🎬 Processing Recording:")
            user_input = input("  Do you want to process this recording now? (y/n): ")

            if user_input.lower() == 'y':
                self.stdout.write("  Queuing for processing...")
                result = process_audio_recording.delay(recording.id)
                self.stdout.write(self.style.SUCCESS(f"  ✅ Task queued: {result.id}"))
                self.stdout.write("  Check Celery logs for processing status")
        else:
            if recording.is_processed:
                self.stdout.write(f"\n✅ Recording already processed")
                self.stdout.write(f"  Segments: {recording.segments.count()}")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Debug complete!")