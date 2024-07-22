import RPi.GPIO as GPIO
import requests
from time import sleep
from pushbullet import Pushbullet
import environ
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

pb = env('PUSHBULLET_KEY')

sensor_pin = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

play_clip = True

try:
    while True:
        if GPIO.input(sensor_pin) and play_clip:
            r = requests.get('http://' + env('LOCAL_DOMAIN') + env('LOCAL_PORT') + '/clips/trigger/')
            dev = pb.get_device('Samsung SM-N975U')
            push = dev.push_note("Alert!!", "Someone came in the door")
            sleep(3)
        if not GPIO.input(sensor_pin):
            play_clip = True
except KeyboardInterrupt:
    GPIO.cleanup()
