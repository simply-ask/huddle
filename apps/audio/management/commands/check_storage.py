"""
Check storage configuration and fix audio file access
Run: python manage.py check_storage
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from apps.audio.models import AudioRecording
from apps.audio.tasks import process_audio_recording
import os


class Command(BaseCommand):
    help = 'Check storage configuration and audio file access'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("🔍 STORAGE CONFIGURATION CHECK")
        self.stdout.write("=" * 60)

        # Check Django settings
        self.stdout.write("\n📋 Django Settings:")
        self.stdout.write(f"  MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"  MEDIA_URL: {settings.MEDIA_URL}")
        self.stdout.write(f"  DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")

        # Check for cloud storage
        if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
            self.stdout.write(self.style.SUCCESS(f"  ☁️ Using S3/Spaces: {settings.AWS_STORAGE_BUCKET_NAME}"))

        if hasattr(settings, 'AWS_S3_ENDPOINT_URL'):
            self.stdout.write(f"  Endpoint: {settings.AWS_S3_ENDPOINT_URL}")

        # Get latest recording
        try:
            recording = AudioRecording.objects.latest('created_at')
        except AudioRecording.DoesNotExist:
            self.stdout.write(self.style.ERROR('\nNo recordings found!'))
            return

        self.stdout.write(f"\n📀 Latest Recording:")
        self.stdout.write(f"  ID: {recording.id}")
        self.stdout.write(f"  Created: {recording.created_at}")
        self.stdout.write(f"  Processed: {recording.is_processed}")
        self.stdout.write(f"  File name: {recording.audio_file.name}")

        # Check storage access
        self.stdout.write(f"\n💾 Storage Access Test:")

        # Check if file exists using storage API
        exists = default_storage.exists(recording.audio_file.name)
        self.stdout.write(f"  File exists in storage: {exists}")

        if exists:
            # Get URL
            try:
                url = default_storage.url(recording.audio_file.name)
                self.stdout.write(self.style.SUCCESS(f"  ✅ URL: {url}"))
            except Exception as e:
                self.stdout.write(f"  URL error: {e}")

            # Try to read file
            try:
                with default_storage.open(recording.audio_file.name, 'rb') as f:
                    content = f.read()
                    size_kb = len(content) / 1024
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Can read file! Size: {size_kb:.1f} KB"))

                    # Save to temp file for processing
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
                        tmp.write(content)
                        temp_path = tmp.name
                        self.stdout.write(f"  📁 Temp file created: {temp_path}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Read error: {e}"))
        else:
            self.stdout.write(self.style.ERROR("  ❌ File not found in storage!"))

            # Try alternative paths
            self.stdout.write("\n🔎 Trying alternative names:")
            import re
            base_name = recording.audio_file.name.replace('.webm', '')

            # List files in the directory
            try:
                dir_path = os.path.dirname(recording.audio_file.name)
                files = default_storage.listdir(dir_path)[1]  # [0] is dirs, [1] is files
                self.stdout.write(f"  Files in {dir_path}:")
                for f in files:
                    if 'recording' in f:
                        full_path = os.path.join(dir_path, f)
                        self.stdout.write(f"    - {f}")
                        # Check if this is our file
                        if base_name in full_path:
                            self.stdout.write(self.style.SUCCESS(f"  ✅ Likely match: {full_path}"))
            except Exception as e:
                self.stdout.write(f"  Cannot list directory: {e}")

        # Offer to process
        if not recording.is_processed and exists:
            self.stdout.write(f"\n🎬 Process Recording?")
            self.stdout.write("  The file is accessible via Django storage.")
            user_input = input("  Process this recording now? (y/n): ")

            if user_input.lower() == 'y':
                self.stdout.write("  Queuing for processing...")
                result = process_audio_recording.delay(recording.id)
                self.stdout.write(self.style.SUCCESS(f"  ✅ Task queued: {result.id}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Storage check complete!")