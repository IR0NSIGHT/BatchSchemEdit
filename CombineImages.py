from PIL import Image
import math


def combine_images_grid(image_paths, images_per_row=3, bg_color=(255, 255, 255, 0)):
    """
    Combines images into a grid.

    Args:
        image_paths (list of str): paths to images.
        images_per_row (int): how many images per row.
        bg_color (tuple): background color RGBA (default transparent).

    Returns:
        PIL.Image: combined image.
    """

    images = [Image.open(p) for p in image_paths]

    # Find max width and height of all images to align grid cells
    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)

    num_images = len(images)
    rows = math.ceil(num_images / images_per_row)

    padding = 10

    combined_width = max_width * images_per_row + images_per_row * padding
    combined_height = max_height * rows + rows * padding

    combined_img = Image.new("RGBA", (combined_width, combined_height), bg_color)

    for index, img in enumerate(images):
        row = index // images_per_row
        col = index % images_per_row
        x = col * max_width + col * padding
        y = row * max_height + row * padding

        # Paste image at calculated position
        combined_img.paste(img, (x, y))

    return combined_img
