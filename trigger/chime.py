import RPi.GPIO as GPIO
import requests
from time import sleep

sensor_pin = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

play_clip = True

try:
    while True:
        if GPIO.input(sensor_pin) and play_clip:
            r = requests.get('http://localhost/clips/trigger/')
            sleep(3)
        if not GPIO.input(sensor_pin):
            play_clip = True
except KeyboardInterrupt:
    GPIO.cleanup()
