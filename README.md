## Description

This gives you the ability to setup a triggered sound to play on a raspberry pi.  The initial reason for me to make this was to change the terrible sound that my ancient door chime made.  It can be triggered by anything, for any reason though.

## Features

Remote upload of sound clips.
Ordering, updating, and deleting of sound clips.
Remote triggering of device.

# Installation instructions

This app was built on django.  It runs as a wsgi application using a web server.  I will use Apache as the server in these instructions.

This app was meant to run on a lan, behind a firewall/router, where people from the internet can't access it.  I did nothing to enable this app over the internet.  There is essentially no security to keep people from changing things.  If you want that, you will need to do more work to get things secure.

The first thing to do is install a minimal Raspberry Pi image.  I suggest Raspberry Pi OS Lite, using the Raspberry Pi Imager.  During the install, it will ask you if you would like to apply OS customization settings.  Click "Edit Settings", and I suggest setting a hostname.  I chose chime.local.  This is also where you can set your username, password, wifisettings, timezone, and keyboard.  Once you have created the boot media, boot it, and update it.  Once that is done, clone this repository to your user directory.

```bash
git clone *this repo*
```

Once that is done, you should create a virtual environment.

First install python and pip.

```bash
sudo apt install python3 python3-pip
```

Then, install virtualenv.

```bash
sudo pip3 install virtualenv
```

Then, install virtualenvwrapper.

```bash
sudo pip3 install virtualenvwrapper
```

Now, we need to edit the `.bashrc` file.

```bash
nano ~/.bashrc
```

At the end of `.bashrc`, add the following lines:

```bash
export WORKON_HOME=$HOME/.virtualenvs
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
```

To get virtualenvwrapper working, we need to either exit the shell and reopen it, or type:

```bash
source ~/.bashrc
```

Now, any time we want to create a virtual environment, we can use `mkvirtualenv`.  Let's make a virtualenv for this app and call it "chime".

```bash
mkvirtualenv chime
```

You will now notice that your prompt has (chime) at the front of it, signifying that you are in a virtual environment.  All python commands we type will now be with that virtual python environment.

Now, we need to install the requirements stored in requirements.txt.

```bash
cd ~/chime
pip install -r requirements.txt
```

Once this finishes, we need to create our database and structure.

```bash
./manage.py migrate
```

Now we need to collect static files, and create our media directory.

```bash
mkdir static
./manage.py collectstatic
mkdir media
```

Once that is done, we need to setup a web server to serve the app.

```bash
sudo apt install apache2 -y
```

Add your user to the www-data group.

```bash
sudo usermod -aG www-data $USER
```

Now, to serve django, we need to install and enable mod-wsgi.

```bash
sudo apt install libapache2-mod-wsgi-py3
sudo a2enmod wsgi
```

Let's edit the default page for apache.

```bash
sudo nano /etc/apache2/sites-enabled/000-default.conf
```

Above the line with `<Virtualhost *:80>`, add the following lines.  Replace any instance of `pi` with your username.

```apache
Alias /static /home/pi/chime/static
<Directory /home/pi/chime/static>
    Require all granted
</Directory>

<Directory /home/pi/chime/chime>
    <Files wsgi.py>
        Require all granted
    </Files>
</Directory>

WSGIDaemonProcess django python-path=/home/pi/chime python-home=/home/poduc>
WSGIProcessGroup django
WSGIScriptAlias / /home/pi/chime/chime/wsgi.py
```

Test the configuration.

```bash
sudo apache2ctl configtest
```

If you see `Syntax OK` at the end, you are good, even if it complains about a fully qualified domain name.  You can restart apache.

```bash
sudo systemctl restart apache2
```

We are almost done.  Apache and django are a bit finicky about file ownership and permissions, and the easiest way I've found to make this work is to just change ownership of the entire chime folder to www-data.

```bash
sudo chown www-data:www-data -R ~/chime
```

At this point, you should be done with the django part of things.  We just need to add the chime.py file to systemd.

## Setup Systemd Service

We need to create a file `/lib/systemd/system/chime.service`.  This will be to start our triggering script at startup.  Put the following text in that file and save it.  Again, replace `pi` with whatever username you chose.

```bash
[Unit]
Description=Chime Service
After=multi-user.target

[Service]
Type=idle
ExecStart=/home/pi/.virtualenvs/chime/bin/python /home/pi/chime/trigger/chime.py < /home/pi/chime.log 2>&1

[Install]
WantedBy=multi-user.target
```

Now set permissions on the file to 644.

```bash
sudo chmod 644 /lib/systemd/system/chime.service
```

Now we reload the daemon and enable the service.

```bash
sudo systemctl daemon-reload
sudo systemctl start chime.service
```

At this point, we should be completely done.  Once you upload clips, you should be able to trigger the chime by pulling pin 21 low.  If that doesn't work, reboot the pi and try again.
