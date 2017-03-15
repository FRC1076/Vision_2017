#!/bin/bash

# create the vision log and make it writeable 
touch /var/log/vision.log
chmod 666 /var/log/vision.log

# set static address on eth0 (.13 for vision)
# customize dhcpcd-changes before you run this, I guess.
sudo cat dhcpcd-changes >> /etc/dhcpcd.conf

# add command to LXDE-pi/autostart to fire up the vision system
cp find-lift.sh /home/pi/.config/lxsession/LXDE-pi
chmod 755 /home/pi/.config/lxsession/LXDE-pi/find-lift.sh
echo "@/home/pi/.config/lxsession/LXDE-pi/find-lift.sh" >> /home/pi/.config/lxsession/LXDE-pi/autostart
