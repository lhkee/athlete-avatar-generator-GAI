# app.py
# This script creates a Streamlit web application to automate the generation of athlete profile images.
# This version features improved cropping logic to prevent distortion and a more visible guideline overlay.

import streamlit as st
from PIL import Image, ImageDraw
import io
import zipfile
import os

# Define the output specifications based on the tech brief
OUTPUT_SPECS = {
    "avatar": {
        "title": "Avatar Exports",
        "sizes": [
            {"width": 256, "height": 256, "type": "avatar"},
            {"width": 500, "height": 345, "type": "avatar"}
        ]
    },
    "hero": {
        "title": "Hero Exports",
        "sizes": [
            {"width": 1200, "height": 1165, "type": "hero"},
            {"width": 1500, "height": 920, "type": "hero"}
        ]
    }
}

# --- Core Image Processing Logic ---

def crop_to_aspect_ratio_tighter(image, target_aspect):
    """
    Crops the image to a target aspect ratio with a tighter, top-focused frame
    for head-and-shoulders shots without distortion.
    """
    img_width, img_height = image.size
    
    # Calculate the new crop dimensions based on the target aspect ratio
    if img_width / img_height > target_aspect:
        # If the original image is wider, the new crop width is based on height.
        new_width = int(img_height * target_aspect)
        new_height = img_height
    else:
        # If the original image is taller, the new crop height is based on width.
        new_width = img_width
        new_height = int(img_width / target_aspect)
        
    # Center the crop horizontally but keep the top of the image (head)
    left = (img_width - new_width) / 2
    top = 0
    right = left + new_width
    bottom = top + new_height
    
    return image.crop((left, top, right, bottom))


def create_guideline_image(width, height):
    """Generates a transparent guideline image with a more visible dashed border."""
    guideline = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(guideline)
    # Draw a thicker, more visible yellow dashed border
    line_color = (255, 255, 0, 200) # Semi-transparent yellow for visibility
    line_width = 4
    dash_length = 20
    for i in range(0, width, dash_length * 2):
        draw.line((i, 0, i + dash_length, 0), fill=line_color, width=line_width)
        draw.line((i, height-1, i + dash_length, height-1), fill=line_color, width=line_width)
    for i in range(0, height, dash_length * 2):
        draw.line((0, i, 0, i + dash_length), fill=line_color, width=line_width)
        draw.line((width-1, i, width-1, i + dash_length), fill=line_color, width=line_width)
    return guideline

def create_hero_guideline_image(width, height):
    """Generates a guideline for hero images with a centered horizontal line."""
    guideline = create_guideline_image(width, height)
    draw = ImageDraw.Draw(guideline)
    # Add a more prominent horizontal line for the shoulders based on reference
    shoulder_height = int(height * 0.4) 
    draw.line((0, shoulder_height, width, shoulder_height), fill=(255, 255, 0, 200), width=6)
    return guideline

def process_image(uploaded_file, size_spec, add_guideline=False):
    """
    Processes a single uploaded image file to a single specified size,
    maintaining aspect ratio and optionally adding a guideline overlay.
    """
    try:
        # Open the image using Pillow (PIL)
        image = Image.open(uploaded_file)
        image = image.convert("RGBA")

        original_filename, _ = os.path.splitext(uploaded_file.name)
        width = size_spec["width"]
        height = size_spec["height"]
        
        # Calculate target aspect ratio
        target_aspect = width / height

        # Crop the image to match the target aspect ratio without distortion
        cropped_image = crop_to_aspect_ratio_tighter(image, target_aspect)

        # Resize the cropped image to the final dimensions
        processed_image = cropped_image.resize((width, height), Image.LANCZOS)

        # Create a new image with a transparent background
        bg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bg.paste(processed_image, (0, 0), processed_image)
        
        # Add guideline overlay for previews if requested
        if add_guideline:
            if size_spec["type"] == "hero":
                guideline_overlay = create_hero_guideline_image(width, height)
            else:
                guideline_overlay = create_guideline_image(width, height)
            bg.paste(guideline_overlay, (0, 0), guideline_overlay)
        
        filename = f"{original_filename}-{size_spec['type']}_{width}x{height}.png"
        
        buffer = io.BytesIO()
        bg.save(buffer, format="PNG")
        buffer.seek(0)
        
        return {"name": filename, "data": buffer}

    except Exception as e:
        st.error(f"Error processing {uploaded_file.name} for size {width}x{height}: {e}")
        return None

