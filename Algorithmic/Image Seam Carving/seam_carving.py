"""Seam carving algorithm for content-aware image resizing.

This module implements the seam carving algorithm which resizes images
by intelligently removing or adding seams (paths of least importance)
rather than scaling uniformly. Uses dynamic programming to find optimal seams.
"""

import numpy as np
from PIL import Image


def calculate_energy(
    img_array: np.ndarray, gray: np.ndarray | None = None
) -> np.ndarray:
    """
    Calculates the energy map of the image using the dual-gradient energy function.

    Args:
        img_array: A 3D numpy array of shape (H, W, 3) or (H, W).
        gray: Optional pre-calculated grayscale image of shape (H, W).

    Returns:
        A 2D numpy array of shape (H, W) representing energy.
    """
    if gray is None:
        # Convert to grayscale for simpler gradient calculation if it's color
        if len(img_array.shape) == 3:
            # Standard luminosity weights: 0.299 R + 0.587 G + 0.114 B
            # Use float32 to save memory bandwidth during updates
            gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
        else:
            gray = img_array.astype(np.float32)

    # Gradients using simple difference
    # dy: (x, y+1) - (x, y-1)
    # dx: (x+1, y) - (x-1, y)

    # Manual gradient calculation is faster than np.gradient
    rows, cols = gray.shape

    # Calculate dx directly into energy buffer to save memory
    energy = np.empty((rows, cols), dtype=gray.dtype)

    # Interior: |I(x+1, y) - I(x-1, y)|
    energy[:, 1:-1] = gray[:, 2:] - gray[:, :-2]
    # Boundaries: 2 * |I(1, y) - I(0, y)| to match scale of interior
    energy[:, 0] = 2 * (gray[:, 1] - gray[:, 0])
    energy[:, -1] = 2 * (gray[:, -1] - gray[:, -2])

    # Absolute value in-place
    np.abs(energy, out=energy)

    # Calculate dy
    dy = np.empty((rows, cols), dtype=gray.dtype)
    # Interior: |I(x, y+1) - I(x, y-1)|
    dy[1:-1, :] = gray[2:, :] - gray[:-2, :]
    # Boundaries
    dy[0, :] = 2 * (gray[1, :] - gray[0, :])
    dy[-1, :] = 2 * (gray[-1, :] - gray[-2, :])

    # Add dy contribution
    energy += np.abs(dy)
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
    # Optimization: Pad once outside the loop to avoid O(H) allocations of size W
    # Note: astype(float) converts to float64, which is safer for accumulation
    dp = np.pad(
        energy.astype(float),
        ((0, 0), (1, 1)),
        mode="constant",
        constant_values=np.inf,
    )

    # backtrack[i][j] stores the offset (-1, 0, 1) from the previous row
    backtrack = np.zeros((rows, cols), dtype=int)

    for r in range(1, rows):
        # Vectorized implementation for speed
        # Previous row values from padded dp array
        prev_row = dp[r - 1]

        # Valid columns are 1..cols
        # left neighbor for col j (in 1..cols) is prev_row[j-1]
        # up neighbor for col j is prev_row[j]
        # right neighbor for col j is prev_row[j+1]

        left = prev_row[:-2]
        up = prev_row[1:-1]
        right = prev_row[2:]

        # Find min of (left, up, right) for each column
        # Optimization: Avoid np.stack and np.argmin to reduce allocations
        # Compute min values directly
        # Break down minimum calc to re-use intermediate result for mask calculation
        min_ur = np.minimum(up, right)
        min_values = np.minimum(left, min_ur)

        # Determine offsets (-1 for left, 0 for up, 1 for right)
        # Optimized boolean arithmetic to avoid expensive np.where calls
        # We use .view(np.int8) on boolean arrays to avoid allocation during casting
        m_left = left == min_values
        m_up = (up == min_values) & (~m_left)

        # Logic:
        # If m_left is True: 1 - 2(1) - 0 = -1
        # If m_up is True:   1 - 0 - 1 = 0
        # If neither (right is min): 1 - 0 - 0 = 1
        offset = 1 - 2 * m_left.view(np.int8) - m_up.view(np.int8)

        # Update dp table (valid region only)
        dp[r, 1 : cols + 1] += min_values
        backtrack[r] = offset

    # Backtrack from the bottom
    seam = np.zeros(rows, dtype=int)

    # Find the bottom pixel with min cumulative energy
    # We look at the valid region 1..cols+1
    min_col = np.argmin(dp[-1, 1 : cols + 1])
    seam[-1] = min_col

    for r in range(rows - 2, -1, -1):
        prev_col = seam[r + 1]
        offset = backtrack[r + 1, prev_col]
        seam[r] = prev_col + offset

        # Boundary check (should be handled by the logic above, but good for safety)
        # Optimization: Use native Python min/max instead of np.clip for scalar
        seam[r] = max(0, min(seam[r], cols - 1))

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

    if channels == 1 and img_array.ndim == 2:
        # Optimization for 2D arrays (like grayscale map):
        # Use np.delete on flattened array which is faster than boolean masking
        flat_indices = np.arange(rows) * cols + seam
        return np.delete(img_array, flat_indices).reshape(rows, cols - 1)

    # For 3D arrays, boolean masking is still effective
    col_indices = np.arange(cols)
    mask = col_indices != seam[:, None]

    if channels > 1:
        # Reshape mask to (H, W, 1) to broadcast or apply per channel
        # Actually simplest is to just reshape the output
        new_img = img_array[mask].reshape(rows, cols - 1, channels)
    else:
        new_img = img_array[mask].reshape(rows, cols - 1)

    return new_img


def seam_carve(
    image: Image.Image, target_width: int, target_height: int, verbose: bool = False
) -> Image.Image:
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

    # Optimization: Calculate grayscale once and update it incrementally
    # to avoid expensive dot product in every iteration.
    # Use float32 to reduce memory bandwidth requirements.
    if len(img_array.shape) == 3:
        gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
    else:
        gray = img_array.astype(np.float32)

    for i in range(delta_w):
        if verbose and i % 10 == 0:
            print(f"Removing vertical seam {i+1}/{delta_w}")

        energy = calculate_energy(img_array, gray=gray)
        seam = find_vertical_seam(energy)
        img_array = remove_vertical_seam(img_array, seam)
        gray = remove_vertical_seam(gray, seam)

    # Handle height reduction
    # To remove horizontal seams, we can rotate the image 90 degrees,
    # remove vertical seams, and rotate back.
    current_h = img_array.shape[0]
    delta_h = current_h - target_height

    if delta_h < 0:
        raise NotImplementedError("Upscaling (seam insertion) not implemented yet.")

    if delta_h > 0:
        img_array = (
            np.transpose(img_array, (1, 0, 2))
            if len(img_array.shape) == 3
            else np.transpose(img_array)
        )

        # Re-calculate grayscale for the rotated image
        if len(img_array.shape) == 3:
            gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
        else:
            gray = img_array.astype(np.float32)

        for i in range(delta_h):
            if verbose and i % 10 == 0:
                print(f"Removing horizontal seam {i+1}/{delta_h}")

            energy = calculate_energy(img_array, gray=gray)
            seam = find_vertical_seam(energy)
            img_array = remove_vertical_seam(img_array, seam)
            gray = remove_vertical_seam(gray, seam)

        img_array = (
            np.transpose(img_array, (1, 0, 2))
            if len(img_array.shape) == 3
            else np.transpose(img_array)
        )

    return Image.fromarray(img_array.astype(np.uint8))
