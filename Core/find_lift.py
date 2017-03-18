#
# Code to find the gear lift for the FRC 2017 Steamworks game.
# Sends range and heading information via UDP
# Type this to run interactively:
# python find_lift.py 127.0.0.1 interactive
#
from __future__ import division

import numpy as np
import cv2
import sys
import logging
import time
import json
import socket
import subprocess
from udp_channels import UDPChannel
from sensor_message import RobotMessage
from image_grabber import ImageGrabber

# set to true if you want images logged
grabbing = True

import psutil
import logging
import os
import time

fps_last_time = 0
fps = 0
fps_count = 0

print("Keys:\nEsc exit\np toggling print\ni toggle updating images\ns save filter values\n");

# log every grab_periodTH image
grab_period = 10

tx_udp = True
if "interactive" in sys.argv:
    im_show = True
    sliders = True
    printer = True
    wait = False
else:
    im_show = False
    sliders = False
    printer = False
    wait = False

if "log-images" in sys.argv:
    grabbing = True
else:
    grabbing = False

def restart_program(input1, input2):
    try:
        p = psutil.Process(os.getpid())
        for handler in p.get_open_files() + p.connections():
            os.close(handler.fd)
    except Exception, e:
        logging.error(e)

    python = sys.executable
    os.execl(os.path.realpath(__file__), input1, input2)


def receive_messages(im_show, sliders, printer, wait):
    data, address = sock.recvfrom(4096)
    if (data == "Toggle Interactive Mode") and imshow:
        restart_program("not_interactive")
    else:
        restart_program("127.0.0.1", "interactive")
    if data:
        sent = sock.sendto(data, address)


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', filename="/var/log/vision.log")
logger = logging.getLogger(__name__)

grabber = ImageGrabber(logger, grab_period=grab_period, grab_limit=4000)

# Make a UDP Socket
# try:
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     server_address = ('localhost', 10000)
#     sock.bind(server_address)
# except:
#     print("Crap")

# These are the hue saturation value
# This works for close-up
exposure = 30
lower_h = 75
lower_s = 100
lower_v = 100
upper_h = 105
upper_s = 255
upper_v = 255
FIELD_OF_VIEW = 65
camera = -1  # camera to open, -1 is default

#
# Configurations are on the /var volume where we write stuff
#
config_file_pathname = './find_lift.cfg'

#
# If there is a configuration file, import it, use existing values
# as default for anything missing.
# If there is not a configuration file, populate it with the application
# default values.
#
try:
    config_fp = open(config_file_pathname, 'r')
    config = json.load(config_fp)

    lower_h = config.get('lower_hue', lower_h)
    lower_s = config.get('lower_saturation', lower_s)
    lower_v = config.get('lower_value', lower_v)
    upper_h = config.get('upper_hue', upper_h)
    upper_s = config.get('upper_saturation', upper_s)
    upper_v = config.get('upper_value', upper_v)
    exposure = config.get('exposure', exposure)
    FIELD_OF_VIEW = config.get('field_of_view', FIELD_OF_VIEW)
    camera = config.get('camera', -1)

except:
    config = {
        'lower_hue': lower_h,
        'lower_saturation': lower_s,
        'lower_value': lower_v,
        'upper_hue': upper_h,
        'upper_saturation': upper_s,
        'upper_value': upper_v,
        'exposure': exposure,
        'field_of_view': FIELD_OF_VIEW,
        'camera': camera
    }
    config_fp = open(config_file_pathname, 'w')
    json.dump(config, config_fp)

config_fp.close()

# from function fitting
K_INCH_PIXELS = 1300
CM_PER_INCH = 2.54


def distance_in_cm_from_pixels(pixels):
    """
    We measured visible pixel width from experiments
    and fit that to the distances we measured.  We came
    up with a magic number and apply that here to get distance
    from the width of the 8 inch target.
    """
    return K_INCH_PIXELS / pixels * CM_PER_INCH


