#!/usr/bin/env python
# license removed for brevity
import rospy
from std_msgs.msg import String
import numpy as np
import pandas as pd
import cv2
import os
import glob
import matplotlib.pyplot as plt
import pickle
import math
from numpy import linalg as LA
from moviepy.editor import VideoFileClip
from os.path import expanduser

roi_x = 0
roi_y = 500
max_value_H = 360/2
max_value = 255
low_H = 0
low_S = 0
low_V = 0
high_H = max_value_H
high_S = max_value
high_V = 145

left_a, left_b, left_c = [],[],[]
right_a, right_b, right_c = [],[],[]

def getRect(vector, center, size):
    angle = np.arctan2(vector[0], vector[1]) * 180 / math.pi
    if angle < 0:
        angle = angle + 360
    if 45 <= angle and angle <= 135:
        topLeft = np.add(center, [0, -size])
        bottomLeft = np.add(center, [size, -size])
        bottomRight = np.add(center, [size, size])
        topRight = np.add(center, [0, size])
    elif 135 <= angle and angle <= 225:
        topLeft = np.add(center, [-size, -size])
        bottomLeft = np.add(center, [size, -size])
        bottomRight = np.add(center, [size, 0])
        topRight = np.add(center, [-size, 0])
    elif 225 <= angle and angle <= 315:
        topLeft = np.add(center, [-size, -size])
        bottomLeft = np.add(center, [0, -size])
        bottomRight = np.add(center, [0, size])
        topRight = np.add(center, [-size, size])
    elif 315 <= angle or angle <= 45:
        topLeft = np.add(center, [-size, 0])
        bottomLeft = np.add(center, [size, 0])
        bottomRight = np.add(center, [size, size])
        topRight = np.add(center, [-size, size])

    return topLeft, bottomLeft, bottomRight, topRight

def seekForward(img, changeVector, oldCenter, windowSize):
        counter = 0

        # Each iteration is a fresh search attempt farther out from the last known lane point
        while (1):
            counter += 1
            # Break out if max iteartion exceeded
            if counter > 5:
                return None, None, None
            topLeft, bottomLeft, bottomRight, topRight = getRect(changeVector, oldCenter, windowSize)
            #print topLeft, bottomLeft, bottomRight, topRight
            if topLeft[0] < 0 or bottomLeft[0] > img.shape[0] - 1 or bottomLeft[1] < 0 or bottomRight[1] > img.shape[1] - 1:
                return None, None, None
            block = img[topLeft[0]:bottomLeft[0], bottomLeft[1]:bottomRight[1]]
            whitePixels = np.argwhere(block == 255)
            if len(whitePixels):
             avgPixel = np.mean(whitePixels, axis=0)
             try:
                newCenter = [topLeft[0] + int(avgPixel[0]), topLeft[1] + int(avgPixel[1])]
                return avgPixel, whitePixels, newCenter
             except Exception, e:
                center = np.add(oldCenter, changeVector)
                #cv2.circle(img, tuple(oldCenter[::-1]), 5, (0, 0, 255), -1)
            return None, None, None

