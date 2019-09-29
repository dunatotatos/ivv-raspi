# Todo


 # reminder
Send HTML GET request from the py
```
 curl -X GET http://192.168.42.42:14999/okok
```

# temperature sensor
```
enable 1-wire in raspi-config
sudo pip3 install w1thermsensor
```
# Setup
add to /etc/wpa_supplicant/:

```
network={
 scan_ssid=1
 ssid="free wifi"
 psk="qwertzuiop"
}
```
in `/boot`
```
touch ssh in boot folder
```
open a terminal
```
sudo apt update && sudo apt upgrade -y
```

```
sudo apt install git
```
```
git clone https://github.com/Lu-ni/escape-room.git
```
```
sudo apt install python3-pip
```
```
sudo pip3 install w1thermsensor
```
```
sudo rasp-config
 ->inteface -> enable one-wire
```
```
sudo apt-get install rpi.gpio
```
in `/etc/dhcpcd.conf` add the following to the end of the file.
```
interface eth0

static ip_address=192.168.0.10/24
static routers=192.168.0.1
static domain_name_servers=192.168.0.1
```
```
sudo chmod 644 /lib/systemd/system/sample.service

Step 2 – Configure systemd

Now the unit file has been defined we can tell systemd to start it during the boot sequence :

sudo systemctl daemon-reload
sudo systemctl enable sample.service

Reboot the Pi and your custom service should run:
```