def distance_to_point(x0, y0):
    def distance(pt):
        x, y = pt[0]
        dx, dy = x - x0, y - y0
        return (dx * dx + dy * dy) ** 0.5;

    return distance


# finds the midpoint of 2 points
def midpoint(p1, p2):
    x1, y1 = p1[0]
    x2, y2 = p2[0]
    return (x1 + x2) / 2, (y1 + y2) / 2


# finds the area of a contour
def area(cnt):
    return cv2.contourArea(cnt)


# return width / height
def aspect_ratio(cnt):
    # finds the diagonal extreme of the contour
    upper_left = min(cnt, key=distance_to_point(0, 0))
    upper_right = min(cnt, key=distance_to_point(width, 0))
    bottom_left = min(cnt, key=distance_to_point(0, height))
    bottom_right = min(cnt, key=distance_to_point(width, height))
    avg_height = (bottom_left[0][1] - upper_left[0][1] + bottom_right[0][1] - upper_right[0][1]) / 2
    avg_width = (upper_right[0][0] - upper_left[0][0] + bottom_right[0][0] - bottom_left[0][0]) / 2
    # print("aspect_ratio:", avg_height, avg_width, avg_height / avg_width;)
    # print(cnt)
    if avg_width != 0:
        return abs(avg_width / avg_height)
    else:
        return 0


# determines the degrees of the cube off from the middle
def find_heading(cnt, width, height):
    # finds the diagonal extremes of the contour
    upper_left = min(cnt, key=distance_to_point(0, 0))
    upper_right = min(cnt, key=distance_to_point(width, 0))
    bottom_left = min(cnt, key=distance_to_point(0, width))
    bottom_right = min(cnt, key=distance_to_point(width, height))

    # finds the midpoint
    midpoint_upper = midpoint(upper_left, upper_right)
    midpoint_bottom = midpoint(bottom_left, bottom_right)
    up_x, up_y = midpoint_upper
    bot_x, bot_y = midpoint_bottom
    mid = (up_x + bot_x) / 2, (up_y + bot_y) / 2
    mid_x, mid_y = mid
    pixel_distance = mid_x - width / 2
    heading = ((FIELD_OF_VIEW / 2.0) * pixel_distance) / (width / 2)
    return int(heading)


# determines the distance of the tape from the robot in inches
# width is the number of pixels our image is wide
# height is the number of pixels our image is tall
# note the tape is 5 inches tall

def find_distance(contour, width, height):
    # print(contour)
    # find the diagonal extremes of the contour
    upper_left = min(contour, key=distance_to_point(0, 0))
    upper_right = min(contour, key=distance_to_point(width, 0))
    bottom_left = min(contour, key=distance_to_point(0, height))
    bottom_right = min(contour, key=distance_to_point(width, height))

    # finds the left and right X values
    bottom_left_x, bottom_left_y = bottom_left[0]
    bottom_right_x, bottom_right_y = bottom_right[0]
    if bottom_left_y > bottom_right_y:
        pixel_height = bottom_left_y - upper_left[0][1]
    else:
        pixel_height = bottom_right_y - upper_left[0][1]
    # print("The pixel height is: " + str(pixel_height))
    pixel_width = abs(bottom_right_x - bottom_left_x)
    # print("The pixel width is:", pixel_width)
    distance = distance_in_cm_from_pixels(pixel_height)
    # FIELD_OF_VIEW = 65
    if distance >= 0 and distance < 9999:
        return round(distance)
    else:
        return 9999

def nothing(x):
    pass


# sets the video capture
cap = cv2.VideoCapture(camera)
if cv2.__version__ == '3.1.0':
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 60)
else:
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.cv.CV_CAP_PROP_FPS, 30)

