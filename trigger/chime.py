#!/usr/bin/env python3
"""
Low-latency chime trigger script.
Queries database directly and uses mpg123 for audio playback.
"""
import os
import sys
import subprocess
import threading
import time

COOLDOWN_SECONDS = 3  # Minimum time between triggers

# Add the project directory to Python path
sys.path.insert(0, "/home/poduck/chime")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chime.settings")

import django
django.setup()

import RPi.GPIO as GPIO
import requests
from time import sleep
from django.conf import settings
from clips.models import Clip
from tracking.models import Track

SENSOR_PIN = 21


class ChimeTrigger:
    def __init__(self):
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.last_trigger_time = 0

    def get_next_clip(self):
        """Get the next clip to play, cycling through in order."""
        clips = list(Clip.objects.all().order_by("order"))
        if not clips:
            return None

        # Find the last played clip
        last_played_idx = -1
        for idx, clip in enumerate(clips):
            if clip.last_played:
                last_played_idx = idx
                break

        # Calculate next clip index (cycle back to 0 if at end)
        next_idx = (last_played_idx + 1) % len(clips)

        # Update last_played flags
        if last_played_idx >= 0:
            Clip.objects.filter(pk=clips[last_played_idx].pk).update(last_played=False)
        Clip.objects.filter(pk=clips[next_idx].pk).update(last_played=True)

        return clips[next_idx]

    def play_clip(self, clip):
        """Play a clip using mpg123 in a background thread."""
        file_path = os.path.join(settings.MEDIA_ROOT, str(clip.file))

        def _play():
            try:
                subprocess.run(['killall', 'mpg123'], stderr=subprocess.DEVNULL)
                subprocess.run(['killall', 'ffmpeg'], stderr=subprocess.DEVNULL)
                use_trim = clip.start_time > 0 or clip.end_time > 0
                if use_trim:
                    ffmpeg_cmd = ['ffmpeg', '-ss', str(clip.start_time)]
                    if clip.end_time > 0:
                        ffmpeg_cmd += ['-to', str(clip.end_time)]
                    ffmpeg_cmd += ['-i', file_path, '-f', 'mp3', '-loglevel', 'quiet', '-']
                    ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                    subprocess.run(['mpg123', '-q', '-a', 'hw:0,0', '-'], stdin=ffmpeg.stdout, timeout=60)
                    ffmpeg.stdout.close()
                else:
                    subprocess.run(['mpg123', '-q', '-a', 'hw:0,0', file_path], timeout=60)
            except Exception as e:
                print(f'Error playing clip: {e}')

        thread = threading.Thread(target=_play, daemon=True)
        thread.start()

    def send_notification(self):
        """Send Gotify notification (non-blocking, fire-and-forget)."""
        try:
            gotify_url = getattr(settings, "GOTIFY_URL", None)
            gotify_key = getattr(settings, "GOTIFY_API_KEY", None)
            if gotify_url and gotify_key:
                requests.post(
                    f"{gotify_url}/message?token={gotify_key}",
                    json={
                        "message": "Front door entry.",
                        "priority": 7,
                        "title": "Alert!"
                    },
                    timeout=2
                )
        except Exception as e:
            print(f"Gotify notification failed: {e}")

    def log_trigger(self):
        """Log the trigger event to the tracking database."""
        try:
            Track.objects.create(location="front_door")
            print("Logged trigger to tracking database")
        except Exception as e:
            print(f"Failed to log trigger: {e}")

    def trigger(self):
        """Handle a trigger event."""
        print("TRIGGER! Playing clip...")
        
        # Log to tracking database
        self.log_trigger()
        
        clip = self.get_next_clip()
        if clip:
            print(f"Playing: {clip.title}")
            self.play_clip(clip)

        # Send notification in background thread
        threading.Thread(target=self.send_notification, daemon=True).start()

    def run(self):
        """Main loop monitoring GPIO."""
        print(f"Chime trigger started. Monitoring GPIO pin {SENSOR_PIN}...")

        try:
            while True:
                current_time = time.time()
                sensor_triggered = GPIO.input(SENSOR_PIN)  # HIGH when triggered
                
                if sensor_triggered:
                    # Trigger immediately if cooldown has passed
                    if (current_time - self.last_trigger_time) >= COOLDOWN_SECONDS:
                        self.last_trigger_time = current_time
                        self.trigger()

                sleep(0.05)  # 50ms polling interval

        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            GPIO.cleanup()


if __name__ == "__main__":
    chime = ChimeTrigger()
    chime.run()
