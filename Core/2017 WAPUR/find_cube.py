import cv2
import numpy as np
kernel = np.ones((3,3), np.uint8)

cube_color_lower = np.array([210, 180, 80])
cube_color_upper = np.array([255, 255, 160])

video_capture = cv2.VideoCapture(0)

while(True):
    # Get the frame
    _, frame = video_capture.read()

    mask = cv2.inRange(frame, cube_color_lower, cube_color_upper)
    close_gaps = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    no_noise = cv2.morphologyEx(close_gaps, cv2.MORPH_OPEN, kernel)
    dilate = cv2.dilate(no_noise, kernel, iterations=1)

    im2, contours, hierarchy = cv2.findContours(dilate, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(dilate, contours, -1, (0,255,0), 3)

    cv2.imshow("Modified Video", dilate)
    cv2.imshow("Original Video", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.waitKey(0)
cv2.destroyAllWindows()
