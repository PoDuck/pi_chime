# Door Chime Customizer

A Raspberry Pi-based door chime system that plays custom audio clips when triggered by a GPIO sensor. Perfect for replacing boring doorbells with video game sounds, music clips, or any audio you like.

## Features

- **Web Interface** - Upload, manage, and reorder audio clips from any device on your network
- **Drag-and-Drop Ordering** - Easily reorder clips with smooth animations
- **Clip Rotation** - Automatically cycles through your playlist with each trigger
- **Analytics Dashboard** - Track door activity by day of week and hour
- **Push Notifications** - Optional Gotify integration for mobile alerts
- **GPIO Trigger** - Hardware trigger via magnetic door sensor or button
- **Dark/Light Mode** - Toggle between themes in the UI

## Requirements

### Hardware
- Raspberry Pi (tested on Pi 4, should work on Pi 3/Zero 2)
- Audio output (3.5mm jack, HDMI, or USB audio)
- Magnetic door sensor or momentary switch
- Speaker/amplifier

### Software
- Raspberry Pi OS Lite (Bookworm or newer recommended)
- Python 3.9+
- Apache2 with mod_wsgi
- mpg123 (audio player)

## Installation

### 1. Initial Raspberry Pi Setup

Install Raspberry Pi OS Lite using the Raspberry Pi Imager. During setup:
- Set a hostname (e.g., `chime.local`)
- Configure WiFi credentials
- Set username and password
- Enable SSH

Boot the Pi and update the system:

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install System Dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv git apache2 \
    libapache2-mod-wsgi-py3 mpg123
```

**Note:** `mpg123` is required for audio playback. It's lightweight and provides low-latency MP3 playback.

### 3. Clone the Repository

```bash
cd ~
git clone https://github.com/yourusername/chime.git
cd chime
```

### 4. Set Up Python Virtual Environment

```bash
python3 -m venv ~/.virtualenvs/chime
source ~/.virtualenvs/chime/bin/activate
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
nano ~/chime/.env
```

Add the following (adjust values for your setup):

```bash
DEBUG=off
SECRET_KEY="your-random-secret-key-here"
LOCAL_DOMAIN=chime.local
LOCAL_PORT=80
ON_PI=True
LOCAL_TIMEZONE=America/New_York

# Optional: Gotify push notifications
GOTIFY_URL=https://your-gotify-server.com
GOTIFY_KEY="your-gotify-app-token"
```

### 6. Initialize the Database

```bash
cd ~/chime
source ~/.virtualenvs/chime/bin/activate
./manage.py migrate
./manage.py collectstatic --noinput
mkdir -p media/clips media/thumbnails
```

### 7. Configure Apache

Add your user to the www-data group:

```bash
sudo usermod -aG www-data $USER
```

Edit the Apache configuration:

```bash
sudo nano /etc/apache2/sites-enabled/000-default.conf
```

Replace the contents with (change `poduck` to your username):

```apache
Alias /static /home/poduck/chime/static
<Directory /home/poduck/chime/static>
    Require all granted
</Directory>

Alias /media /home/poduck/chime/media
<Directory /home/poduck/chime/media>
    Require all granted
</Directory>

<Directory /home/poduck/chime/chime>
    <Files wsgi.py>
        Require all granted
    </Files>
</Directory>

WSGIDaemonProcess django python-path=/home/poduck/chime python-home=/home/poduck/.virtualenvs/chime
WSGIProcessGroup django
WSGIScriptAlias / /home/poduck/chime/chime/wsgi.py

<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html
    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

Test and restart Apache:

```bash
sudo apache2ctl configtest
sudo systemctl restart apache2
```

### 8. Set File Permissions

```bash
sudo chown -R www-data:www-data ~/chime
sudo chmod -R 775 ~/chime
```

### 9. Configure Audio Output

Ensure your audio output is configured correctly:

```bash
# List audio devices
aplay -l

# Test audio (should hear white noise)
speaker-test -t wav -c 2 -l 1

# If using 3.5mm jack, you may need to force output
sudo raspi-config
# Navigate to: System Options > Audio > Choose output
```

For best results with mpg123, identify your audio device:

```bash
# The trigger script uses hw:0,0 by default
# Modify /home/poduck/chime/trigger/chime.py if your device differs
```

### 10. Set Up the Trigger Service