def sliding_window1(img, nwindows=9, margin=50, minpix = 1, draw_windows=True):
    global left_a, left_b, left_c,right_a, right_b, right_c
    left_fit_= np.empty(3)
    right_fit_ = np.empty(3)
    out_img = np.dstack((img, img, img))*255

    # find peaks of left and right halves
    histogram = np.sum(warped_img[img.shape[0]//2:,:], axis=0) # Histrogram
    midpoint = int(histogram.shape[0]/2)
    leftx_base = np.argmax(histogram[:midpoint])
    rightx_base = np.argmax(histogram[midpoint:]) + midpoint

    # Set height of windows
    window_height = np.int(img.shape[0]/nwindows)
    # Identify the x and y positions of all nonzero pixels in the image
    nonzero = img.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])
    # Current positions to be updated for each window
    leftx_current = leftx_base
    rightx_current = rightx_base

    # Set height of windows
    window_height = np.int(img.shape[0]/nwindows)
    # Identify the x and y positions of all nonzero pixels in the image
    nonzero = img.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])
    # Current positions to be updated for each window
    leftx_current = leftx_base
    rightx_current = rightx_base

    prev_point = []

    for window in range(nwindows):
      # Identify window boundaries in x and y (and right and left)
      win_y_low = img.shape[0] - (window+1)*window_height
      win_y_high = img.shape[0] - window*window_height
      win_xleft_low = leftx_current - margin
      win_xleft_high = leftx_current + margin
      win_xright_low = rightx_current - margin
      win_xright_high = rightx_current + margin

      # Identify the nonzero pixels in x and y within the window
      good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
      (nonzerox >= win_xleft_low) &  (nonzerox < win_xleft_high)).nonzero()[0]
      good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
      (nonzerox >= win_xright_low) &  (nonzerox < win_xright_high)).nonzero()[0]

      # If you found > minpix pixels, recenter next window on their mean position
      if len(good_left_inds) > minpix:
            leftx_current = np.int(np.mean(nonzerox[good_left_inds]))
      if len(good_right_inds) > minpix:
            rightx_current = np.int(np.mean(nonzerox[good_right_inds]))

      win_y_low1 = img.shape[0] - (window+1)*window_height
      win_y_high1 = img.shape[0] - window*window_height
      win_xleft_low1 = leftx_current - margin
      win_xleft_high1 = leftx_current + margin
      win_xright_low1 = rightx_current - margin
      win_xright_high1 = rightx_current + margin

      cv2.circle(out_img, (leftx_current, (win_y_low1+win_y_high1)/2), 8, (0, 0, 255), -1)
      cv2.rectangle(out_img, (win_xleft_low1, win_y_low1), (win_xleft_high1, win_y_high1), (100,255,255), 3)
      cv2.rectangle(out_img, (win_xright_low1, win_y_low1), (win_xright_high1, win_y_high1), (100,255,255), 3)

      # Calcaute the tangential angle between center of the last two windows
      if window>0:
       theta = math.atan2(prev_point[1]-(win_y_low1+win_y_high1)/2,prev_point[0]-leftx_current)-1.57
       leftx_current1 = ((leftx_current-prev_point[0])*math.cos(theta)-(((win_y_low1+win_y_high1)/2)-prev_point[1])*math.sin(theta))
       #print("Edge direction:", theta)
       #print leftx_current, leftx_current1, leftx_current1+prev_point[0]

       cv2.circle(out_img, (int(leftx_current1+prev_point[0]), (win_y_low1+win_y_high1)/2), 8, (0, 0, 255), -1)
       win_xleft_low2 = int(leftx_current1+prev_point[0]) - margin
       win_xleft_high2 = int(leftx_current1+prev_point[0]) + margin
       cv2.rectangle(out_img, (win_xleft_low2, win_y_low1), (win_xleft_high2, win_y_high1), (0,0,255), 3)

      # UPDATE THE leftx_current, rightx_current
      prev_point = [leftx_current, (win_y_low1+win_y_high1)/2]

    return out_img

