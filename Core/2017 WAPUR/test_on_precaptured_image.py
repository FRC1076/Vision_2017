import cv2
import numpy as np
# Kernal to use for removing noise
kernel = np.ones((3,3), np.uint8)
# Path of image
img = cv2.imread("/Users/cbmonk/Downloads/cube-green8.jpg", 1)

# Set values for thresholding
cube_color_lower = np.array([210, 180, 80])
cube_color_upper = np.array([255, 255, 160])

# Remove noise
mask = cv2.inRange(img, cube_color_lower, cube_color_upper)
close_gaps = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
no_noise = cv2.morphologyEx(close_gaps, cv2.MORPH_OPEN, kernel)
dilate = cv2.dilate(no_noise, kernel, iterations=1)

# Find boundary of object
_, contours, hierarchy = cv2.findContours(dilate, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cnt = contours[0]
# Extract boundary points of object
left = tuple(cnt[cnt[:,:,0].argmin()][0])
right = tuple(cnt[cnt[:,:,0].argmax()][0])
top = tuple(cnt[cnt[:,:,1].argmin()][0])
bottom = tuple(cnt[cnt[:,:,1].argmax()][0])

# Use boundary points to find the top left and bottom right corners
top_left = (left[0], top[1])
bottom_right = (right[0], bottom[1])

# Draw a rectangle bounding the object using top left and bottom right points
cv2.rectangle(img, top_left, bottom_right, (0,0,255), 3)

# Find the center point of the object
center = (int((top_left[0]+bottom_right[0])/2), int((top_left[1]+bottom_right[1])/2))

# Draw circle at the center point
cv2.circle(img, center, 5, (0,0,255), -1)

# Show the image
cv2.imshow("Scanned Image", img)
#cv2.imshow("Mask Image", dilate)   # This should be enabled for debugging purposes ONLY!

# Exit the program
cv2.waitKey(0)
cv2.destroyAllWindows()