Create the systemd service file:

```bash
sudo nano /etc/systemd/system/chime-trigger.service
```

Add the following (change `poduck` to your username):

```ini
[Unit]
Description=Chime Door Trigger Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/poduck/chime
ExecStart=/home/poduck/.virtualenvs/chime/bin/python /home/poduck/chime/trigger/chime.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable chime-trigger
sudo systemctl start chime-trigger
```

Check the service status:

```bash
sudo systemctl status chime-trigger
```

## GPIO Wiring

The trigger uses **BCM GPIO pin 21** (physical pin 40) with an internal pull-up resistor.

### Wiring Diagram

```
Raspberry Pi GPIO Header (looking at Pi with USB ports facing down)
                    
   3V3  (1)  (2)  5V
 GPIO2  (3)  (4)  5V
 GPIO3  (5)  (6)  GND
 GPIO4  (7)  (8)  GPIO14
   GND  (9)  (10) GPIO15
GPIO17 (11)  (12) GPIO18
GPIO27 (13)  (14) GND
GPIO22 (15)  (16) GPIO23
   3V3 (17)  (18) GPIO24
GPIO10 (19)  (20) GND
 GPIO9 (21)  (22) GPIO25
GPIO11 (23)  (24) GPIO8
   GND (25)  (26) GPIO7
 GPIO0 (27)  (28) GPIO1
 GPIO5 (29)  (30) GND
 GPIO6 (31)  (32) GPIO12
GPIO13 (33)  (34) GND
GPIO19 (35)  (36) GPIO16
GPIO26 (37)  (38) GPIO20
   GND (39)  (40) GPIO21  <-- SENSOR PIN
```

### Connection

Connect your magnetic door sensor or momentary switch:
- One wire to **Pin 40** (GPIO21)
- Other wire to **Pin 39** (GND)

### Trigger Behavior

- **Trigger on HIGH**: The chime triggers immediately when GPIO21 goes HIGH (sensor activated)
- **3-second cooldown**: After triggering, additional triggers are ignored for 3 seconds to prevent multiple clips from playing simultaneously when multiple people come through the door
- **Instant response**: No delay on initial trigger - the clip plays immediately when the sensor is activated

**Typical magnetic door sensor behavior:**
- Door closed → Magnet near reed switch → Switch closed → GPIO21 reads LOW
- Door opens → Magnet moves away → Switch opens → Internal pull-up pulls GPIO21 HIGH → **Chime triggers**

## Usage

### Web Interface

Access the web interface at `http://chime.local` (or your configured hostname).

- **Clip Library** - View, play, edit, and delete clips
- **Add Clip** - Upload new MP3 files with title, game name, and thumbnail
- **Analytics** - View door trigger patterns by day and hour
- **Trigger Chime** - Manually trigger via the nav button

### Manual Trigger

You can also trigger the chime via API:

```bash
curl http://chime.local/clips/trigger/
```

## Troubleshooting

### No Sound

1. Check audio device: `aplay -l`
2. Test mpg123 directly: `mpg123 /path/to/clip.mp3`
3. Check volume: `alsamixer`
4. Verify the audio device in trigger script matches your setup

### Trigger Not Working

1. Check service status: `sudo systemctl status chime-trigger`
2. View logs: `sudo journalctl -u chime-trigger -f`
3. Test GPIO manually:
   ```bash
   python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP); print(GPIO.input(21))"
   ```
   Should print `1` (HIGH) when door closed, `0` (LOW) when open.

### Web Interface 500 Error

1. Check Apache logs: `sudo tail -f /var/log/apache2/error.log`
2. Verify permissions: `ls -la ~/chime`
3. Test Django: `cd ~/chime && source ~/.virtualenvs/chime/bin/activate && ./manage.py check`

### Analytics Not Showing Data

Data only appears after triggers have been logged. Open the door a few times to generate data.

## Push Notifications (Optional)

To receive push notifications when the door opens:

1. Set up a [Gotify](https://gotify.net/) server
2. Create an application in Gotify and get the token
3. Add to your `.env` file:
   ```bash
   GOTIFY_URL=https://your-gotify-server.com
   GOTIFY_KEY="your-app-token"
   ```
4. Restart the trigger service: `sudo systemctl restart chime-trigger`

## License

MIT License - See LICENSE file for details.
