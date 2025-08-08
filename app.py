# app.py
# This script creates a Streamlit web application to automate the generation of athlete profile images.
# It simulates the face detection and cropping process described in the provided technical brief.
# The app handles file uploads, processes the images, and provides a downloadable ZIP file of the results.

import streamlit as st
from PIL import Image
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

# --- Core Image Processing Logic (Simulated) ---

def simulate_face_crop(image, target_size):
    """
    Simulates cropping an image to a target size.
    A real implementation would use a face detection model.
    """
    width, height = image.size
    
    # Crop a square from the center of the original image
    min_dim = min(width, height)
    left = (width - min_dim) / 2
    top = (height - min_dim) / 2
    right = (width + min_dim) / 2
    bottom = (height + min_dim) / 2
    
    cropped_image = image.crop((left, top, right, bottom))
    
    # Resize to the target size while maintaining aspect ratio
    cropped_image.thumbnail((target_size, target_size), Image.LANCZOS)
    
    return cropped_image


def process_image(uploaded_file, size_spec):
    """
    Processes a single uploaded image file to a single specified size.
    """
    try:
        # Open the image using Pillow (PIL)
        image = Image.open(uploaded_file)
        
        # Ensure image is in RGBA format for transparency
        image = image.convert("RGBA")

        # Get the original filename without the suffix
        original_filename, _ = os.path.splitext(uploaded_file.name)

        width = size_spec["width"]
        height = size_spec["height"]
        
        if size_spec["type"] == "avatar":
            processed_image = simulate_face_crop(image, min(width, height))
            processed_image = processed_image.resize((width, height), Image.LANCZOS)
        else:
            processed_image = image.resize((width, height), Image.LANCZOS)

        # Create a new image with a transparent background
        bg = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bg.paste(processed_image, (0, 0), processed_image)
        
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
    st.write("Drag and drop front and side profile images below.")

    col1, col2 = st.columns(2)

    front_profile_file = None
    side_profile_file = None
    with col1:
        front_profile_file = st.file_uploader(
            "Upload Front Profile Image",
            type=["tif", "tiff", "jpg", "jpeg", "png"],
            key="front_profile"
        )
    with col2:
        side_profile_file = st.file_uploader(
            "Upload Side Profile Image",
            type=["tif", "tiff", "jpg", "jpeg", "png"],
            key="side_profile"
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

    if st.button("Generate Images", type="primary", use_container_width=True):
        if not front_profile_file and not side_profile_file:
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
                        uploaded_files = [file for file in [front_profile_file, side_profile_file] if file is not None]
                        
                        for uploaded_file in uploaded_files:
                            st.info(f"Processing image: {uploaded_file.name}")
                            for size_spec in selected_sizes:
                                generated_image = process_image(uploaded_file, size_spec)
                                if generated_image:
                                    all_generated_images.append(generated_image)

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
                        else:
                            st.error("No images were generated. Please check your uploads and selections.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# This ensures the main function runs when the script is executed
if __name__ == "__main__":
    main()
