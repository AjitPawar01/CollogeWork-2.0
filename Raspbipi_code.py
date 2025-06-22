import cv2
import sys
import os
from mlx90614 import MLX90614
import RPi.GPIO as GPIO
import time
import lcd
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import imutils


import picamera
camera = picamera.PiCamera() 
camera.resolution = (1028, 720)



LCD_RS = 11
LCD_E  = 9
LCD_D4 = 10
LCD_D5 = 22
LCD_D6 = 27
LCD_D7 = 17

BUZ = 4
led = 18

ma1 = 23
ma2 = 24

def main():

        GPIO.setmode(GPIO.BCM)      
        GPIO.setup(LCD_E, GPIO.OUT)  
        GPIO.setup(LCD_RS, GPIO.OUT)
        GPIO.setup(LCD_D4, GPIO.OUT) 
        GPIO.setup(LCD_D5, GPIO.OUT) 
        GPIO.setup(LCD_D6, GPIO.OUT) 
        GPIO.setup(LCD_D7, GPIO.OUT) 
    
        GPIO.setup(BUZ, GPIO.OUT) 
        GPIO.setup(led, GPIO.OUT) 
        
        GPIO.setup(ma1, GPIO.OUT) 
        GPIO.setup(ma2, GPIO.OUT) 
    
        lcd_init()
        lcd_string("Hello Welcome",LCD_LINE_1)
        lcd_string("Monitoring...",LCD_LINE_2)
    
        GPIO.output(ma2, False) 
        GPIO.output(ma1, False) 
                    
        GPIO.output(BUZ, True) 
        
        GPIO.output(led, True)
        time.sleep(0.7) 
        GPIO.output(BUZ, False) 
        GPIO.output(led, False) 
        time.sleep(0.7)     
        GPIO.output(BUZ, True) 
        GPIO.output(led, True) 
        time.sleep(0.7) 
        GPIO.output(BUZ, False) 
        GPIO.output(led, False) 
        temp = 0
        def detect_and_predict_mask(frame, faceNet, maskNet):
    
            (h, w) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(frame, 1.0, (224, 224),
            (104.0, 177.0, 123.0))
            faceNet.setInput(blob)
            detections = faceNet.forward()
    
            faces = []
            locs = []
            preds = []

            for i in range(0, detections.shape[2]):
        
                confidence = detections[0, 0, i, 2]

                if confidence > 0.5:
            
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")

                    (startX, startY) = (max(0, startX), max(0, startY))
                    (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

                    face = frame[startY:endY, startX:endX]
                    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                    face = cv2.resize(face, (224, 224))
                    face = img_to_array(face)
                    face = preprocess_input(face)

                    faces.append(face)
                    locs.append((startX, startY, endX, endY))
            if len(faces) > 0:
        
                faces = np.array(faces, dtype="float32")
                preds = maskNet.predict(faces, batch_size=32)

    
            return (locs, preds)


        prototxtPath = r"/home/pi/face_detector/deploy.prototxt.txt"
        weightsPath = r"/home/pi/face_detector/res10_300x300_ssd_iter_140000.caffemodel11"
        faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

        maskNet = load_model("/home/pi/mask_detector.model")


      
        while True:
            camera.capture('img.jpg')
            time.sleep(0.1)
            img = cv2.imread('img.jpg')
            frame = imutils.resize(img, width=400)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            (locs, preds) = detect_and_predict_mask(gray, faceNet, maskNet)
            bus = SMBus(1)
            sensor = MLX90614(bus, address=0x5A)
            bt = sensor.get_object_1()                
            
            fbt = float(bt)*float(1.8)                
            fbt = fbt+32
            
            data = "Temp:"+str(fbt)+" Fh"
            
            lcd_byte(0x01, LCD_CMD)
            lcd_string(data,LCD_LINE_1) 
            
            for (box, pred) in zip(locs, preds):
        
                (startX, startY, endX, endY) = box
                (mask, withoutMask) = pred

                label = "Mask" if mask > withoutMask else "No Mask"
            
                if temp == 0:
                    
                    lcd_string("Show the hand     ",LCD_LINE_2) 
                        
                if temp == 1:
                    
                    lcd_string("Checking Mask  ",LCD_LINE_2) 
                                        
                if fbt > 90 and fbt < 100.8:
                   
                    lcd_string("Temp is fine",LCD_LINE_2)              
                    time.sleep(1.6)
                    temp = 1

                if fbt > 100.8:
                    temp = 0
                   
                    lcd_string("Temp is High ",LCD_LINE_2) 
                    GPIO.output(BUZ, True)
                    GPIO.output(led, False) 
                    time.sleep(0.7)
                else:
                    
                    GPIO.output(BUZ, False) 
                    
                if label=="No Mask" and temp == 1:
                    temp = 0
                    lcd_string("No Mask Detected   ",LCD_LINE_2) 
                    
                    GPIO.output(BUZ, True)
                    GPIO.output(led, False) 
                        
                if label=="Mask" and temp == 1:

                    temp = 0
                    lcd_string("Mask is Detected  ",LCD_LINE_2) 
                    time.sleep(1.6)
                    lcd_string("Gate Opened      ",LCD_LINE_1) 
                    
                    lcd_string("    WELCOME      ",LCD_LINE_2) 
                
                        
                    GPIO.output(led, True) 
                
                    GPIO.output(ma1, True) 
                   
                    GPIO.output(ma2, False) 
                    time.sleep(0.7) 
                    GPIO.output(ma2, False) 
                    GPIO.output(ma1, False) 
    
                    time.sleep(4) 
                    
                    GPIO.output(ma2, True) 
                    GPIO.output(ma1, False) 

                    time.sleep(0.7) 
                    GPIO.output(ma2, False) 
                    GPIO.output(ma1, False) 
                    
                   
                    lcd_byte(0x01, LCD_CMD)
                    lcd_string("Gate Closed    ",LCD_LINE_1) 
        
                    time.sleep(1.6) 
                
                    GPIO.output(led, False) 
       
                
                
main()