def sliding_window(img, nwindows=9, margin=75, minpix = 1, draw_windows=True):
    global left_a, left_b, left_c,right_a, right_b, right_c
    left_fit_= np.empty(3)
    right_fit_ = np.empty(3)
    out_img = np.dstack((img, img, img))*255

    # find peaks of left and right halves
    histogram = np.sum(warped_img[img.shape[0]//2:,:], axis=0) # Histrogram
    midpoint = int(histogram.shape[0]/2)
    leftx_base = np.argmax(histogram[:midpoint])
    rightx_base = np.argmax(histogram[midpoint:]) + midpoint

    # Set height of windows
    window_height = np.int(img.shape[0]/nwindows)
    # Identify the x and y positions of all nonzero pixels in the image
    nonzero = img.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])
    # Current positions to be updated for each window
    leftx_current = leftx_base
    rightx_current = rightx_base

    # Create empty lists to receive left and right lane pixel indices
    left_lane_inds = []
    right_lane_inds = []
    left_lane_inds1= []
    right_lane_inds1 = []

    # empty lists to store the information of lane
    points = []
    confidenceValues = [1]

    # Step through the windows one by one
    for window in range(nwindows):
        # Identify window boundaries in x and y (and right and left)
        win_y_low = img.shape[0] - (window+1)*window_height
        win_y_high = img.shape[0] - window*window_height
        win_xleft_low = leftx_current - margin
        win_xleft_high = leftx_current + margin
        win_xright_low = rightx_current - margin
        win_xright_high = rightx_current + margin
        #if top < 0 or bottom > self.height - 1 or left < 0 or right > self.width - 1:
                #break

        # Identify the nonzero pixels in x and y within the window
        good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
        (nonzerox >= win_xleft_low) &  (nonzerox < win_xleft_high)).nonzero()[0]
        good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
        (nonzerox >= win_xright_low) &  (nonzerox < win_xright_high)).nonzero()[0]
        block_o= img[win_y_low:win_y_high, win_xleft_low:win_xleft_high]
        whitePixels_o = np.argwhere(block_o == 255)

        # Append these indices to the lists
        left_lane_inds.append(good_left_inds)
        right_lane_inds.append(good_right_inds)

        # If you found > minpix pixels, recenter next window on their mean position
        if len(good_left_inds) > minpix:
            leftx_current = np.int(np.mean(nonzerox[good_left_inds]))
        if len(good_right_inds) > minpix:
            rightx_current = np.int(np.mean(nonzerox[good_right_inds]))

        counter = 0
        step_size = 15
        leftx_current1 = leftx_current
        rightx_current1 = rightx_current
        whitePixelsvector_l = []
        whitePixelsvector_r = []

        # Each iteration is a fresh search attempt farther out from the last known lane point
        while (1):
            counter += 1
            leftx_current1 = leftx_current1+step_size
            rightx_current1 = rightx_current1+step_size
            # Break out if max iteartion exceeded
            if counter > 3:
             break
            win_y_low1 = img.shape[0] - (window+1)*window_height
            win_y_high1 = img.shape[0] - window*window_height
            win_xleft_low1 = leftx_current1 - margin
            win_xleft_high1 = leftx_current1 + margin
            win_xright_low1 = rightx_current1 - margin
            win_xright_high1 = rightx_current1 + margin

            # Identify the nonzero pixels in x and y within the window
            block_l = img[win_y_low1:win_y_high1, win_xleft_low1:win_xleft_high1]
            whitePixels_l = np.argwhere(block_l == 255)
            block_r = img[win_y_low1:win_y_high1, win_xright_low1:win_xright_high1]
            whitePixels_r = np.argwhere(block_r == 255)
            if whitePixels_l is not None:
              #print window, len(whitePixels_o), len(whitePixels) #avgPixel, newCenter, changeVector, rotatevvector
              whitePixelsvector_l.append(len(whitePixels_l))
            if whitePixels_r is not None:
              #print window, len(whitePixels_o), len(whitePixels_r) #avgPixel, newCenter, changeVector, rotatevvector
              whitePixelsvector_r.append(len(whitePixels_r))

        # Draw the windows on the visualization image
        #for whitePixels in whitePixelsvector:
        if len(whitePixelsvector_l)>0: #draw_windows == True
           #print np.max(whitePixelsvector)
           if np.max(whitePixelsvector_l) > len(whitePixels_o):
              cv2.rectangle(out_img,(win_xleft_low1,win_y_low1),(win_xleft_high1,win_y_high1),(0,0,255), 3)
              curr_win_xleft = [win_xleft_low1, win_xleft_high1]
           else:
              cv2.rectangle(out_img,(win_xleft_low,win_y_low),(win_xleft_high,win_y_high), (100,255,255), 3)
              curr_win_xleft = [win_xleft_low1, win_xleft_high1]

        if len(whitePixelsvector_r)>0: #draw_windows == True
           if np.max(whitePixelsvector_r) > len(whitePixels_o):
              cv2.rectangle(out_img,(win_xright_low1,win_y_low1),(win_xright_high1,win_y_high1),(0,0,255), 3)
              curr_win_xright = [win_xright_low1, win_xright_high1]
           else:
              cv2.rectangle(out_img,(win_xright_low,win_y_low),(win_xright_high,win_y_high),(100,255,255), 3)
              curr_win_xright = [win_xright_low1, win_xright_high1]

        # Identify the nonzero pixels in x and y within the window
        good_left_inds1 = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
        (nonzerox >= curr_win_xleft[0]) &  (nonzerox < curr_win_xleft[1])).nonzero()[0]
        good_right_inds1 = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
        (nonzerox >= curr_win_xright[0]) &  (nonzerox < curr_win_xright[1])).nonzero()[0]

        # Append these indices to the lists
        left_lane_inds1.append(good_left_inds1)
        right_lane_inds1.append(good_right_inds1)

    # Concatenate the arrays of indices
    left_lane_inds1 = np.concatenate(left_lane_inds1)
    right_lane_inds1 = np.concatenate(right_lane_inds1)

    # Extract left and right line pixel positions
    leftx = nonzerox[left_lane_inds1]
    lefty = nonzeroy[left_lane_inds1]
    rightx = nonzerox[right_lane_inds1]
    righty = nonzeroy[right_lane_inds1]

    # Fit a second order polynomial to
    left_fit = np.polyfit(lefty, leftx, 2)
    right_fit = np.polyfit(righty, rightx, 2)

    left_a.append(left_fit[0])
    left_b.append(left_fit[1])
    left_c.append(left_fit[2])

    right_a.append(right_fit[0])
    right_b.append(right_fit[1])
    right_c.append(right_fit[2])

    left_fit_[0] = np.mean(left_a[-10:])
    left_fit_[1] = np.mean(left_b[-10:])
    left_fit_[2] = np.mean(left_c[-10:])

    right_fit_[0] = np.mean(right_a[-10:])
    right_fit_[1] = np.mean(right_b[-10:])
    right_fit_[2] = np.mean(right_c[-10:])

    # Generate x and y values for plotting
    ploty = np.linspace(0, img.shape[0]-1, img.shape[0] )
    left_fitx = left_fit_[0]*ploty**2 + left_fit_[1]*ploty + left_fit_[2]
    right_fitx = right_fit_[0]*ploty**2 + right_fit_[1]*ploty + right_fit_[2]

    out_img[nonzeroy[left_lane_inds1], nonzerox[left_lane_inds1]] = [255, 0, 100]
    out_img[nonzeroy[right_lane_inds1], nonzerox[right_lane_inds1]] = [0, 100, 255]

    return out_img, (left_fitx, right_fitx), (left_fit_, right_fit_), ploty

