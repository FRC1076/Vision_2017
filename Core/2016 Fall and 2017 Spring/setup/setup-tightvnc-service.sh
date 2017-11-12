#!/bin/bash

# copy the revision controlled service definition file to install location
cp tightvncserver.service /etc/systemd/system

# make sure it is owned by root and it is executable
chown root:root /etc/systemd/system/tightvncserver.service
chmod 755 /etc/systemd/system/tightvncserver.service

# start up the service
systemctl start tightvncserver.service 

# enable the service
systemctl enable tightvncserver.service

echo 'You should probably reboot to ensure that the vnc server starts up on boot'
