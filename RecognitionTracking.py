

import cv2
import numpy as np
import xlsxwriter
import logging
import sys


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)


class Detector:

    def __init__(self, videopath, minSize, maxSize):
        self.videopath = videopath
        self.minSize = minSize
        self.maxSize = maxSize
        self.numberOfParticlesToShow = 200
        self.label = False

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        self.logger.info('Detector object created')

    def get_Frame(self, n=0):
        cap = cv2.VideoCapture(self.videopath)
        if n != 0:
            total_frames = cap.get(7)
            cap.set(1, n)
        success, self.frame = cap.read()
        cap.release()
        self.logger.debug('First frame extracted')

    def detect(self, frame=0):
        self.logger.info(f'Searching for circles from size {self.minSize} to {self.maxSize}')
        self.get_Frame(n=frame)
        img = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        img = cv2.medianBlur(img,5)
        edges = cv2.Canny(img,0,50)
        self.preview = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)

        circles = cv2.HoughCircles(img,cv2.HOUGH_GRADIENT,1,20,
                                    param1=50,param2=30,minRadius=self.minSize,maxRadius=self.maxSize)

        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            self.circles = circles[0][0:self.numberOfParticlesToShow]
            for i in range(0, len(self.circles)):
                c = self.circles[i]
                cv2.circle(self.preview,(c[0],c[1]),c[2],(0,255,0),2)# draw the outer circle
                cv2.circle(self.preview,(c[0],c[1]),2,(0,0,255),3)# draw the center of the circle
                if self.label == True:
                    cv2.putText(self.preview, f'{i + 1}', (c[0]+30,c[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)


            self.logger.info(f'{len(self.circles)} circles found')
        else:
            self.logger.info(f'0 circles found')
        return(self.circles)



class ExternalSelector:
    
    def __init__(self, videopath):
        self.videopath = videopath
        self.selections = []
        
    
    def get_Frame(self, n=0):

        cap = cv2.VideoCapture(self.videopath)
        if n != 0:
            total_frames = cap.get(7)
            cap.set(1, n)
        success, self.frame = cap.read()
        cap.release()
        self.height, self.width, self.channels = self.frame.shape
        # print('\n\n')
        # print('selector shape', self.frame.shape)
        # print('\n\n')

    def draw_Selection(self, l, frame=0):
        self.get_Frame(n=frame)
        img = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        img = cv2.medianBlur(img,5)
        self.preview = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
        self.selections = []
        for pos in l:
            a = (int(pos[0] * self.width), int(pos[1] * self.height))
            b = (int(pos[2] * self.width), int(pos[3] * self.height))
            self.selections.append(   (int(pos[0] * self.width), int(pos[1] * self.height), int(pos[2] * self.width), int(pos[3] * self.height)   ))
            self.preview = cv2.rectangle(self.preview, a, b, (0,255,0), 2)
            cv2.imwrite('preview.jpg', self.preview)

        



class Tracker():

    def __init__(self, videopath, firstFrame, lastFrame, boxes):
        self.videopath = videopath
        self.circle_color = (0, 255, 0)
        self.txt_color = (0, 255, 0)
        self.positions = {}
        self.bboxes = boxes

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        self.logger.debug('Tracker object created')
        self.logger.info(f'Video path provided : {self.videopath}')

        self.current_frame = None
        self.countimage = 0
        self.firstFrame = firstFrame
        self.lastFrame = lastFrame


    def track(self):
        
        self.countimage = 0

        cap = cv2.VideoCapture(self.videopath)
        cap.set(1, self.firstFrame)
        success, frame = cap.read()
        self.video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if not success:
            self.logger.error('Failed to read video')
            sys.exit(1)


        self.logger.debug(f'{len(self.bboxes)} tracking boxes have been created')
        trackerType = "CSRT"
        multiTracker = cv2.MultiTracker_create()                    # Create MultiTracker object

        for bbox in self.bboxes:                            # Initialize MultiTracker
            multiTracker.add(cv2.TrackerCSRT_create(), frame, bbox)
        self.logger.info(f'Starting the tracking of {len(self.bboxes)} particles')

        while cap.isOpened():

            success, frame = cap.read()
            if not success or self.countimage == self.lastFrame:
                cv2.imwrite('img_path{}_lastframe.jpg'.format(self.countimage), previous_frame)
                self.logger.info("\n Last Image save in your working directory !")
                break

            previous_frame = frame
            success, boxes = multiTracker.update(frame)             # get updated location of objects in subsequent frames

            if self.countimage < 1:                                 # initialize dataframes type
                for i, newbox in enumerate(boxes):
                    self.positions[i] = []

                                                                    # draw tracked objects
            for i, newbox in enumerate(boxes):
                                                                    # coordinates of the tracking box
                p1 = ((newbox[0]), (newbox[1]))
                p2 = ((newbox[0] + newbox[2]), (newbox[1] + newbox[3]))
                Pr1 = (int(newbox[0]), int(newbox[1]))
                Pr2 = (int(newbox[0] + newbox[2]), int(newbox[1] + newbox[3]))
                cv2.rectangle(frame, Pr1, Pr2, (255, 0, 0), 2, 1)
                                                                    # append the center of the box to dict "self.positions[index of box]" according to refresh rate
                if self.countimage:
                    xcenter = (p1[0] + p2[0]) / 2
                    ycenter = (p1[1] + p2[1]) / 2
                    self.positions[i].append((xcenter, ycenter))

                for pos in self.positions[i]:
                    xcenter = pos[0]
                    ycenter = pos[1]
                    cv2.circle(frame, (int(xcenter), int(ycenter)), 1, self.circle_color, -1)

            self.countimage += 1
            cv2.putText(frame, f"Frame no{self.countimage}", (10, 37), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)

            self.current_frame = frame

            yield frame

            # quit on ESC button and save last frame
            if cv2.waitKey(1) & 0xFF == 27:  # Esc pressed
                break
        # yield(None)



