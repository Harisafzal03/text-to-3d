import os
from text_to_3d.text_processor.text_understanding import TextUnderstanding
from text_to_3d.layout_generator.layout_model import LayoutGenerator
from text_to_3d.model_generator.model_builder import ModelBuilder

class TextTo3DPipeline:
    def __init__(self):
        """Initialize the full text-to-3D pipeline."""
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
        # Initialize components
        print("Initializing pipeline components...")
        self.text_processor = TextUnderstanding()
        self.layout_generator = LayoutGenerator()
        self.model_builder = ModelBuilder()
        print("Pipeline ready!")
    
    def generate(self, text_description, output_file=None):
        """Process a text description and generate a 3D model.
        
        Args:
            text_description (str): Text describing the desired layout/model
            output_file (str, optional): Path to save the generated 3D model
            
        Returns:
            tuple: (text_features, layout, model) - the outputs from each stage
        """
        if not output_file:
            output_file = "output/model.obj"
        
        print(f"\n{'='*60}")
        print(f"Processing text: '{text_description}'")
        print(f"{'='*60}\n")
        
        # Step 1: Process text to extract features
        print("\n📝 Step 1: Processing text...")
        text_features = self.text_processor.extract_features(text_description)
        print(f"✓ Detected {len(text_features.get('rooms', []))} rooms")
        print(f"✓ Identified styles: {text_features.get('styles', [])}")
        
        # Step 2: Generate 2D layout from text features
        print("\n🏠 Step 2: Generating 2D layout...")
        layout = self.layout_generator.generate_layout(text_features)
        print(f"✓ Created layout with {len(layout.get('rooms', []))} rooms")
        print(f"✓ Generated {len(layout.get('connections', []))} connections between rooms")
        
        # Step 3: Convert 2D layout to 3D model
        print("\n🏗️ Step 3: Building 3D model...")
        model = self.model_builder.generate_3d_model(layout)
        print(f"✓ Created 3D model with {len(model['vertices'])} vertices")
        print(f"✓ Generated {len(model['faces'])} faces")
        
        # Export the model
        print("\n💾 Exporting model...")
        self.model_builder.export_obj(model, output_file)
        print(f"✓ Model exported to: {output_file}")
        
        # Display paths to visualizations
        print("\n🖼️ Visualizations:")
        if "visualization_path" in layout:
            print(f"✓ 2D Layout: {layout['visualization_path']}")
        if "visualization_path" in model:
            print(f"✓ 3D Model preview: {model['visualization_path']}")
        
        print(f"\n{'='*60}")
        print("Generation complete!")
        print(f"{'='*60}\n")
        
        return text_features, layout, model