def perspective_warp(img,
                     dst_size=(1920,1080),
                     src=np.float32([(550.0,0.0),(1500,0),(1500,1023),(450,1034)]), # Choose the four vertices
                     dst=np.float32([(0,0), (1, 0), (1,1), (0,1)])):

    # For destination points, I'm arbitrarily choosing some points to be
    # a nice fit for displaying our warped result
    # again, not exact, but close enough for our purposes
    dst = dst * np.float32(dst_size)

    # Given src and dst points, calculate the perspective transform matrix
    M = cv2.getPerspectiveTransform(src, dst)
    # Warp the image using OpenCV warpPerspective()
    warped = cv2.warpPerspective(img, M, dst_size)
    return warped

def inv_perspective_warp(img, dst_size, src, dst):
    img_size = np.float32([(img.shape[1],img.shape[0])])
    src = src* img_size
    # For destination points, I'm arbitrarily choosing some points to be
    # a nice fit for displaying our warped result
    # again, not exact, but close enough for our purposes
    dst = dst * np.float32(dst_size)
    # Given src and dst points, calculate the perspective transform matrix
    M = cv2.getPerspectiveTransform(src, dst)
    # Warp the image using OpenCV warpPerspective()
    warped = cv2.warpPerspective(img, M, dst_size)
    return warped

