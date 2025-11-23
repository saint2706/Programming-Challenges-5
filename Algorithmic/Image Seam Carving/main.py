import argparse
import sys
import os
from PIL import Image
from seam_carving import seam_carve

def main():
    parser = argparse.ArgumentParser(description="Resize an image using Seam Carving.")
    parser.add_argument("input_image", help="Path to the input image")
    parser.add_argument("output_image", help="Path to save the output image")
    parser.add_argument("--width", type=int, help="Target width (optional, defaults to original)")
    parser.add_argument("--height", type=int, help="Target height (optional, defaults to original)")
    parser.add_argument("--scale", type=float, help="Scale factor (e.g., 0.5 for half size). Overrides width/height.")
    parser.add_argument("--verbose", action="store_true", help="Show progress")

    args = parser.parse_args()

    if not os.path.exists(args.input_image):
        print(f"Error: Input file '{args.input_image}' not found.")
        sys.exit(1)

    try:
        image = Image.open(args.input_image)
    except Exception as e:
        print(f"Error opening image: {e}")
        sys.exit(1)

    original_width, original_height = image.size
    target_width = original_width
    target_height = original_height

    if args.scale:
        target_width = int(original_width * args.scale)
        target_height = int(original_height * args.scale)
    else:
        if args.width:
            target_width = args.width
        if args.height:
            target_height = args.height

    if target_width > original_width or target_height > original_height:
         print("Error: This implementation only supports downscaling.")
         sys.exit(1)

    print(f"Resizing from {original_width}x{original_height} to {target_width}x{target_height}...")

    try:
        resized_image = seam_carve(image, target_width, target_height, verbose=args.verbose)
        resized_image.save(args.output_image)
        print(f"Saved to {args.output_image}")
    except Exception as e:
        print(f"Error during seam carving: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
