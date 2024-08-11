import RPi.GPIO as GPIO
import requests
from time import sleep
from django.conf import settings

sensor_pin = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

play_clip = True

try:
    while True:
        if GPIO.input(sensor_pin) and play_clip:
            r = requests.get('http://localhost/clips/trigger/')
            requests.post(f"https://gotify.talova.com/message?token={settings.GOTIFY_API_KEY}", json={
                "message": "Front door entry.",
                "priority": 7,
                "title": "Alert!"
            })
            push = dev.push_note("Alert!!", "Someone came in the door")
            sleep(3)
        if not GPIO.input(sensor_pin):
            play_clip = True
except KeyboardInterrupt:
    GPIO.cleanup()
