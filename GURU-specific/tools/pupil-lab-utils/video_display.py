import cv2
import numpy as np
import time


if __name__ == '__main__':
    cap = cv2.VideoCapture("./world.mp4")
    gaze_pos = np.load('./world_pupil_data.npy')
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(length)

    # Check if camera opened successfully
    if (cap.isOpened()== False): 
        print("Error opening video stream or file")
     
    # Read until video is completed
    f_index = 0
    while(cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == True:
            height, width, _ = frame.shape
            norm_x, norm_y = gaze_pos[f_index]['norm_pos']
            conf = gaze_pos[f_index]['confidence']
            f_index += 1
            gaze_x, gaze_y = norm_x * width, norm_y * height
            # Display the resulting frame
            if conf < 0.5:
                continue

            cv2.putText(frame, "Conf: {}".format(np.round(conf * 100, decimals=2)), (10,height-20), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
            cv2.circle(frame, (int(gaze_x), int(gaze_y)), 12, (255,165,0), -1)
            cv2.imshow('Frame',frame)
            time.sleep(0.2)
            # Press Q on keyboard to  exit
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
            # Break the loop
        else:
            break
    # When everything done, release the video capture object
    cap.release()
    # Closes all the frames
    cv2.destroyAllWindows()