# --- Streamlit UI ---

def main():
    """
    Main function to run the Streamlit app.
    """
    st.set_page_config(page_title="Athlete Image Generator", layout="centered")

    st.markdown(
        """
        <div style="text-align: center; font-family: Inter, sans-serif;">
            <h1 style="color: #1a1a1a; margin-bottom: 0;">Athlete Image Generator</h1>
            <p style="color: #555; margin-top: 5px;">Automate and streamline the creation of standardized athlete profile images.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.subheader("1. Upload Images")
    st.write("Drag and drop your athlete images below. You can upload multiple files at once.")

    uploaded_files = st.file_uploader(
        "Upload Images",
        type=["tif", "tiff", "jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    st.markdown("---")

    st.subheader("2. Select Output Sizes")
    st.write("Choose the image sizes you need. All outputs will have a transparent background.")

    st.markdown("##### Avatar Exports")
    col_avatar_1, col_avatar_2 = st.columns(2)
    with col_avatar_1:
        st.checkbox("256x256 px", value=True, key="avatar_256")
    with col_avatar_2:
        st.checkbox("500x345 px", value=True, key="avatar_500")

    st.markdown("##### Hero Exports")
    col_hero_1, col_hero_2 = st.columns(2)
    with col_hero_1:
        st.checkbox("1200x1165 px", value=True, key="hero_1200")
    with col_hero_2:
        st.checkbox("1500x920 px", value=True, key="hero_1500")

    st.markdown("---")
    st.checkbox("Show guideline overlay on previews", key="show_guideline")

    if st.button("Generate Images", type="primary", use_container_width=True):
        if not uploaded_files:
            st.warning("Please upload at least one image to begin.")
        else:
            try:
                selected_sizes = []
                if st.session_state.get("avatar_256"):
                    selected_sizes.append(OUTPUT_SPECS["avatar"]["sizes"][0])
                if st.session_state.get("avatar_500"):
                    selected_sizes.append(OUTPUT_SPECS["avatar"]["sizes"][1])
                if st.session_state.get("hero_1200"):
                    selected_sizes.append(OUTPUT_SPECS["hero"]["sizes"][0])
                if st.session_state.get("hero_1500"):
                    selected_sizes.append(OUTPUT_SPECS["hero"]["sizes"][1])
                
                if not selected_sizes:
                    st.warning("Please select at least one output size to generate.")
                else:
                    with st.spinner("Processing images..."):
                        all_generated_images = []
                        
                        show_guideline = st.session_state.get("show_guideline", False)
                        
                        for uploaded_file in uploaded_files:
                            st.info(f"Processing image: {uploaded_file.name}")
                            for size_spec in selected_sizes:
                                generated_image_info = process_image(uploaded_file, size_spec, show_guideline)
                                if generated_image_info:
                                    all_generated_images.append(generated_image_info)

                        if all_generated_images:
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                                for img in all_generated_images:
                                    zf.writestr(img["name"], img["data"].getvalue())

                            st.success("Images generated successfully! Download the ZIP below.")
                            st.download_button(
                                label="Download All Images (.zip)",
                                data=zip_buffer.getvalue(),
                                file_name="athlete_images.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                            
                            st.markdown("---")
                            st.subheader("3. Image Previews")
                            st.write("Here are the images generated from your uploads:")
                            
                            cols = st.columns(2)
                            for i, img in enumerate(all_generated_images):
                                with cols[i % 2]:
                                    st.image(img["data"], caption=img["name"], use_container_width=True)
                        else:
                            st.error("No images were generated. Please check your uploads and selections.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# This ensures the main function runs when the script is executed
if __name__ == "__main__":
    main()
