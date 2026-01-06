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

    # Calculate dy contribution directly into energy to avoid allocating dy array
    # Interior: |I(x, y+1) - I(x, y-1)|
    energy[1:-1, :] += np.abs(gray[2:, :] - gray[:-2, :])
    # Boundaries
    energy[0, :] += np.abs(2 * (gray[1, :] - gray[0, :]))
    energy[-1, :] += np.abs(2 * (gray[-1, :] - gray[-2, :]))
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
    # Note: Using float32 (if energy is float32) is sufficient for precision and saves memory/bandwidth
    # Note: If energy is int (e.g. from tests), we must cast to float to support np.inf
    if not np.issubdtype(energy.dtype, np.floating):
        energy = energy.astype(float)

    dp = np.pad(
        energy,
        ((0, 0), (1, 1)),
        mode="constant",
        constant_values=np.inf,
    )

    # No backtrack array needed to save memory and allocation time.
    # We can reconstruct the path by looking at the DP table values during backtracking.

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
        min_ur = np.minimum(up, right)
        min_values = np.minimum(left, min_ur)

        # Update dp table (valid region only)
        dp[r, 1 : cols + 1] += min_values

    # Backtrack from the bottom
    seam = np.zeros(rows, dtype=int)

    # Find the bottom pixel with min cumulative energy
    # We look at the valid region 1..cols+1
    min_col = np.argmin(dp[-1, 1 : cols + 1])
    seam[-1] = min_col

    for r in range(rows - 2, -1, -1):
        prev_col = seam[r + 1]

        # Reconstruct path by looking at the 3 neighbors in the previous row
        # Padded index for prev_col is prev_col + 1
        # Neighbors are at padded indices: prev_col, prev_col+1, prev_col+2
        l_val = dp[r, prev_col]
        u_val = dp[r, prev_col + 1]
        r_val = dp[r, prev_col + 2]

        # Find which neighbor has the minimum value to determine offset
        # This replaces the lookup in the backtrack table
        if l_val <= u_val and l_val <= r_val:
            offset = -1
        elif u_val <= r_val:
            offset = 0
        else:
            offset = 1

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

    # For 3D arrays, we can also use np.delete on a flattened view
    # which avoids creating and applying a large boolean mask
    flat_indices = np.arange(rows) * cols + seam

    if channels > 1:
        # Reshape to (H*W, C) to delete rows corresponding to pixels
        flat_img = img_array.reshape(-1, channels)
        new_flat = np.delete(flat_img, flat_indices, axis=0)
        return new_flat.reshape(rows, cols - 1, channels)
    else:
        # Fallback for 3D array with 1 channel (rare but possible)
        # Treated same as 2D basically but preserving last dim
        flat_img = img_array.reshape(-1)
        new_flat = np.delete(flat_img, flat_indices)
        return new_flat.reshape(rows, cols - 1, 1)


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
