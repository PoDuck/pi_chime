import RPi.GPIO as GPIO
import requests
from time import sleep
from pushbullet import Pushbullet
from django.conf import settings
from clips.models import Clip

pb = Pushbullet(settings.env('PUSHBULLET_KEY'))

sensor_pin = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

play_clip = True

try:
    while True:
        if GPIO.input(sensor_pin) and play_clip:
            clips = Clip.objects.all().order_by('order')
            last_played = Clip.objects.filter(last_played=True)
            if list(clips)[-1].last_played or not last_played:
                play_next = True
                if list(clips)[-1].last_played:
                    list(clips)[-1].last_played = False
            for clip in clips:
                if clip.last_played:
                    play_next = True
                    clip.last_played = False
                    clip.save()
                elif play_next:
                    play_clip(clip)
                    clip.last_played = True
                    break
            for clip in clips:
                clip.save()
            r = requests.get(
                'http://' + env('LOCAL_DOMAIN') + ':' + env('LOCAL_PORT', default='80') + '/clips/trigger/')
            dev = pb.get_device('Samsung SM-N975U')
            push = dev.push_note("Alert!!", "Someone came in the door")
            sleep(3)
        if not GPIO.input(sensor_pin):
            play_clip = True
except KeyboardInterrupt:
    GPIO.cleanup()
