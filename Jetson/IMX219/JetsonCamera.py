# MIT License
# Copyright (c) 2019 JetsonHacks
# See license
# Using a CSI camera (such as the Raspberry Pi Version 2) connected to a
# NVIDIA Jetson Nano Developer Kit using OpenCV
# Drivers for the camera and OpenCV are included in the base image

import cv2
import time
try:
    from  Queue import  Queue
except ModuleNotFoundError:
    from  queue import  Queue

import  threading
import signal
import sys

import numpy as np


# def signal_handler(sig, frame):
#     print('You pressed Ctrl+C!')
#     sys.exit(0)
# signal.signal(signal.SIGINT, signal_handler)


def gstreamer_pipeline(
    capture_width=1920,
    capture_height=1080,
    #display_width=640,
    #display_height=360,
    display_width=1920,
    display_height=1080,
    framerate=30,
    flip_method=2,
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

class FrameReader(threading.Thread):
    queues = []
    _running = True
    camera = None
    def __init__(self, camera, name):
        threading.Thread.__init__(self)
        self.name = name
        self.camera = camera
 
    def run(self):
        while self._running:
            _, frame = self.camera.read()
            while self.queues:
                queue = self.queues.pop()
                queue.put(frame)
    
    def addQueue(self, queue):
        self.queues.append(queue)

    def getFrame(self, timeout = None):
        queue = Queue(1)
        self.addQueue(queue)
        return queue.get(timeout = timeout)

    def stop(self):
        self._running = False

class Previewer(threading.Thread):
    window_name = "Arducam"
    _running = True
    camera = None
    frame_preview_func = None

    def __init__(
        self,
        camera,
        name,
        frame_preview_func = None
    ):
        threading.Thread.__init__(self)
        self.name = name
        self.camera = camera
        self.frame_preview_func = frame_preview_func
    
    def run(self):
        self._running = True
        while self._running:
            frame = self.camera.getFrame(2000)

            if self.frame_preview_func != None:
                frame, _ = self.frame_preview_func(frame)

            cv2.imshow(self.window_name, frame)
            keyCode = cv2.waitKey(16) & 0xFF
        cv2.destroyWindow(self.window_name)

    def start_preview(self):
        self.start()
    def stop_preview(self):
        self._running = False

class Camera(object):
    frame_reader = None
    cap = None
    previewer = None

    frame_preview_func = None

    def __init__(
        self,
        frame_preview_func = None,
    ):
        self.frame_preview_func = frame_preview_func
        self.open_camera()

    def open_camera(self):
        self.cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2), cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera!")
        if self.frame_reader == None:
            self.frame_reader = FrameReader(self.cap, "")
            self.frame_reader.daemon = True
            self.frame_reader.start()
        self.previewer = Previewer(
            self.frame_reader,
            "",
            frame_preview_func=self.frame_preview_func,
        )

    def getFrame(self):
        return self.frame_reader.getFrame()

    def start_preview(self):
        self.previewer.daemon = True
        self.previewer.start_preview()

    def stop_preview(self):
        self.previewer.stop_preview()
        self.previewer.join()
    
    def close(self):
        self.frame_reader.stop()
        self.cap.release()

if __name__ == "__main__":
    camera = Camera()
    camera.start_preview()
    time.sleep(10)
    camera.stop_preview()
    camera.close()
