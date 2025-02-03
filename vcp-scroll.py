#!/usr/bin/env python3

import sys
sys.path.insert(0, "/home/carsten/.local/lib/python3.7/site-packages")

import cv2
import os
import time
import numpy as np
import random
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat-pwm'  # If you have an Adafruit HAT: 'adafruit-hat'
options.gpio_slowdown = 4
options.panel_type = 'FM6126A'
#options.panel_type = 'FM6126A'
matrix = RGBMatrix(options = options)

# Load the entire CryptoPunks image
img_name = "punks.png"
all_img = cv2.imread(img_name, cv2.IMREAD_UNCHANGED)

# Constants
PUNK_SIZE = 24  # Each Punk in the source sheet is 24x24
MATRIX_SIZE = 64  # Displayed Punk size on the LED matrix
PUNKS_PER_ROW = 100  # Number of punks per row in the sprite sheet
SCROLL_SPEED = 0.1  # Speed of scrolling (seconds per frame)

# Generate initial punk queue (3 punks, for smooth scrolling)
punk_queue = [
    random.randint(0, 9999),  # Left Punk
    random.randint(0, 9999),  # Center Punk
    random.randint(0, 9999)   # Right Punk (new one entering)
]

# Initial scroll position (start with center visible, right punk coming in)
scroll_x = 0


def get_punk_coords(index):
    """Get the x, y coordinates of a punk in the sprite sheet."""
    x = (index % PUNKS_PER_ROW) * PUNK_SIZE
    y = (index // PUNKS_PER_ROW) * PUNK_SIZE
    return x, y

def overlay_transparent(background_img, img_to_overlay_t, x, y, overlay_size=None):
    """
    @brief      Overlays a transparant PNG onto another image using CV2

    @param      background_img    The background image
    @param      img_to_overlay_t  The transparent image to overlay (has alpha channel)
    @param      x                 x location to place the top-left corner of our overlay
    @param      y                 y location to place the top-left corner of our overlay
    @param      overlay_size      The size to scale our overlay to (tuple), no scaling if None

    @return     Background image with overlay on top
    """
    bg_img = background_img.copy()
    if overlay_size is not None:
        img_to_overlay_t = cv2.resize(img_to_overlay_t.copy(), overlay_size)
    # Extract the alpha mask of the RGBA image, convert to RGB
    b,g,r,a = cv2.split(img_to_overlay_t)
    overlay_color = cv2.merge((b,g,r))
    # Blend
    mask = cv2.medianBlur(a,1)
    h, w, _ = overlay_color.shape
    roi = bg_img[y:y+h, x:x+w]
    # Black-out the area behind the logo in our original ROI
    img1_bg = cv2.bitwise_and(roi.copy(),roi.copy(),mask = cv2.bitwise_not(mask))
    # Mask out the logo from the logo image.
    img2_fg = cv2.bitwise_and(overlay_color,overlay_color,mask = mask)
    # Update the original image with our new ROI
    bg_img[y:y+h, x:x+w] = cv2.add(img1_bg, img2_fg)
    return bg_img


def cp_backg(img, color=None, x=24,y=24):
    colors = {}
    colors['blue'] = np.array([95,133,149]) // 2
    colors['purple'] = np.array([145,11,179]) //2
    colors['green'] = np.array([92,166,116]) //2
    colors['brown'] = np.array([154,85,80]) //2
    background = np.arange(y*x*3, dtype='uint8').reshape(y,x,3)
    if color is not None:
        background[:] = colors.get(color)
    else:
        background[:] = random.choice(list(colors.values()))
    #print('background ', background.shape)
    img = overlay_transparent(background, img, 0, 0,(x,y))
    return img

def extract_punk(index):
    """Extracts a single Punk from the sprite sheet and resizes it to 32x32."""
    x, y = get_punk_coords(index)
    punk = all_img[y:y + PUNK_SIZE, x:x + PUNK_SIZE]

    # Convert to PIL format and resize to 32x32
    punk = cv2.cvtColor(punk, cv2.COLOR_BGRA2RGBA)
    punk = cp_backg(punk)
    punk = Image.fromarray(punk).resize((MATRIX_SIZE, MATRIX_SIZE), Image.NEAREST)
    return punk


# Load initial 3 punks
punks = [extract_punk(punk_queue[0]), extract_punk(punk_queue[1]), extract_punk(punk_queue[2])]
x=0

while True:
    x +=1
    # Create an empty frame to assemble the scrolled image
    frame = Image.new("RGBA", (MATRIX_SIZE * 3, MATRIX_SIZE))
    # Paste the punks in their respective positions
    frame.paste(punks[0], (scroll_x + MATRIX_SIZE * 2, 0))
    frame.paste(punks[1], (scroll_x + MATRIX_SIZE, 0))
    frame.paste(punks[2], (scroll_x, 0))
    # Crop to only the center 
    cropped = frame.crop((MATRIX_SIZE, 0, MATRIX_SIZE * 2, MATRIX_SIZE))
    # Send image to LED matrix
    matrix.SetImage(cropped.convert("RGB"))

    # Move left
    scroll_x += 2

    # If the leftmost punk is completely out of frame, shift the queue
    if scroll_x >= MATRIX_SIZE :
        # Remove leftmost punk, shift others left, and generate a new right punk
        punk_queue.pop(0)
        punk_queue.append(random.randint(0, 9999))

        punks[0] = punks[1]
        punks[1] = punks[2]
        punks[2] = extract_punk(punk_queue[2])

        # Reset scroll_x to keep smooth transition
        scroll_x -= MATRIX_SIZE 

    # Control the scrolling speed
    time.sleep(SCROLL_SPEED)
