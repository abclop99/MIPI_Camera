# encoding: UTF-8
'''
    Arducam programable zoom-lens controller.

    Copyright (c) 2019-4 Arducam <http://www.arducam.com>.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
    OR OTHER DEALINGS IN THE SOFTWARE.
'''

import cv2 #sudo apt-get install python-opencv
import numpy as py
import os
import sys
import time
import argparse
from JetsonCamera import Camera

from Focuser import Focuser
from mp_FaceDetection import FaceDetector

import threading

import curses

global image_count
image_count = 0

# Rendering status bar
def RenderStatusBar(stdscr):
    height, width = stdscr.getmaxyx()
    statusbarstr = "Press 'q' to exit"
    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(height-1, 0, statusbarstr)
    stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
    stdscr.attroff(curses.color_pair(3))
# Rendering description
def RenderDescription(stdscr):
    quit_desc        = "Quit \t\t: 'q' Key"
    focus_desc       = "Focus \t\t: Up-Down Arrow"
    snapshot_desc    = "Snapshot \t: 'c' Key"
    autofocus_desc   = "Autofocus \t: 'f' Key"

    desc_y = 1
    
    stdscr.addstr(desc_y + 1, 0, quit_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 2, 0, focus_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 3, 0, snapshot_desc, curses.color_pair(1))
    stdscr.addstr(desc_y + 4, 0, autofocus_desc, curses.color_pair(1))