#
# This doesn't run on systems that don't have this
#
try:
    x = 1
    subprocess.Popen('v4l2-ctl --device=/dev/video0 -c gain_automatic=0 -c white_balance_automatic=0 -c exposure=35 -c gain=0 -c auto_exposure=1 -c brightness=0 -c hue=-32 -c saturation=96'.split())
    time.sleep(1)
except:
    print('Unable to set exposure using v4l2-ctl tool!')

if sliders:
    # creates slider windows1
    
    cv2.namedWindow('HSV Filter', cv2.WINDOW_NORMAL)

    # creates the rgb trackbars
    cv2.createTrackbar('Hue upper', 'HSV Filter', 0, 255, nothing)
    cv2.createTrackbar('Hue lower', 'HSV Filter', 0, 255, nothing)
    cv2.createTrackbar('Val upper', 'HSV Filter', 0, 255, nothing)
    cv2.createTrackbar('Val lower', 'HSV Filter', 0, 255, nothing)
    cv2.createTrackbar('Sat upper', 'HSV Filter', 0, 255, nothing)
    cv2.createTrackbar('Sat lower', 'HSV Filter', 0, 255, nothing)

    cv2.setTrackbarPos('Hue lower', 'HSV Filter', lower_h)
    cv2.setTrackbarPos('Sat lower', 'HSV Filter', lower_s)
    cv2.setTrackbarPos('Val lower', 'HSV Filter', lower_v)
    cv2.setTrackbarPos('Hue upper', 'HSV Filter', upper_h)
    cv2.setTrackbarPos('Sat upper', 'HSV Filter', upper_s)
    cv2.setTrackbarPos('Val upper', 'HSV Filter', upper_v)
    
    cv2.resizeWindow('HSV Filter', 500, 100)

#
# Sets up UDP sender
# Default is the typical robot ip address
#
if len(sys.argv) > 1:
    ip = sys.argv[1]
else:
    ip = '10.10.76.2'


channel = None
while channel is None:
    try:
        channel = UDPChannel(remote_ip=ip, remote_port=5880,
                             local_ip='0.0.0.0', local_port=5888, timeout_in_seconds=0.001)
    except:
        print("Unable to create UDP channel, sleeping 1 sec and retry.")
        time.sleep(1)

#
# Just keep swimming
while 1:
    if fps_last_time != int(time.time()):
        fps_last_time = int(time.time())
        fps = fps_count
        fps_count = 0
    else:
        fps_count = fps_count + 1
    try:
        #
        # Try to receive a control packet from the robot and process it.
        #
