#!/bin/bash
#
# Only start up the driver cam if it is not already running.
#
# Check if there is a process called mjpg_streamer.  If there
# is, then we'll just print a helpful message for the user.
#
export PORTNUM=5809

if [[ $(pidof mjpg_streamer) ]];
then
    echo "mjpg_streamer is already streaming!";
    echo "View stream at: http://$HOSTNAME:$PORTNUM/?action=stream";
else
    echo "mjpg_streamer is *NOT YET* running, so we'll start it up!";
    cd /usr/src/mjpg-streamer/mjpg-streamer-experimental

    # Depending on how the camera gets mounted,
    # you might need to:
    #   flip image vertically    -vf
    #   flip image horizontally  -hf
    #   rotate the image 90 deg  -rot 90
    #
    #   Note that -p NNNN specifies the port number.
    #   It ought to be in the legal FIRST port range.
    #
    #   Note:  connect to    http://$HOSTNAME:NNNN/?action=stream
    #   to stream the video.    Should probably use python+openCV
    #   on the receiving end so the small image can easily be scaled
    #   up.
    #
    ./mjpg_streamer -o "output_http.so -p $PORTNUM -w ./www" -i "input_raspicam.so -x 160 -y 120 -cfx gray -rot 90 -fps 10 -ex sports"
fi
