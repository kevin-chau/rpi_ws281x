#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import time
from neopixel import *
import argparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from time import strftime, sleep
from urlparse import urlparse, parse_qs
from math import log
import json

# Light state
lightstate = {"on" : False, "bri": 0, "xy": [0.0, 0.0], "ct": 153, "hue": 0, "sat": 0, "colormode": "ct"}

# LED strip configuration:
LED_COUNT      = 150      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

def convert_xy(x, y, bri): #needed for milight hub that don't work with xy values
    Y = bri / 250.0
    z = 1.0 - x - y

    X = (Y / y) * x
    Z = (Y / y) * z

  # sRGB D65 conversion
    r =  X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b =  X * 0.051713 - Y * 0.121364 + Z * 1.011530

    if r > b and r > g and r > 1:
    # red is too big
        g = g / r
        b = b / r
        r = 1

    elif g > b and g > r and g > 1:
    #green is too big
        r = r / g
        b = b / g
        g = 1

    elif b > r and b > g and b > 1:
    # blue is too big
        r = r / b
        g = g / b
        b = 1

    r = 12.92 * r if r <= 0.0031308 else (1.0 + 0.055) * pow(r, (1.0 / 2.4)) - 0.055
    g = 12.92 * g if g <= 0.0031308 else (1.0 + 0.055) * pow(g, (1.0 / 2.4)) - 0.055
    b = 12.92 * b if b <= 0.0031308 else (1.0 + 0.055) * pow(b, (1.0 / 2.4)) - 0.055

    if r > b and r > g:
    # red is biggest
        if r > 1:
            g = g / r
            b = b / r
            r = 1
        elif g > b and g > r:
        # green is biggest
            if g > 1:
                r = r / g
                b = b / g
                g = 1

        elif b > r and b > g:
        # blue is biggest
            if b > 1:
                r = r / b
                g = g / b
                b = 1

    r = 0 if r < 0 else r
    g = 0 if g < 0 else g
    b = 0 if b < 0 else b

    return [int(r * 255), int(g * 255), int(b * 255)]

def convert_ct(ct, bri):
    hectemp = 10000 / ct
    r = 0
    g = 0
    b = 0
    if hectemp <= 66:
        r = 255;
        g = 99.4708025861 * log(hectemp) - 161.1195681661
        b = 0 if hectemp <= 19 else (138.5177312231 * log(hectemp - 10) - 305.0447927307)
    else:
        r = 329.698727446 * pow(hectemp - 60, -0.1332047592)
        g = 288.1221695283 * pow(hectemp - 60, -0.0755148492)
        b = 255;

    r = 255 if r > 255 else r
    g = 255 if g > 255 else g
    b = 255 if r > 255 else b
    return [ int(r * (bri / 255.0)), int(g * (bri / 255.0)), int(b * (bri / 255.0))]



class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        if self.path.startswith("/get"):
            self.wfile.write(json.dumps(lightstate))
        elif self.path.startswith("/set"):
            get_parameters = parse_qs(urlparse(self.path).query)
            if "on" in get_parameters:
                if get_parameters["on"][0] == "True":
                    lightstate["on"] = True
                    print("start pwm on all channels. If last state is not automatically applied, then execute the function that is set in lightstate[\"colormode\"] again")
                    setColor(strip, Color(0, 255, 0))  # Set strip to red
                elif get_parameters["on"][0] == "False":
                    lightstate["on"] = False
                    print("stop pwm on all channels")
                    setColor(strip, Color(0, 0, 0))  # Set strip to red
            if "bri" in get_parameters:
                lightstate["bri"] = int(get_parameters["bri"][0])
                print("setup bri to " + get_parameters["bri"][0])
                strip.setBrightness(int(get_parameters["bri"][0]));
                strip.show()
            if "ct" in get_parameters:
                lightstate["ct"] = int(get_parameters["ct"][0])
                lightstate["colormode"] = "ct"
            elif "x" in get_parameters:
                lightstate["xy"] = [float(get_parameters["x"][0]), float(get_parameters["y"][0])]
                lightstate["colormode"] = "xy"

            if lightstate["on"] == True:
                if lightstate["colormode"] == "xy":
                    raw_hue_rgb = convert_xy(lightstate["xy"][0], lightstate["xy"][1], lightstate["bri"])
                    #convert this from 0 <-> 255 to 0.0 <-> 1.0
                    pwm_rgb = [raw_hue_rgb[0] / 255.0, raw_hue_rgb[1] / 255.0, raw_hue_rgb[2] / 255.0]
                    print("red: " + str(pwm_rgb[0]) + ", green: " + str(pwm_rgb[1]) + ", blue: " + str(pwm_rgb[2]))

                elif lightstate["colormode"] == "ct":
                    raw_hue_rgb = convert_ct(lightstate["ct"], lightstate["bri"])
                    #convert this from 0 <-> 255 to 0.0 <-> 1.0
                    pwm_rgb = [raw_hue_rgb[0] / 255.0, raw_hue_rgb[1] / 255.0, raw_hue_rgb[2] / 255.0]
                    print("red: " + str(pwm_rgb[0]) + ", green: " + str(pwm_rgb[1]) + ", blue: " + str(pwm_rgb[2]))

            self.wfile.write("OK")
        else:
            self.wfile.write("WRONG PATH")



def run(server_class=HTTPServer, handler_class=S):
    server_address = ('', 81)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

# Define functions which animate LEDs in various ways.
def setColor(strip, color):
    """Set all the pixels to the same color all at once"""
    
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()

# Main program logic follows:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    print ('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    try:
        run()
 
    except KeyboardInterrupt:
        if args.clear:
            setColor(strip, Color(0,0,0))