# Rendering  middle text
def RenderMiddleText(stdscr,k,focuser):
    # get height and width of the window.
    height, width = stdscr.getmaxyx()
    # Declaration of strings
    title = "Arducam Controller"[:width-1]
    subtitle = ""[:width-1]
    keystr = "Last key pressed: {}".format(k)[:width-1]
    
    
    # Obtain device infomation
    focus_value = "Focus    : {}".format(focuser.get(Focuser.OPT_FOCUS))[:width-1]
    
    if k == 0:
        keystr = "No key press detected..."[:width-1]

    # Centering calculations
    start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
    start_x_subtitle = int((width // 2) - (len(subtitle) // 2) - len(subtitle) % 2)
    start_x_keystr = int((width // 2) - (len(keystr) // 2) - len(keystr) % 2)
    start_x_device_info = int((width // 2) - (len("Focus    : 00000") // 2) - len("Focus    : 00000") % 2)
    start_y = int((height // 2) - 6)
    
    # Turning on attributes for title
    stdscr.attron(curses.color_pair(2))
    stdscr.attron(curses.A_BOLD)

    # Rendering title
    stdscr.addstr(start_y, start_x_title, title)

    # Turning off attributes for title
    stdscr.attroff(curses.color_pair(2))
    stdscr.attroff(curses.A_BOLD)

    # Print rest of text
    stdscr.addstr(start_y + 1, start_x_subtitle, subtitle)
    stdscr.addstr(start_y + 3, (width // 2) - 2, '-' * 4)
    stdscr.addstr(start_y + 5, start_x_keystr, keystr)
    # Print device info
    stdscr.addstr(start_y + 6, start_x_device_info, focus_value)

def parse_cmdline():
    parser = argparse.ArgumentParser(description='Arducam Controller.')

    parser.add_argument('-i', '--i2c-bus', type=int, nargs=None, required=True,
                        help='Set i2c bus, for A02 is 6, for B01 is 7 or 8, for Jetson Xavier NX it is 9 and 10.')

    return parser.parse_args()

# parse input key
def parseKey(k,focuser,autofocuser, face_detector,camera):
    global image_count
    focus_step  = 10
    if k == ord('r'):
        autofocuser.stop_autofocus(set_focus=False)
        focuser.reset(Focuser.OPT_FOCUS)
    elif k == ord('f'):
        # Autofocus
        autofocuser.start_autofocus()
    elif k == curses.KEY_UP:
        autofocuser.stop_autofocus(set_focus=False)
        focuser.set(Focuser.OPT_FOCUS,focuser.get(Focuser.OPT_FOCUS) + focus_step)
    elif k == curses.KEY_DOWN:
        autofocuser.stop_autofocus(set_focus=False)
        focuser.set(Focuser.OPT_FOCUS,focuser.get(Focuser.OPT_FOCUS) - focus_step)
    # elif k == 10:
    #     auto_focus.startFocus()
    #     # auto_focus.startFocus2()
    #     # auto_focus.auxiliaryFocusing()
    #     pass
    elif k == ord('c'):
        #save image to file.
        cv2.imwrite("image{}.jpg".format(image_count), camera.getFrame())
        image_count += 1


# Python curses example Written by Clay McLeod
# https://gist.github.com/claymcleod/b670285f334acd56ad1c
def draw_menu(stdscr, camera, face_detector, i2c_bus):
    focuser = Focuser(i2c_bus)
    autofocuser = Autofocuser(focuser, face_detector)
    autofocuser.start()

    k = 0
    cursor_x = 0
    cursor_y = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    # Loop where k is the last character pressed
    while (k != ord('q')):
        # Initialization
        stdscr.clear()
        # Flush all input buffers. 
        curses.flushinp()
        # get height and width of the window.
        height, width = stdscr.getmaxyx()

        # parser input key
        parseKey(k,focuser,autofocuser,face_detector,camera)

        # Rendering some text
        whstr = "Width: {}, Height: {}".format(width, height)
        stdscr.addstr(0, 0, whstr, curses.color_pair(1))
        
        stdscr.addstr(10, 0, f"Bboxes: {face_detector.bboxs}", curses.color_pair(1))

        # render key description
        RenderDescription(stdscr)
        # render status bar
        RenderStatusBar(stdscr)
        # render middle text
        RenderMiddleText(stdscr,k,focuser)
        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        k = stdscr.getch()

def laplacian(img, mask=None):
	img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
	img_sobel = cv2.Laplacian(img_gray,cv2.CV_16U)
	# return cv2.mean(img_sobel, mask)[0]
	return py.average(img_sobel, weights=mask)

class Autofocuser(threading.Thread):
    focuser = None
    face_detector = None
    _running = False

    event = threading.Event()

    focus_step = 10
    
    best_focus = None
    best_metric = None
    frames_since_improvement = 0

    def __init__(
        self,
        focuser: Focuser,
        face_detector: FaceDetector,
        focus_step = 10,
        starting_focus = 100, # Skip useless range
        name="Autofocuser",
        daemon=True,
    ):
        threading.Thread.__init__(
            self,
            name=name,
            daemon=daemon,
        )
        self.focuser = focuser
        self.face_detector = face_detector
        self.focus_step = focus_step
        self.starting_focus = starting_focus

    def run(self):
        while True:
            if self._running:
                # Set initial focus value
                self.focuser.set(Focuser.OPT_FOCUS, self.starting_focus)

                bboxs = []

                # Wait some extra cycles for the focus to
                # change completely
                # And a chance to capture some bboxs
                for _ in range(5):
                    self.face_detector.event.clear()
                    self.face_detector.event.wait()

                    bboxs.extend(self.face_detector.bboxs)

                # Create a weight mask from the bboxs
                mask = py.ones_like(self.face_detector.frame[:,:,0]) * 0.0001
                # Add bounding boxes
                for _, bbox, confidence in bboxs:
                    mask[bbox[0]:bbox[0]+bbox[2], bbox[1]+bbox[2]] = 1#confidence[0]

                while self._running:

                    # Wait for next frame to be processed
                    self.face_detector.event.clear()
                    self.face_detector.event.wait()
                
                    # Get frame and bounding boxes
                    frame = self.face_detector.frame
                    bboxs = self.face_detector.bboxs

                    #
                    if frame is not None:

                        # Evaluate focus
                        metric = laplacian(frame, mask)

                        # Set best focus and metric if better
                        if self.best_focus is None:
                            self.best_focus = self.focuser.get(Focuser.OPT_FOCUS)
                            self.best_metric = metric
                            self.frames_since_improvement = 0
                        elif metric > self.best_metric:
                            self.best_focus = self.focuser.get(Focuser.OPT_FOCUS)
                            self.best_metric = metric
                            self.frames_since_improvement = 0
                        elif metric < self.best_focus * 0.6 and self.focuser.get(Focuser.OPT_FOCUS) > 200:
                            self.frames_since_improvement += 1

                        # print(f"Best focus: {self.best_focus}\tBest metric: {self.best_metric}\tCurrent metric: {metric} frames_since_blah: {self.frames_since_improvement}")

                    # Stop if focus value reaches max
                    if self.focuser.get(Focuser.OPT_FOCUS) >= 1000:
                        self.stop_autofocus()
                    # Stop if metric keeps getting worse for long enough
                    elif self.frames_since_improvement > 6:
                        self.stop_autofocus()
                    # Set next focus and
                    # Wait for next frame to be detected
                    else:
                        # Set next focus value
                        self.focuser.set(
                            Focuser.OPT_FOCUS,
                            self.focuser.get(Focuser.OPT_FOCUS) + self.focus_step
                        )

            # Sleep until awaken to start again
            # Event is cleared in self.stop_autofocus()
            self.event.wait()
            self.event.clear()

    def start_autofocus(self,):
        """
        Start/restart autofocus search
        - Sets/resets search variables
        """
        # Set running and wake up thread
        self._running = True
        self.event.set()

        self.best_focus = None
        self.best_metric = None

    def stop_autofocus(self,set_focus=True):
        """
        Ends autofocus search and sets focus to best found
        unless False
        """
        self._running = False
        self.event.clear()

        if set_focus:
            if self.best_focus is not None:
                self.focuser.set(
                    Focuser.OPT_FOCUS,
                    self.best_focus,
                )

def main():
    args = parse_cmdline()
    
    #open camera and face detector
    face_detector = FaceDetector(0.4)
    camera = Camera(
        frame_preview_func=lambda f : face_detector.findFaces(f)[0]
    )
    
    #open camera preview
    camera.start_preview()
    print(args.i2c_bus)
    curses.wrapper(draw_menu, camera, face_detector, args.i2c_bus)

    camera.stop_preview()
    camera.close()

    

if __name__ == "__main__":
    main()