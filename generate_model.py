#!/usr/bin/env python3
"""
Text to 3D Model Generator
--------------------------
This script takes a text description and generates a 3D model based on it.

Usage:
    python generate_model.py "A house with a kitchen and two bedrooms"

Output will be saved in the output/ directory.
"""

import sys
import os
import time
from text_to_3d.pipeline import TextTo3DPipeline

def main():
    # Check if a description is provided
    if len(sys.argv) < 2:
        print("Please provide a text description of the model you want to generate.")
        print("Usage: python generate_model.py \"A house with a kitchen and two bedrooms\"")
        return 1
    
    # Join all arguments to form the description
    description = ' '.join(sys.argv[1:])
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Output filenames
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base_filename = f"model_{timestamp}"
    obj_file = f"output/{base_filename}.obj"
    glb_file = f"output/{base_filename}.glb"
    
    # Initialize the pipeline and generate the model
    print(f"Generating 3D model from text: '{description}'")
    pipeline = TextTo3DPipeline()
    
    start_time = time.time()
    text_features, layout, model = pipeline.generate(description, obj_file)
    end_time = time.time()
    
    print(f"\nProcessing completed in {end_time - start_time:.2f} seconds")
    print("\nSummary:")
    print(f"- Input text: '{description}'")
    print(f"- Detected rooms: {[room['type'] for room in text_features.get('rooms', [])]}")
    print(f"- OBJ model: {obj_file}")
    print(f"- GLB model: {glb_file} (for 3D viewers)")
    print(f"- 2D layout visualization: {layout.get('visualization_path', 'N/A')}")
    print(f"- 3D model visualization: {model.get('visualization_path', 'N/A')}")
    
    print("\nTo view the 3D model:")
    print("1. Use any 3D model viewer that supports GLB format")
    print("2. Online options: https://gltf-viewer.donmccurdy.com/ or https://3dviewer.net/")
    print("3. Desktop options: Blender, Windows 3D Viewer, or any 3D modeling software")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())