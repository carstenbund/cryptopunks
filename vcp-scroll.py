#!/usr/bin/env python3

import cv2
import os
import time
import numpy as np
import random
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# LED Matrix Configuration
options = RGBMatrixOptions()
options.rows = 32
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'
options.gpio_slowdown = 4

matrix = RGBMatrix(options=options)

# Load the entire CryptoPunks image
img_name = "punks.png"
all_img = cv2.imread(img_name, cv2.IMREAD_UNCHANGED)

# Constants
PUNK_SIZE = 24  # Each Punk in the source sheet is 24x24
MATRIX_SIZE = 32  # Displayed Punk size on the LED matrix
PUNKS_PER_ROW = 100  # Number of punks per row in the sprite sheet
SCROLL_SPEED = 0.05  # Speed of scrolling (seconds per frame)

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


def extract_punk(index):
    """Extracts a single Punk from the sprite sheet and resizes it to 32x32."""
    x, y = get_punk_coords(index)
    punk = all_img[y:y + PUNK_SIZE, x:x + PUNK_SIZE]

    # Convert to PIL format and resize to 32x32
    punk = cv2.cvtColor(punk, cv2.COLOR_BGRA2RGBA)
    punk = Image.fromarray(punk).resize((MATRIX_SIZE, MATRIX_SIZE), Image.NEAREST)
    return punk


# Load initial 3 punks
punks = [extract_punk(punk_queue[0]), extract_punk(punk_queue[1]), extract_punk(punk_queue[2])]

while True:
    # Create an empty frame to assemble the scrolled image
    frame = Image.new("RGBA", (MATRIX_SIZE * 3, MATRIX_SIZE))

    # Paste the punks in their respective positions
    frame.paste(punks[0], (scroll_x - MATRIX_SIZE * 2, 0))
    frame.paste(punks[1], (scroll_x - MATRIX_SIZE, 0))
    frame.paste(punks[2], (scroll_x, 0))

    # Crop to only the center 32x32
    cropped = frame.crop((MATRIX_SIZE, 0, MATRIX_SIZE * 2, MATRIX_SIZE))

    # Send image to LED matrix
    matrix.SetImage(cropped.convert("RGB"))

    # Move left
    scroll_x -= 1

    # If the leftmost punk is completely out of frame, shift the queue
    if scroll_x <= -MATRIX_SIZE * 2:
        # Remove leftmost punk, shift others left, and generate a new right punk
        punk_queue.pop(0)
        punk_queue.append(random.randint(0, 9999))

        punks[0] = punks[1]
        punks[1] = punks[2]
        punks[2] = extract_punk(punk_queue[2])

        # Reset scroll_x to keep smooth transition
        scroll_x += MATRIX_SIZE

    # Control the scrolling speed
    time.sleep(SCROLL_SPEED)
