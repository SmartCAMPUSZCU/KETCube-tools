#!/usr/bin/python
# -*- coding: utf-8 -*-
#

## @file rxDisplayPlot.py
#
# @author Jan Belohoubek
# @version 0.1
# @date    2018-05-07
# @brief   Read data from the KETCube RxDisplay and show graph of values
#
# This script is intended for RxDisplay hex values produced by 
# StarNetConcentrator module
#
# Received data are converted to 0 - 100 % of the defined range. 
# The resulting relative value is plotted.
#
# First CALIB_CNT values are used for calibration. 
# If you want to skip calibration, set CALIB_CNT to 0 and 
# calib_min and calib_max to ẗheir respective values.
#
#
# @note LiveGraph HoWTo: https://pythonprogramming.net/live-graphs-matplotlib-tutorial/
#
# @attention
# 
#  <h2><center>&copy; Copyright (c) 2018 University of West Bohemia in Pilsen
#  All rights reserved.</center></h2>
# 
#  Developed by:
#  The SmartCampus Team
#  Department of Technologies and Measurement
#  www.smartcampus.cz | www.zcu.cz
# 
#  Permission is hereby granted, free of charge, to any person obtaining a copy 
#  of this software and associated documentation files (the “Software”), 
#  to deal with the Software without restriction, including without limitation 
#  the rights to use, copy, modify, merge, publish, distribute, sublicense, 
#  and/or sell copies of the Software, and to permit persons to whom the Software 
#  is furnished to do so, subject to the following conditions:
# 
#     - Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimers.
#     
#     - Redistributions in binary form must reproduce the above copyright notice, 
#       this list of conditions and the following disclaimers in the documentation 
#       and/or other materials provided with the distribution.
#     
#     - Neither the names of The SmartCampus Team, Department of Technologies and Measurement
#       and Faculty of Electrical Engineering University of West Bohemia in Pilsen, 
#       nor the names of its contributors may be used to endorse or promote products 
#       derived from this Software without specific prior written permission. 
# 
#  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
#  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
#  PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT HOLDERS 
#  BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
#  OR THE USE OR OTHER DEALINGS WITH THE SOFTWARE.

import sys
import serial
import serial.tools.list_ports

# Graphing ...
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import signal

# Debug ON/OFF
DEBUG=True
# Interpreter
TERMINAL="cmd" # bash or cmd
#List com ports?
COM_LIST=True

# Connection options
COM="COM0"
SPEED=9600
TIMEOUT=1000

# Parsing options -- bytes to parse
PARSED_MSB=1
PARSED_LSB=4

# Strings
if (TERMINAL == "bash"):
    STR_ERROR= "\033[91m[ERROR]\033[0m   "
    STR_WARN = "\033[93m[WARNING]\033[0m "
    STR_INFO = "[INFO]    "
else:
    STR_ERROR= "[ERROR]   "
    STR_WARN = "[WARNING] "
    STR_INFO = "[INFO]    "

# Graph options
POINT_CNT=10 # number of points in graph
points_arr = []
points_ptr = 0
points_sample = 0

for i in range(POINT_CNT):
    points_arr.append((0,0))

# Correct exit
def exit_gracefully(signum, frame):
    exit(0)

signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
    
# Calibration
CALIB_CNT=10 # number of points for calibration
calib_min = 0
calib_max = 0

calib_arr = []
calib_ptr = 0

for i in range(CALIB_CNT):
    calib_arr.append((i,0))

mpl.rcParams['toolbar'] = 'None' # disable toolbar
style.use('fivethirtyeight')
LiveGraphFig  = plt.figure()
LiveGraphPlot = LiveGraphFig.add_subplot(1,1,1)

# Graph animation
def liveGraphAnimation(i):
    global DEBUG
    global plt
    global points_arr, points_ptr
    global calib_arr, calib_ptr, calib_min, calib_max
    
    # return when not calibrated yet
    if (calib_ptr < CALIB_CNT):
        return
    
    xs = []
    ys = []
    for i in range(POINT_CNT):
        xs.append(points_arr[(points_ptr + i) % POINT_CNT][0])
        ys.append(points_arr[(points_ptr + i) % POINT_CNT][1])
    LiveGraphPlot.clear()
    LiveGraphPlot.plot(xs, ys)
    plt.ylim((-5,105))
    plt.title('Sensor data')
    
    if (DEBUG == True):
        print(STR_INFO + "Updating graph .. ")

