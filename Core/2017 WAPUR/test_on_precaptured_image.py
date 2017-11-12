import cv2
import numpy as np
kernel = np.ones((3,3), np.uint8)
img = cv2.imread("/Users/cbmonk/Downloads/cube-green8.jpg", 1)

cube_color_lower = np.array([210, 180, 80])
cube_color_upper = np.array([255, 255, 160])

mask = cv2.inRange(img, cube_color_lower, cube_color_upper)
close_gaps = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
no_noise = cv2.morphologyEx(close_gaps, cv2.MORPH_OPEN, kernel)
dilate = cv2.dilate(no_noise, kernel, iterations=1)

cv2.imshow("Modified Image", dilate)
cv2.imshow("Original Image", img)

cv2.waitKey(0)
cv2.destroyAllWindows()
