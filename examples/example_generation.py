import os
import sys
import time
from text_to_3d.pipeline import TextTo3DPipeline

def main():
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    pipeline = TextTo3DPipeline()
    
    # Example text descriptions
    examples = [
        "A small house with a kitchen, living room, and two bedrooms.",
        "An open concept apartment with a kitchen island, dining area and living room.",
        "A modern office with three meeting rooms, an open workspace, and a kitchen area."
    ]
    
    # Check if a description is provided via command line
    if len(sys.argv) > 1:
        # Join all arguments to form the description
        custom_description = ' '.join(sys.argv[1:])
        print(f"Using custom description: '{custom_description}'")
        
        # Generate model
        output_file = f"output/custom_model.obj"
        start_time = time.time()
        text_features, layout, model = pipeline.generate(custom_description, output_file)
        end_time = time.time()
        
        print(f"\nProcessing completed in {end_time - start_time:.2f} seconds")
        return
    
    # Process each example
    for i, text in enumerate(examples):
        print(f"\n\nExample {i+1}: '{text}'")
        
        # Generate model
        output_file = f"output/example_{i+1}.obj"
        text_features, layout, model = pipeline.generate(text, output_file)

if __name__ == "__main__":
    main()