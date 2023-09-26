from PIL import Image

def resize_png(input_file, output_file, scale_factor=1.2):
    try:
        # Open the original PNG file
        original_image = Image.open(input_file)

        # Calculate the new size
        new_width = int(original_image.width * scale_factor)
        new_height = int(original_image.height * scale_factor)

        # Create a new transparent image with the same size
        new_image = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

        # Paste the resized image onto the new transparent image
        new_image.paste(original_image, (0, 0))

        # Save the new transparent image as the output file
        new_image.save(output_file, format="PNG")

        print(f"Resized and saved as {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_file = "kanji.png"
    output_file = "kanji_resized.png"
    resize_png(input_file, output_file)

