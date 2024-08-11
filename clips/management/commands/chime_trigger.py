from django.core.management.base import BaseCommand
from time import sleep
from clips.models import Clip
from clips.views import play_clip
from django.conf import settings
import requests
from tracking.models import Track
try:
    import RPi.GPIO as GPIO
    on_pi = True
except RuntimeError:
    from pynput import keyboard
    on_pi = False


q_pressed = False
space_pressed = False


def on_press(key):
    try:
        if key.char == 'q':
            global q_pressed
            q_pressed = True
    except AttributeError:
        if key == keyboard.Key.space:
            global space_pressed
            space_pressed = True


def on_release(key):
    pass


if not on_pi:
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()


class Command(BaseCommand):
    help = "Runs chime detection"

    def handle(self, *args, **options):
        global q_pressed
        global space_pressed
        # pb = Pushbullet(settings.PUSHBULLET_API_KEY)
        play = False  # for detecting trigger
        if on_pi:
            sensor_pin = 21
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        try:
            while True:
                if not on_pi:
                    if space_pressed:
                        break
                    if q_pressed:
                        q_pressed = False
                        play = True
                        Track.objects.create()
                else:
                    if GPIO.input(sensor_pin):  # Sensor is tripped
                        play = True
                        Track.objects.create()
                if play:
                    play = False  # reset play
                    play_next = False  # Play next clip in list default False
                    clips = Clip.objects.all().order_by('order')
                    last_played = Clip.objects.filter(last_played=True)
                    # If the last clip was the last played, or no clips have been played,
                    # Allows the first clip in the list to be played
                    if list(clips)[-1].last_played or not last_played:
                        play_next = True  # Ensure next clip will be played
                        # if the last clip in the list was the last played clip, reset it to false
                        if list(clips)[-1].last_played:
                            list(clips)[-1].last_played = False
                    for clip in clips:
                        # if the current clip was the last played clip, play the next clip.
                        if clip.last_played:
                            play_next = True
                            clip.last_played = False
                        elif play_next:
                            play_clip(clip)
                            clip.last_played = True
                            break
                    for clip in clips:
                        clip.save()
                    # Send signal to pushbullet
                    requests.post(f"https://gotify.talova.com/message?token={settings.GOTIFY_API_KEY}", json={
                        "message": "Front door entry.",
                        "priority": 7,
                        "title": "Alert!"
                    })
                    # Wait at least 3 seconds before allowing chime to be tripped again.
                    sleep(3)
        except KeyboardInterrupt:
            if on_pi:
                GPIO.cleanup()