# --- User input ---
if COM_LIST == True:
    COM = ""
    print("Available COM ports: ")
    for p in serial.tools.list_ports.comports():
        print(((p.description).decode('utf8')).encode('ascii',errors='ignore')+": "+((p.device).decode('utf8')).encode('ascii',errors='ignore'))
        if 'TTL232R-3V3' in p.description:
            COM=p.device
        if 'USB Serial Port' in p.description:
            COM=p.device

    if COM == "":
        print(STR_ERROR + "KETCube port not found! Connection FAILED!")
        raw_input("Press ENTER to exit")
        sys.exit(1)

COM = raw_input("Select COM port [" + COM + "]:") or str(COM)

# --- Start ---

if (DEBUG == True):
    print(STR_INFO + "Connecting serial monitor: "  + str(COM) + "; " + str(SPEED) + "; "+ str(TIMEOUT) + "!")

try:
    with serial.Serial(COM, SPEED, timeout=TIMEOUT) as ser:
        if (DEBUG == True):
            print(STR_INFO + "Connected: "  + str(COM) + "; " + str(SPEED) + "; "+ str(TIMEOUT) + "!")

        # --- Init graph ---
        GraphAni = animation.FuncAnimation(LiveGraphFig, liveGraphAnimation, interval=200)
        plt.title('Calibration ...')
        plt.pause(.001) # force graph update ...
            
        while True:
            line = ser.readline()
            
            # --- PARSE DATA START ---
            try:
                if (line.find("rxDisplay ::") > 0):
                    parts = line.split(" ")
                    for sub in parts:
                        if (sub.find("DATA=") > 0):
                            data=sub.split("=")[1]
                            data=data.split("-")
                            
                            decodedNumber = 0
                            shift = 8 * abs(PARSED_MSB - PARSED_LSB)
                            if (DEBUG == True):
                                print(STR_INFO + "Received data ALL     : "  + str(data))
                                
                            for i in range(PARSED_MSB, PARSED_LSB+1):
                                decodedNumber = decodedNumber + (int(data[i],16) << shift)
                                shift = shift - 8
                            
                            if (DEBUG == True):
                                print(STR_INFO + "Received data SELECTED: "  + str(decodedNumber))
                            
                            # store calib data
                            if (calib_ptr < CALIB_CNT):
                                calib_arr[calib_ptr] = decodedNumber
                                calib_ptr = calib_ptr + 1
                                break
                            elif (CALIB_CNT = 0):
                                calib_ptr = calib_ptr + 1
                            elif (calib_ptr == CALIB_CNT):
                                calib_min = min(calib_arr)
                                calib_max = max(calib_arr)
                                calib_ptr = calib_ptr + 1
                                if (DEBUG == True):
                                    print(STR_INFO + "Calibrated data range: ["  + str(calib_min) + ", " + str(calib_max) + "]")
                                if (abs(calib_max - calib_min) == 0):
                                    print(STR_ERROR + "Calibration range invalid! REPEAT CALIBRATION!")
                                    exit(0)
                                
                            # place into array
                            normalized = 100.0* ((1.0 * abs(decodedNumber - calib_min))/(abs(calib_max - calib_min)))
                            normalized = max(normalized, 0)
                            normalized = min(normalized, 100)
                            points_arr[points_ptr] = (points_sample, normalized)
                            points_ptr = (points_ptr + 1) % POINT_CNT
                            points_sample = points_sample + 1
                            
                            plt.pause(.001) # force graph update ...
                            
                            break
            except:
                continue
            # --- PARSE DATA END ---
        
except serial.SerialException as e:
    print(STR_ERROR + "Connection to KETCube (" + str(COM) + ") FAILED! See trace:")
    print(e)