#        try:
#            robot_data, robot_address = channel.receive_from()
#            print("YIKES!", robot_data)
#            message_from_robot = RobotMessage(robot_data)
#            if ((message_from_robot.sender == 'robot') and
#                (message_from_robot.message == 'target')):
#                set_thresholds(message_from_robot.color)
#                logger.info("Robot changed target color to %s", message_from_robot.color)
#                logger.info("Start grabbing images NOW!")
#                grabbing = True
#        except socket.timeout as e:
#            logger.info("Timed out waiting for message from robot : %s", e)


        #
        # In interactive mode (should we condition on this one?)
        # respond to some single key commands
        #
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # Exit when the escape key is hit
            break
        if k == ord('i'):
            im_show = not im_show
        if k == ord('p'):
            printer = not printer
        if k == ord('s'):
            config = {
                'lower_hue': lower_h,
                'lower_saturation': lower_s,
                'lower_value': lower_v,
                'upper_hue': upper_h,
                'upper_saturation': upper_s,
                'upper_value': upper_v,
                'exposure': exposure,
                'field_of_view': FIELD_OF_VIEW,
                'camera': camera
            }
            config_fp = open(config_file_pathname, 'w')
            json.dump(config, config_fp)
            config_fp.close()

        start_time = time.time()
        # captures each frame individually
        ret, frame = cap.read()
        #frame = cv2.imread('TestImages/gearlift_2ft.jpeg')
        height, width, channels = frame.shape

        if im_show:
            cv2.imshow('source', frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # converts frame from BGR to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        if sliders:
            # lower hsv values
            lower_h = cv2.getTrackbarPos('Hue lower', 'HSV Filter')
            lower_s = cv2.getTrackbarPos('Sat lower', 'HSV Filter')
            lower_v = cv2.getTrackbarPos('Val lower', 'HSV Filter')

            # upper rgb values
            upper_h = cv2.getTrackbarPos('Hue upper', 'HSV Filter')
            upper_s = cv2.getTrackbarPos('Sat upper', 'HSV Filter')
            upper_v = cv2.getTrackbarPos('Val upper', 'HSV Filter')

        # range of HSV color values
        lower_green = np.array([lower_h, lower_s, lower_v])
        upper_green = np.array([upper_h, upper_s, upper_v])

        # creates a bw image using the above range of values
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # sets the dilation and erosion factor
        kernel = np.ones((2, 2), np.uint8)
        dots = np.ones((3, 3), np.uint8)
        # erodes and dilates the image
        if im_show:
            cv2.imshow('After cv2.inRange', mask)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, dots)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, dots)
        # dilates and erodes the image
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        if im_show:
            cv2.imshow('After cv2.morphologyEx', mask)

        if cv2.__version__ == '3.1.0':
            dontcare, contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        else:
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        cube_found = False  # count number of contours that match our tests for cubes
        count = 0  # count times through the loop below
        tape_heading = []
        tape_distance = []
        for contour in contours:
            count += 1
            is_aspect_ok = (0.28 < aspect_ratio(contour) < 1.5)
            is_area_ok = (25 < cv2.contourArea(contour) < 20000)
            if not is_area_ok:
                # print("Contour fails area test:", cv2.contourArea(contour), "Contour:", count, " of ", len(contours))
                continue  # jump to bottom of for loop
            if not is_aspect_ok:

                # sprint("Contour fails aspect test:", aspect_ratio(contour), "Contour:", count, " of ", len(contours))
                print("Contour fails aspect test:", aspect_ratio(contour), "Contour:", count, " of ", len(contours))
                continue  # jump to bottom of for loop
            # Find the heading of this tape
            heading = find_heading(contour, width, height)
            tape_heading.append(heading)
            # determines the distance of this tape
            distance = find_distance(contour, width, height)
            tape_distance.append(distance)
        if len(tape_heading) == 2:
            #
            # Note, we negate the heading that we send to the rio so it looks
            # more like it is a gyro and the robot is trying to drive straight.
            #
            data = {
                "heading": (tape_heading[0] + tape_heading[1]) / -2,
                "range": distance,
                "status": "ok",
                "sender": "vision",
                "average range": (tape_distance[0] + tape_distance[1]) / 2,
                "message": "range and heading",
                "fps": fps
            }
            message = json.dumps(data)
            # Transmit the message
            if tx_udp:
                channel.send_to(message)
            if printer:
                print("Tx:" + message)
            logger.info(message)
        else:
            data = {
                "sender": "vision",
                "message": "range and heading",
                "status": "no target",
                "fps": fps
            }
            message = json.dumps(data)

            if tx_udp:
                channel.send_to(message)
                if printer:
                    print("Tx:" + message)
                logging.info(message)
        if grabbing:
            grabber.grab(frame, message)
            #
            # I do not think we really want to sleep here...
            # MMMMUUUSSSSSTTT KKKKEEEEEPPPPPP  RRRRRUUNNNIIINNNGGGG
            # time.sleep(.1)
            # Is not this code totally redundant because it occurs earlier?
        if wait:
            if not im_show:
                cv2.namedWindow('waitkey placeholder')
            k = cv2.waitKey(0)
            if k == 27:  # wait for ESC key to exit
                cv2.destroyAllWindows()
                print(tape_heading)
                break
    except:
        print("Exception Caught")
