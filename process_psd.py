import os
from PIL import Image, ImageDraw
from psd_tools import PSDImage
from psd_tools.api.layers import TypeLayer, SmartObjectLayer, Group

# --- Configuration ---
PSD_FILE = './psd/test.psd'
TEXT1_FILE = './text/1.txt'
TEXT2_FILE = './text/2.txt'
IMAGE_FILE = 'sample_image.jpg'
OUTPUT_PDF = 'test.pdf'
OUTPUT_PNG = 'test.png' # Also save a PNG for easier inspection

def get_group(layers, name):
    """Find a group by name."""
    for layer in layers:
        if layer.name == name and layer.is_group():
            return layer
        if layer.is_group():
            found = get_group(layer, name)
            if found:
                return found
    return None

def main():
    """
    Main function to process the PSD file.
    """
    # Check if the PSD file is a placeholder.
    # If so, print a message and create a dummy PDF to avoid errors in the workflow.
    with open(PSD_FILE, 'r') as f:
        content = f.read()
        if "This is a placeholder" in content:
            print("="*50)
            print("WARNING: The file 'psd/test.psd' is a placeholder.")
            print("This script requires a real PSD file to work.")
            print("Please replace 'psd/test.psd' with your template.")
            print("Creating a dummy PDF file for demonstration purposes.")
            print("="*50)
            dummy_img = Image.new('RGB', (600, 400), color = 'red')
            draw = ImageDraw.Draw(dummy_img)
            draw.text((10, 10), "This is a dummy PDF because test.psd is a placeholder.", fill='white')
            dummy_img.save(OUTPUT_PDF, "PDF" ,resolution=100.0)
            return

    # 1. Read input text files
    try:
        with open(TEXT1_FILE, 'r', encoding='utf-8') as f:
            text1 = f.read().strip()
        with open(TEXT2_FILE, 'r', encoding='utf-8') as f:
            text2 = f.read().strip()
    except FileNotFoundError as e:
        print(f"Error: Could not read text files. {e}")
        return

    # 2. Load the user-provided image
    try:
        user_image = Image.open(IMAGE_FILE)
    except FileNotFoundError:
        print(f"Error: Image file '{IMAGE_FILE}' not found.")
        return

    # 3. Load the PSD file
    print(f"Loading PSD file: {PSD_FILE}")
    psd = PSDImage.open(PSD_FILE)

    # 4. --- Modify Text Layers ---
    # Find the text layers named '文字1' and '文字2'.
    # The search is done within the '改文本' group inside the '模板' group.
    print("Searching for text layers...")
    template_group = get_group(psd, '模板')
    if template_group:
        text_group = get_group(template_group, '改文本')
        if text_group:
            text_layer_1 = next((l for l in text_group if l.name == '文字1'), None)
            text_layer_2 = next((l for l in text_group if l.name == '文字2'), None)

            if text_layer_1 and isinstance(text_layer_1, TypeLayer):
                print("Updating text for layer '文字1'")
                text_layer_1.text = text1
            else:
                print("Warning: Text layer '文字1' not found or not a text layer.")

            if text_layer_2 and isinstance(text_layer_2, TypeLayer):
                print("Updating text for layer '文字2'")
                text_layer_2.text = text2
            else:
                print("Warning: Text layer '文字2' not found or not a text layer.")
        else:
            print("Warning: Group '改文本' not found inside '模板'.")
    else:
        print("Warning: Group '模板' not found.")


    # 5. --- Modify Image Layers ---
    # The user described "white circles" where images should be placed.
    # For robust templates, these are often Smart Objects.
    # This script ASSUMES that the layers inside the '改图' group are Smart Objects.
    print("\nSearching for image placeholder layers (Smart Objects)...")
    if template_group:
        image_group = get_group(template_group, '改图')
        if image_group:
            print(f"Found image container group: '{image_group.name}'.")
            for layer in image_group:
                if isinstance(layer, SmartObjectLayer):
                    print(f"  - Replacing content of Smart Object: '{layer.name}'")
                    # The `replace` method modifies the smart object in memory.
                    # The `compose` function will then use this modified data.
                    layer.smart_object.replace(user_image)
                    # NOTE: This implementation replaces every found smart object
                    # with the same user image. It also does not perform the complex
                    # resizing requested ("shortest side >= diameter") as that would
                    # require changing the layer's transform matrix, which is not
                    # supported. The image will be scaled according to the existing
                    # smart object's transform.
        else:
            print("Warning: Group '改图' not found inside '模板'.")


    # 6. --- Compose and Save ---
    print("\nComposing the final image from the modified PSD structure...")
    # The compose() method generates a PIL Image from the PSD structure.
    # If we have modified layers (like text or smart objects) in memory,
    # it will use the updated data.
    final_image = psd.compose()

    # 7. Save the output
    print(f"Saving final image to {OUTPUT_PNG}")
    final_image.save(OUTPUT_PNG)

    print(f"Saving final PDF to {OUTPUT_PDF}")
    # To save as PDF, it's best to ensure it's in RGB mode.
    if final_image.mode == 'RGBA':
        final_image = final_image.convert('RGB')
    final_image.save(OUTPUT_PDF, "PDF", resolution=100.0)

    print("\nProcessing complete.")


if __name__ == '__main__':
    main()