def draw_lanes(img, left_fit, right_fit):
    ploty = np.linspace(0, img.shape[1]-1, img.shape[1])
    color_img = np.zeros_like(img)

    left = np.array([np.transpose(np.vstack([left_fit+roi_y, ploty]))])
    right = np.array([np.flipud(np.transpose(np.vstack([right_fit+roi_y, ploty])))])
    points = np.hstack((left, right))

    cv2.fillPoly(color_img, np.int_(points), (0,200,255))

    dst_size=(rwidth, rheight) #+roi_x +roi_y
    src=np.float32([(0,0), (1, 0), (0,1), (1,1)])
    dst=np.float32([(0,0), (1, 0), (0,1), (1,1)])
    inv_perspective = inv_perspective_warp(color_img, dst_size, src, dst)

    #print img.shape, inv_perspective.shape

    inv_perspective = cv2.addWeighted(img, 1, inv_perspective, 0.7, 0)

    return inv_perspective

if __name__ == '__main__':
  rospy.init_node('curved_lane_detector', anonymous=True)
  rospy.spin()


  # Load an color image in grayscale
  home = expanduser("~/ICRA_2020/curved_lane.jpg") #very_curved.png"
  img = cv2.imread(home) #'/home/saga/ICRA_2020/curved_lane.jpg')

  # Convert BGR to HSV
  hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
  height, width = hsv.shape[:2]

  # Getting ROI
  Roi = hsv[roi_y:height,roi_x:width] #-(roi_y+1),-(roi_x+1)

  # define range of blue color in HSV
  lower_t = np.array([low_H,low_S,low_V])
  upper_t = np.array([high_H,high_S,high_V])

  # Detect the object based on HSV Range Values v_min 71.65 v_max 179.0,242.25,200.60
  mask = cv2.inRange(Roi, lower_t, upper_t)

  # Opening the image
  kernel = np.ones((7,7),np.uint8)
  eroded = cv2.erode(mask, kernel, iterations = 1) # eroding + dilating = opening
  wscale = cv2.dilate(eroded, kernel, iterations = 1)
  ret,thresh = cv2.threshold(wscale,128,255,cv2.THRESH_BINARY_INV) # thresholding the image //THRESH_BINARY_INV

  # Perspective warp
  rheight, rwidth = thresh.shape[:2]
  warped_img = perspective_warp(thresh,dst_size=(rheight,rwidth),
                                src=np.float32([(250,0.0),(1200,0),(1200,1023-(roi_y+1)),(250,1034-(roi_y+1))]))

  # Sliding Window Search
  out_img, curves, lanes, ploty = sliding_window(warped_img)

  #print warped_img.shape

  Roi_c = cv2.cvtColor(Roi, cv2.COLOR_HSV2BGR)
  img_ = draw_lanes(Roi_c, curves[0], curves[1])

  #out_img = sliding_window1(warped_img)
  #print(np.asarray(curves).shape)

  #plt.imshow(out_img)
  #plt.plot(curves[0], ploty, color='yellow', linewidth=1)
  #plt.plot(curves[1], ploty, color='yellow', linewidth=1)
  #plt.show()
  #img_ = draw_lanes(Roi, curves[0], curves[1])
  #plt.imshow(img_, cmap='hsv')
  #plt.show()
  #print(np.asarray(curves).shape)

  img_dir = expanduser("~/warped_img.jpg")
  cv2.imwrite(img_dir, img_)

  #cv2.imshow('image',warped_img)
  #cv2.waitKey(0)
  #cv2.destroyAllWindows()

          # Modified Sliding Window Algorithm
          # Search along the path
          #changeVector = [70,0]
          #oldCenter = [leftx_current, (win_y_low+win_y_high)/2]
          #windowSize = 100
          #seek_angle = 0.2
          #changeVectors = [changeVector]

          # First perform seek forward behavior
          #avgPixel, whitePixels, newCenter = seekForward(img, changeVector, oldCenter, windowSize)

          # If first seek forward fails, perform two more shifted to the left and right by (no
          # concrete reason to use default .17)
          #if avgPixel is None:
             # create an anonymous function to map points to a new space based on the heading of the car
          #rotatevvector = [int(changeVector[0] * math.cos(seek_angle) + changeVector[1] * math.sin(seek_angle)),
          #int(changeVector[1] * math.cos(seek_angle) - changeVector[0] * math.sin(seek_angle))]

            #return None, None, None
            #topLeft, bottomLeft, bottomRight, topRight = getRect(changeVector, oldCenter, windowSize)
            #print topLeft, bottomLeft, bottomRight, topRight
            #if topLeft[0] < 0 or bottomLeft[0] > img.shape[0] - 1 or bottomLeft[1] < 0 or bottomRight[1] > img.shape[1] - 1:
                #return None, None, None
            #block = img[topLeft[0]:bottomLeft[0], bottomLeft[1]:bottomRight[1]]
            #whitePixels = np.argwhere(block == 255)
            #if len(whitePixels):
             #avgPixel = np.mean(whitePixels, axis=0)
             #try:
                #newCenter = [topLeft[0] + int(avgPixel[0]), topLeft[1] + int(avgPixel[1])]
                #return avgPixel, whitePixels, newCenter
             #except Exception, e:
                #center = np.add(oldCenter, changeVector)
        #avgPixel, whitePixels, newCenter = seekForward(img, rotatevvector, oldCenter, windowSize)

        #if avgPixel is None:
           # create an anonymous function to map points to a new space based on the heading of the car
            #rotatevvector = [int(changeVector[0] * math.cos(-seek_angle) + changeVector[1] * math.sin(-seek_angle)),
                                                         #int(changeVector[1] * math.cos(-seek_angle) - changeVector[0] * math.sin(-seek_angle))]
            #avgPixel, whitePixels, newCenter = seekForward(img, rotatevvector, oldCenter, windowSize)
            #print window, avgPixel, newCenter
            #print window, changeVector,rotatevvector


            # add the confidence value correpsonding to point
            # this is represented by the number of white pixels used to get the point
            # less white pixels is lower confidence (direct inverse proportional)
            #confidenceValues.append(len(whitePixels))
            # the unweighted new change vector
            #rawChangeVector = np.subtract(newCenter, oldCenter)

            # Normalize the change vector's magnitude against the step size for consistent stepping distances
            #magnitude = LA.norm(rawChangeVector)
            #scaleFactor = step_size / magnitude
            #changeVector = np.multiply(scaleFactor, rawChangeVector).astype(int)

            # Set the newCenter to the scaled Unweighted vector
            #newCenter = np.add(oldCenter, changeVector)
            #oldCenter = newCenter
            #points.append(newCenter)

            # Weight the change vector based on the previous change vector
            # The two are weighted using their correpsonding confidence values and added
            #totalConfidence = confidenceValues[-1] + confidenceValues[-2]
            #oldVectorWeighted = np.multiply(changeVectors[-1], confidenceValues[-2] / totalConfidence)
            #currentVectorWeighted = np.multiply(changeVector, confidenceValues[-1] / totalConfidence)
            #changeVector = np.add(oldVectorWeighted, currentVectorWeighted)
            #magnitude = LA.norm(changeVector)
            #if magnitude != 0:
             #scaleFactor = step_size / magnitude
             #changeVector = np.multiply(scaleFactor, changeVector).astype(int)

             # Store this weighted change Vector
             #changeVectors.append(changeVector)

        #if newCenter is not None:
         #win_y_low1 = newCenter[1] - (2)*margin
         #win_y_high1 = newCenter[1] + (2)*margin
         #win_xleft_low1 = newCenter[0] - margin
         #win_xleft_high1 = newCenter[0] + margin
         #cv2.rectangle(out_img,(win_xleft_low1,win_y_low1),(win_xleft_high1,win_y_high1),
            #(0,0,255), 3)
