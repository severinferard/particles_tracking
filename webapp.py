from flask import Flask
from RecognitionTracking import Detector, Tracker, ExternalSelector
from flask import Flask, render_template, Response, request, redirect, url_for
from Utils import createCSVFile, createExcelFile
from flask_caching import Cache
import webbrowser
import threading
import logging
import numpy as np
import json
import requests
import pandas as pd
import os
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
import webbrowser

import cv2

class VideoFeed(object):
    def __init__(self):
        self.videopath = None
        self.state = 0
        self.minParticlesSize = 0
        self.maxParticlesSize = 0
        self.numberOfParticlesToShowSize = 0
        self.firstFrame = 0
        self.lastFrame = None
        self.videolength = None
        self.countimage = 0
        self.numberOfParticlesToShow = 10
        self.numParticles = 0
        self.label = False
        self.selectionType = "auto"
        self.selections = []
        self.video = cv2.VideoCapture(self.videopath)
        self.settingChanged =  False
        self.fileToOpen = None

    def __setitem__(self, key, value):
        setattr(self, key, value)
        
    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()


    def preview(self):
        print(self.videopath, self.minParticlesSize, self.maxParticlesSize)
        detector = Detector(self.videopath, int(self.minParticlesSize), int(self.maxParticlesSize))
        self.selector = ExternalSelector(self.videopath)
        a = 2

        while not self.state:
            if self.selectionType == 'auto':
                self.settingChanged = False
                detector.minSize = int(self.minParticlesSize)
                detector.maxSize = int(self.maxParticlesSize)
                detector.numberOfParticlesToShow = int(self.numberOfParticlesToShow)
                detector.label = self.label

                detector.detect(frame=int(self.firstFrame))
                ret, jpeg = cv2.imencode('.jpg', detector.preview)
                frame = jpeg.tobytes()
                self.numParticles = len(detector.circles)
                
                self.bboxes = []
                for circle in detector.circles:
                    x = circle[0] - 5
                    y = circle[1] - 5
                    radius = circle[2]
                    width = (radius * 2) + 10
                    height = width
                    self.bboxes.append( (x-(radius+a),y-(radius+a), width, height))

                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            else:
                indexedSelections = [[selec["x1"], selec["y1"], selec["x2"], selec["y2"]] for selec in self.selections]
                self.selector.draw_Selection(indexedSelections)
                ret, jpeg = cv2.imencode('.jpg', self.selector.preview)
                frame = jpeg.tobytes()
                self.numParticles = len(self.selector.selections)
                self.bboxes = []
                for box in self.selector.selections:
                    self.bboxes.append((box[0], box[1], box[2]-box[0], box[3]-box[1]))

                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                    
        

    
    


    def runAnalysis(self):
        self.tracker = Tracker(self.videopath, self.firstFrame, self.lastFrame, self.bboxes)
        for frame in self.tracker.track():
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame = jpeg.tobytes()
            self.countimage = self.tracker.countimage
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        print('BREAKED')
        self.state = 2




videofeed = VideoFeed()

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "null", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}
app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)


@app.route('/', methods=['POST', 'GET'])
def index():
    cache.clear()
    global videofeed
    # return render_template('index.html', videop=videofeed.videopath, state=videofeed.state)
    return render_template('homepage.html')

@app.route('/preview', methods=['POST', 'GET'])
def preview():
    global videofeed
    videofeed.state = 0

    if request.method == 'POST':
        for key, value in request.form.items():
            print(key, value)
            videofeed[key] = value
    elif request.method == 'GET':
        videofeed.selections = [] 

    return render_template('preview2.html', videopath=videofeed.videopath, videolength=videofeed.videolength, numParticles=videofeed.numParticles, maxparticle=videofeed.numberOfParticlesToShow)


@app.route('/video_feed_preview')
def video_feed_preview():
        return Response(videofeed.preview(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_tracking')
def video_feed_tracking():
    return Response(videofeed.runAnalysis(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/tracking-state')
def trackingstate():
    print(videofeed.state)
    return json.dumps({"trackingState" : videofeed.state})


@app.route('/data')
def data():
    try:
        ci = videofeed.tracker.countimage
    except:
        ci = 0
    print('ci',ci)
    s = f'''"videopath" : "{videofeed.videopath}",
            "state" : "{videofeed.state}",
            "countimage" : "{ci}",
            "videolength" : "{videofeed.videolength}",
            "numParticles" : "{videofeed.numParticles}"
            '''
    return('{' + s + '}')



@app.route('/testdata', methods=['POST', 'GET'])
def testdata():
    global videofeed

    if request.method == 'POST':
        print(request.form["data"])
        returnedData = json.loads(request.form["data"])
        for key, value in returnedData.items():
            print(key, value)
            if key == "videopath":
                value = '../VideoFiles/' + value.split('\\')[-1]
                print('\n\n', value)
            setattr(videofeed, key, value)

        if videofeed.selectionType == "auto":
            videofeed.settingChanged = True
    return "success"

@app.route('/results', methods=['POST', 'GET'])
def results():
    if request.method == 'POST':
        if request.form["fileToOpen"] == 'CSV':
            createCSVFile(videofeed.tracker.positions, videofeed.selections)

        elif request.form["fileToOpen"] == 'Excel':
            createExcelFile(videofeed.tracker.positions, videofeed.selections)
        
    print(videofeed.tracker.positions)
    print(json.dumps(videofeed.tracker.positions))
    return render_template('results.html')

@app.route('/positions', methods=['GET'])
def positions():
    response = {}
    response['pos'] = videofeed.tracker.positions
    response["height"], response["width"], _ = videofeed.selector.frame.shape


    print(videofeed.selections)
    response["sizes"] = [s["size"] * 1e6 if s["size"] is not None else s["size"] for s in videofeed.selections]
    
    return json.dumps(response)

@app.route("/downloadCSV")
def downloadCSV():
    csvFileName = f"{videofeed.videopath}.CSV"
    with open("CSVfile.csv", "r") as f:
        csv = f.read()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename={csvFileName}"})


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

   
if __name__ == '__main__':
    # threading.Timer(1.25, lambda: webbrowser.open('http://localhost:5000', new=2, autoraise=True) ).start()
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='localhost', debug=True)
