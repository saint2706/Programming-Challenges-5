"""Seam carving algorithm for content-aware image resizing.

This module implements the seam carving algorithm which resizes images
by intelligently removing or adding seams (paths of least importance)
rather than scaling uniformly. Uses dynamic programming to find optimal seams.
"""
import numpy as np
from PIL import Image
from typing import Tuple, Optional

def calculate_energy(img_array: np.ndarray) -> np.ndarray:
    """
    Calculates the energy map of the image using the dual-gradient energy function.

    Args:
        img_array: A 3D numpy array of shape (H, W, 3) or (H, W).

    Returns:
        A 2D numpy array of shape (H, W) representing energy.
    """
    # Convert to grayscale for simpler gradient calculation if it's color
    if len(img_array.shape) == 3:
        # Standard luminosity weights: 0.299 R + 0.587 G + 0.114 B
        gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114])
    else:
        gray = img_array

    # Gradients using simple difference
    # dy: (x, y+1) - (x, y-1)
    # dx: (x+1, y) - (x-1, y)

    # We use np.gradient for convenience which handles boundaries
    dy, dx = np.gradient(gray)

    energy = np.abs(dx) + np.abs(dy)
    return energy

def find_vertical_seam(energy: np.ndarray) -> np.ndarray:
    """
    Finds the vertical seam with the lowest cumulative energy.

    Args:
        energy: A 2D numpy array of shape (H, W).

    Returns:
        A 1D numpy array of length H containing the column index for each row.
    """
    rows, cols = energy.shape

    # dp[i][j] stores the minimum cumulative energy to reach pixel (i, j)
    # Ensure it's float to handle infinity
    dp = energy.astype(float)

    # backtrack[i][j] stores the offset (-1, 0, 1) from the previous row
    backtrack = np.zeros_like(dp, dtype=int)

    for r in range(1, rows):
        # Vectorized implementation for speed
        # Previous row values
        prev_row = dp[r-1]

        # Shifted versions for left, up, right neighbors
        up = prev_row
        left = np.roll(prev_row, 1)
        right = np.roll(prev_row, -1)

        # Handle boundaries: set invalid moves to infinity
        # Since 'left', 'up', 'right' come from prev_row which is float (energy),
        # they should be able to hold infinity.
        # However, if energy is somehow int, this would fail.
        # But calculate_energy returns abs(gradients) which are typically floats or can be cast.
        # Let's ensure choices are float.

        left[0] = np.inf
        right[-1] = np.inf

        # Find min of (left, up, right) for each column
        # This is a bit tricky to vectorize cleanly with argmin for 3 choices,
        # so we might do a column-wise loop or a stacked argmin.
        # Let's do a stacked argmin.

        choices = np.stack([left, up, right]) # Shape (3, W)
        min_indices = np.argmin(choices, axis=0) # Shape (W,), values 0, 1, 2 corresponding to left, up, right
        min_values = np.min(choices, axis=0)

        dp[r] += min_values
        backtrack[r] = min_indices - 1 # Convert 0,1,2 to -1,0,1

    # Backtrack from the bottom
    seam = np.zeros(rows, dtype=int)

    # Find the bottom pixel with min cumulative energy
    min_col = np.argmin(dp[-1])
    seam[-1] = min_col

    for r in range(rows - 2, -1, -1):
        prev_col = seam[r+1]
        offset = backtrack[r+1, prev_col]
        seam[r] = prev_col + offset

        # Boundary check (should be handled by the logic above, but good for safety)
        seam[r] = np.clip(seam[r], 0, cols - 1)

    return seam

def remove_vertical_seam(img_array: np.ndarray, seam: np.ndarray) -> np.ndarray:
    """
    Removes a vertical seam from the image.

    Args:
        img_array: (H, W, C) or (H, W) array.
        seam: (H,) array of column indices.

    Returns:
        New image array with width W-1.
    """
    rows, cols = img_array.shape[:2]
    channels = img_array.shape[2] if len(img_array.shape) == 3 else 1

    # Mask to keep pixels
    mask = np.ones((rows, cols), dtype=bool)

    # This is slow: for r in rows: mask[r, seam[r]] = False
    # Vectorized mask creation:
    col_indices = np.arange(cols)
    mask = col_indices != seam[:, None]

    if channels > 1:
        # Reshape mask to (H, W, 1) to broadcast or apply per channel
        # Actually simplest is to just reshape the output
        new_img = img_array[mask].reshape(rows, cols - 1, channels)
    else:
        new_img = img_array[mask].reshape(rows, cols - 1)

    return new_img

def seam_carve(image: Image.Image, target_width: int, target_height: int, verbose: bool = False) -> Image.Image:
    """
    Resizes an image using seam carving.

    Args:
        image: PIL Image object.
        target_width: Desired width.
        target_height: Desired height.
        verbose: Print progress.

    Returns:
        Resized PIL Image.
    """
    img_array = np.array(image)

    # Handle width reduction
    current_h, current_w = img_array.shape[:2]

    delta_w = current_w - target_width

    if delta_w < 0:
        raise NotImplementedError("Upscaling (seam insertion) not implemented yet.")

    for i in range(delta_w):
        if verbose and i % 10 == 0:
            print(f"Removing vertical seam {i+1}/{delta_w}")

        energy = calculate_energy(img_array)
        seam = find_vertical_seam(energy)
        img_array = remove_vertical_seam(img_array, seam)

    # Handle height reduction
    # To remove horizontal seams, we can rotate the image 90 degrees,
    # remove vertical seams, and rotate back.
    current_h = img_array.shape[0]
    delta_h = current_h - target_height

    if delta_h < 0:
        raise NotImplementedError("Upscaling (seam insertion) not implemented yet.")

    if delta_h > 0:
        img_array = np.transpose(img_array, (1, 0, 2)) if len(img_array.shape) == 3 else np.transpose(img_array)

        for i in range(delta_h):
            if verbose and i % 10 == 0:
                print(f"Removing horizontal seam {i+1}/{delta_h}")

            energy = calculate_energy(img_array)
            seam = find_vertical_seam(energy)
            img_array = remove_vertical_seam(img_array, seam)

        img_array = np.transpose(img_array, (1, 0, 2)) if len(img_array.shape) == 3 else np.transpose(img_array)

    return Image.fromarray(img_array.astype(np.uint8))
