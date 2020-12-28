"""Application configuration."""

IP_SRV = "192.168.42.13"
PORT_SRV = 14999
IP_DST = "192.168.42.42"
PORT_DST = 14999

ATELIER_GPIO = 11
SERRE_GPIO = 9
CAVEAU_GPIO = 5
BIRD_GPIO = 21
MOINE_GPIO = 20

# Do not modify below this line.
URL_DST = "http://{}:{}/".format(IP_SRV, PORT_DST)
