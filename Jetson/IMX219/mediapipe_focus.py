import cv2

from mp_FaceDetection import FaceDetector
from Focuser import Focuser

def gstreamer_pipeline (
        capture_width=1920, capture_height=1080,
        display_width=1920, display_height=1080,
        framerate=30, flip_method=2) : 
    """
        The pipeline for gstreamer
    """
    return ('nvarguscamerasrc ! ' 
    'video/x-raw(memory:NVMM), '
    'width=(int)%d, height=(int)%d, '
    'format=(string)NV12, framerate=(fraction)%d/1 ! '
    'nvvidconv flip-method=%d ! '
    'video/x-raw, format=(string)BGRx ! '
    'videoconvert ! '
    'video/x-raw, format=(string)BGR ! appsink'  % (capture_width,capture_height,framerate,flip_method))

def show_camera(
        args,
        window_name="CSI Camera",
    ):
    #print("pipeline", gstreamer_pipeline())

    # Capture
    cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    cap.set(6, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Make sure camera is opened
    assert cap.isOpened(), "Cannot open camera"

    window_handle = cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    face_detector = FaceDetector(0.75)
    focuser = Focuser(args.i2c_bus)

    while cv2.getWindowProperty(window_name, 0) >= 0 and cap.isOpened():
        ret_val, img = cap.read()

        # print(ret_val, img)

        marked_img, _ = face_detector.findFaces(img)
        cv2.imshow(window_name, marked_img)

        keycode = cv2.waitKey(16) & 0xff
        # Quit if esc or q pressed
        if keycode == 27:
            break
        elif keycode == ord('q'):
            break
        elif keycode == 81:
            # Left
            pass
        elif keycode == 82:
            # Up
            print("Up")
        elif keycode == 83:
            # Right
            pass
        elif keycode == 84:
            # Down
            print("Down")

    # Close/clean up camera and window
    cap.release()
    cv2.destroyAllWindows()

def parse_cmdline():
    """
        Parses command line arguments
    """
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--i2c-bus', type=int, nargs=None, required=True,
                        help='Set i2c bus, for A02 is 6, for B01 is 7 or 8, for Jetson Xavier NX it is 9 and 10.')

    return parser.parse_args()

def main():
    args = parse_cmdline()
    show_camera(args)

if __name__ == "__main__":
    main()
