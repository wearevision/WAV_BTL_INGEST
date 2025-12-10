
import os
from PIL import Image, ExifTags
from pipeline.image_enhancer import enhance_image
from pipeline.media_processor import convert_to_webp

def create_rotated_image(path):
    # Create a 100x50 image (landscape)
    img = Image.new('RGB', (100, 50), color='red')
    
    # Find the orientation tag ID
    orientation_key = None
    for key, value in ExifTags.TAGS.items():
        if value == 'Orientation':
            orientation_key = key
            break
            
    if orientation_key is None:
        raise RuntimeError("Could not find Orientation EXIF tag")

    # Set EXIF orientation to 6 (Rotate 90 CW). 
    # This means the image is stored as landscape but should be displayed as portrait (50x100).
    exif_data = img.getexif()
    exif_data[orientation_key] = 6
    
    img.save(path, exif=exif_data)
    print(f"Created test image at {path} with size {img.size} and Orientation=6")

def verify_fix():
    test_img_path = "test_orientation.jpg"
    enhanced_path = "test_enhanced.webp"
    converted_path = "test_converted_dir"
    
    try:
        create_rotated_image(test_img_path)
        
        # Test 1: enhance_image
        print("\nTesting enhance_image...")
        enhance_image(test_img_path, enhanced_path)
        
        with Image.open(enhanced_path) as img:
            print(f"Enhanced image size: {img.size}")
            # Should be 50x100 (portrait) because it was rotated
            if img.size == (50, 100):
                print("✅ enhance_image fixed orientation correctly!")
            else:
                print(f"❌ enhance_image failed! Expected (50, 100), got {img.size}")

        # Test 2: convert_to_webp
        print("\nTesting convert_to_webp...")
        convert_to_webp(test_img_path, converted_path)
        converted_file = os.path.join(converted_path, "test_orientation.webp")
        
        with Image.open(converted_file) as img:
            print(f"Converted image size: {img.size}")
            # Should be 50x100 (portrait)
            if img.size == (50, 100):
                print("✅ convert_to_webp fixed orientation correctly!")
            else:
                print(f"❌ convert_to_webp failed! Expected (50, 100), got {img.size}")

    finally:
        # Cleanup
        if os.path.exists(test_img_path):
            os.remove(test_img_path)
        if os.path.exists(enhanced_path):
            os.remove(enhanced_path)
        if os.path.exists(converted_path):
            import shutil
            shutil.rmtree(converted_path)

if __name__ == "__main__":
    verify_fix()
