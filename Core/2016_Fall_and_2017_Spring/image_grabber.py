from __future__ import print_function

import cv2
import glob
import os


class ImageGrabber:
    def __init__(self, logger, grab_period=5, grab_limit=100):
        """
        Create a image grabber that grabs an image every
        grab_period calls.   Default is every 5th call.

        Usage:

        ig = ImageGrabber(logger, grab_period=5, grab_limit=50)

        while 1:
            ret, frame = cap.read()    # get image, for example

            process_image_to_extract_info(frame)

            if appropriate_to_grab:
                ig.grab(frame,log_message)

        Note that all of the images are stored in a new directory with the name Imagesnnnn.  e.g. Images0001, Images0002.
        """
        self.logger = logger
        self.grab_period = grab_period
        self.grab_limit = grab_limit
        self.file_index = 1
        self.call_index = 0

        image_dirs = sorted(glob.glob("Images[0-9][0-9][0-9][0-9]"))
        if len(image_dirs) != 0:
            last_dir = image_dirs[-1]
            dir_index = int(last_dir[-4:]) + 1
        else:
            dir_index = 1

        self.dir_name = "Images{:04d}".format(dir_index)
        os.mkdir(self.dir_name)

    def grab(self, image, log_result=None):
        """
        Export an image to a file every "period" calls.
        Log the filename and a message.  (with some result?)
        """
        self.call_index += 1
        if ((self.file_index < self.grab_limit) and
                    (self.call_index % self.grab_period) == 0):
            filename = os.path.join(self.dir_name, "camera_capture_{:04d}.jpg".format(self.file_index))
            cv2.imwrite(filename, image)
            if self.logger is not None:
                self.logger.info("Call %d: captured image to %s, result was [%s]", self.call_index, filename,
                                 log_result)
            self.file_index += 1



