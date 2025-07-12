# Text to 3D Model Generator

This project converts natural language descriptions into 3D models through a two-step process:
1. Converting text descriptions to 2D layouts
2. Transforming 2D layouts to 3D models

## Installation

1. Clone the repository:
```bash
git clone https://github.com/username/text-to-3d.git
cd text-to-3d
```

2. Install the package and dependencies:
```bash
pip install -e .
```

## Quick Start

The easiest way to use this tool is with the provided shell script:

```bash
./generate_3d.sh "A modern house with a kitchen, living room, and two bedrooms"
```

This will:
1. Process your text description
2. Generate a 2D layout
3. Create a 3D model
4. Save visualizations and the model in the `output/` directory

## Examples

Here are some example descriptions you can try:

- "A small apartment with a kitchen, bathroom, and bedroom"
- "A modern office with three meeting rooms and an open workspace"
- "A two-story house with four bedrooms, three bathrooms, and a garage"

## How It Works

The system works in three stages:

1. **Text Understanding**: Using NLP to extract room types, relationships, dimensions, and styles.
2. **Layout Generation**: Creating a 2D floor plan based on the extracted information.
3. **3D Model Generation**: Converting the 2D layout into a 3D model with walls, floors, and basic structure.

## Output Files

The tool generates several output files in the `output/` directory:
- `layout.png`: A visualization of the 2D layout
- `3d_model.png`: A preview of the 3D model
- `model_TIMESTAMP.obj`: The 3D model in OBJ format (can be opened with Blender, etc.)

## Requirements

- Python 3.8+
- PyTorch
- Transformers (Hugging Face)
- NumPy
- Matplotlib
- NLTK

## Limitations

This is a prototype system with the following limitations:
- Basic room shapes (rectangular only)
- Limited understanding of complex architectural terms
- Simple 3D representation (walls and floors only)
- No textures or detailed furnishings

## Advanced Usage

For more control, you can use the Python API directly:

```python
from text_to_3d.pipeline import TextTo3DPipeline

# Initialize the pipeline
pipeline = TextTo3DPipeline()

# Generate a 3D model from text
description = "A modern house with a large kitchen, living room, and three bedrooms"
text_features, layout, model = pipeline.generate(description, output_file="house.obj")
```