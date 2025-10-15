#!/usr/bin/env python3
"""
Resize cover art to meet podcast platform requirements.
Apple Podcasts requires 1400x1400 to 3000x3000 pixels.
"""

from PIL import Image
import os

def resize_cover_art(input_path, output_path, target_size=(1400, 1400)):
    """
    Resize cover art to meet podcast platform requirements
    
    Args:
        input_path: Path to the original image
        output_path: Path where resized image will be saved
        target_size: Target dimensions (width, height) - default 1400x1400
    """
    try:
        # Open the original image
        with Image.open(input_path) as img:
            print(f"Original image size: {img.size}")
            print(f"Original image format: {img.format}")
            print(f"Original image mode: {img.mode}")
            
            # Convert to RGB if necessary (for JPEG output)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Resize using high-quality resampling
            # LANCZOS provides good quality for upscaling
            resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save with high quality
            resized_img.save(output_path, "JPEG", quality=95, optimize=True)
            
            print(f"✅ Resized image saved: {output_path}")
            print(f"New size: {resized_img.size}")
            
            # Verify file size
            file_size = os.path.getsize(output_path)
            print(f"File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            return True
            
    except Exception as e:
        print(f"❌ Error resizing image: {e}")
        return False

if __name__ == "__main__":
    input_file = "hackerpulse_img.jpg"
    output_file = "hackerpulse_img_1400x1400.jpg"
    
    if os.path.exists(input_file):
        success = resize_cover_art(input_file, output_file)
        if success:
            print(f"\n🎉 Cover art successfully resized for podcast platforms!")
            print(f"You can now use {output_file} as your podcast cover art.")
        else:
            print("\n❌ Failed to resize cover art.")
    else:
        print(f"❌ Input file not found: {input_file}")