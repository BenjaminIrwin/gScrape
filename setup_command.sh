#!/bin/bash

# Update and Upgrade Ubuntu
sudo apt-get update
sudo apt-get -y upgrade

# Install XFCE Desktop, VNC Server, and Google Chrome
sudo apt-get install -y xfce4 xfce4-goodies tightvncserver
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

# Clone the gScrape repository
git clone https://github.com/BenjaminIrwin/gScrape.git
# Navigate into the gScrape directory
cd gScrape

# Install Python3-venv if not installed
sudo apt-get install -y python3-venv
# Create a virtual environment in the gScrape directory
python3 -m venv venv
# Activate the virtual environment
source venv/bin/activate
# Print that we are installing libraries
echo "Installing libraries........"
# Install the required libraries
pip install -r requirements.txt
# Navigate back to the home directory
cd ~

# Initial VNC server start to configure it, then kill it to configure xstartup
vncserver :1
vncserver -kill :1

# Configure VNC Server to start XFCE. Google Chrome launch line removed.
mkdir -p ~/.vnc
echo '#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &

# Wait for the desktop to load, then run a specific script from gScrape
(sleep 60; cd ~/gScrape && source venv/bin/activate && python3 scraper.py &)' > ~/.vnc/xstartup
chmod +x ~/.vnc/xstartup

# Install noVNC
cd ~
git clone https://github.com/novnc/noVNC.git

# Generate a self-signed SSL certificate for noVNC
cd noVNC
openssl req -new -x509 -days 365 -nodes -out self.pem -keyout self.pem -batch

# Adjust the VNC and noVNC startup part, omitting the noVNC specific startup
# and instead just starting the VNC server. The script from gScrape will be
# run as part of the xstartup script we configured above.
IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "VNC server is running. Connect with a VNC client at $IP:5901"
vncserver :1
