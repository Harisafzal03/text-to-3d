#!/bin/bash
# Robust 3D Model Generator with Reliable GLB Export
# Current Date: 2025-07-12 21:55:03
# User: Harisafzal03

# Display help message
show_help() {
  echo "Robust 3D Model Generator"
  echo "-----------------------"
  echo "Generates 3D models from text descriptions"
  echo ""
  echo "Usage: ./generate_3d.sh \"Your text description\""
  echo ""
  echo "Examples:"
  echo "  ./generate_3d.sh \"A modern house with two bedrooms and kitchen\""
  echo ""
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  show_help
  exit 0
fi

# Check if any text description was provided
if [ $# -eq 0 ]; then
  echo "Error: Please provide a text description."
  show_help
  exit 1
fi

# Ensure output directory exists
mkdir -p output

# Clean previous output files
echo "🧹 Cleaning previous output files..."
rm -f output/*.obj output/*.mtl output/*.glb output/*.png output/*.json

# Join all arguments to form the description
DESCRIPTION="$*"

echo "🚀 3D Model Generator"
echo "------------------"
echo "Generating 3D model from: \"$DESCRIPTION\""

# Generate the 3D model from text description
python generate_model.py "$DESCRIPTION"

# Check if model generation was successful
if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Base model generated successfully!"
  echo ""
  
  # Create the reliable GLB converter script if it doesn't exist
  if [ ! -f reliable_glb_converter.py ]; then
    echo "Creating reliable GLB converter script..."
    # Generate the script content
    cat > reliable_glb_converter.py << 'ENDSCRIPT'
#!/usr/bin/env python3
"""
Reliable GLB Converter
---------------------
Creates properly formatted GLB files that work in all viewers
"""

import os
import sys
import numpy as np
from pathlib import Path

def convert_obj_to_reliable_glb(obj_file=None, output_file=None):
    """Convert OBJ to GLB using the most reliable methods."""
    print("\n🔧 Reliable GLB Converter")
    print("----------------------")
    
    # Find most recent OBJ file if none specified
    if not obj_file:
        obj_files = list(Path("output").glob("*.obj"))
        if not obj_files:
            print("Error: No OBJ files found.")
            return False
        obj_file = str(max(obj_files, key=os.path.getmtime))
    
    # Set output GLB file
    if not output_file:
        output_file = os.path.splitext(obj_file)[0] + "_reliable.glb"
    
    print(f"Processing: {obj_file}")
    
    try:
        import trimesh
        print(f"Trimesh version: {trimesh.__version__}")
        
        # Define vibrant colors (RGB only, alpha added later)
        room_colors = {
            "bedroom": [1.0, 0.4, 0.7],      # Pink
            "kitchen": [0.2, 0.4, 1.0],      # Blue
            "bathroom": [0.2, 0.8, 0.2],     # Green
            "living": [1.0, 0.6, 0.0],       # Orange
            "tv": [0.9, 0.5, 0.0],           # Dark Orange
            "lounge": [0.9, 0.6, 0.2],       # Light Orange
            "dining": [0.5, 0.1, 0.9],       # Purple
            "play": [0.0, 0.6, 1.0],         # Cyan
            "office": [1.0, 0.8, 0.0],       # Gold
            "hallway": [0.9, 0.9, 0.5],      # Light Yellow
            "entry": [0.8, 0.7, 0.5],        # Tan
        }
        
        # Parse vertices and faces from OBJ
        print("Parsing OBJ data...")
        vertices, faces, groups = parse_obj_file(obj_file)
        
        if not vertices or not faces:
            print("Error: Could not extract valid geometry from OBJ file")
            return False
            
        print(f"- Found {len(vertices)} vertices and {len(faces)} faces")
        print(f"- Found {len(groups)} groups/rooms")
        
        # Create a new scene
        scene = trimesh.Scene()
        
        # Create meshes for each group
        for group_name, group_faces in groups.items():
            # Skip empty groups
            if not group_faces:
                continue
                
            # Find appropriate color based on room type
            color = [0.7, 0.7, 0.7]  # Default gray
            for room_type, room_color in room_colors.items():
                if room_type.lower() in group_name.lower():
                    color = room_color
                    print(f"- Colored {group_name} as {room_type}")
                    break
            
            # Create triangles from faces (triangulate quads)
            triangles = []
            for face in group_faces:
                if len(face) == 3:
                    triangles.append(face)
                elif len(face) == 4:
                    triangles.append([face[0], face[1], face[2]])
                    triangles.append([face[0], face[2], face[3]])
            
            if not triangles:
                continue
                
            try:
                # Create a mesh with vertices and triangulated faces
                mesh = trimesh.Trimesh(
                    vertices=np.array(vertices),
                    faces=np.array(triangles),
                    process=False
                )
                
                # Apply color (using float values 0-1)
                if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'face_colors'):
                    # Add alpha channel (1.0)
                    rgba_color = color + [1.0]
                    
                    # Convert to uint8 (0-255) for face_colors
                    uint8_color = (np.array(rgba_color) * 255).astype(np.uint8)
                    
                    # Apply to all faces
                    mesh.visual.face_colors = np.tile(
                        uint8_color,
                        (len(mesh.faces), 1)
                    )
                
                # Add to scene
                scene.add_geometry(mesh, geom_name=group_name)
            except Exception as e:
                print(f"Error creating mesh for {group_name}: {e}")
        
        # Export to GLB using the most basic parameters
        print(f"Exporting to GLB: {output_file}")
        
        # Get the correct export function based on trimesh version
        try:
            # Try direct export (newer trimesh)
            trimesh.exchange.export.export_mesh(
                scene, 
                output_file, 
                file_type='glb'
            )
        except:
            # Fall back to basic export
            with open(output_file, 'wb') as f:
                # Export as GLB with minimal options
                f.write(trimesh.exchange.gltf.export_glb(scene))
        
        print(f"✅ GLB created successfully at: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try a super minimal approach as fallback
        print("Trying minimal fallback export...")
        return export_minimal_glb(vertices, faces, output_file)

def parse_obj_file(obj_file):
    """Parse OBJ file safely, extracting vertices, faces, and groups."""
    vertices = []
    faces = []
    groups = {}
    current_group = "default"
    groups[current_group] = []
    
    try:
        with open(obj_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('v '):
                    # Parse vertex (v x y z)
                    parts = line.split()
                    if len(parts) >= 4:
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                
                elif line.startswith('g ') or line.startswith('o '):
                    # Group or object name
                    current_group = line.split(' ', 1)[1].strip()
                    if current_group not in groups:
                        groups[current_group] = []
                
                elif line.startswith('f '):
                    # Face (f v1 v2 v3 ...)
                    parts = line.split()[1:]
                    face_indices = []
                    
                    for part in parts:
                        # Handle v/vt/vn format
                        if '/' in part:
                            vertex_idx = int(part.split('/')[0])
                        else:
                            vertex_idx = int(part)
                        
                        # Convert to 0-indexed and validate
                        vertex_idx = vertex_idx - 1  # OBJ is 1-indexed
                        
                        # Skip if out of bounds
                        if vertex_idx >= len(vertices) or vertex_idx < 0:
                            continue
                            
                        face_indices.append(vertex_idx)
                    
                    # Add face if it has at least 3 valid vertices
                    if len(face_indices) >= 3:
                        faces.append(face_indices)
                        groups[current_group].append(face_indices)
    except Exception as e:
        print(f"Error parsing OBJ: {e}")
    
    return vertices, faces, groups

def export_minimal_glb(vertices, faces, output_file):
    """Create the simplest possible GLB as a fallback."""
    try:
        import trimesh
        import json
        import struct
        import base64
        
        # Create a basic mesh with just vertices and faces
        if not vertices or not faces:
            print("No valid geometry to export")
            return False
            
        # Triangulate all faces
        triangles = []
        for face in faces:
            if len(face) == 3:
                triangles.append(face)
            elif len(face) >= 4:  # Handle n-gons
                for i in range(2, len(face)):
                    triangles.append([face[0], face[i-1], face[i]])
        
        print(f"Creating minimal mesh with {len(vertices)} vertices and {len(triangles)} triangles")
        
        # Try with simple trimesh approach first
        try:
            mesh = trimesh.Trimesh(
                vertices=np.array(vertices),
                faces=np.array(triangles),
                process=False
            )
            
            # Set colors - divide into colored sections
            colors = np.zeros((len(triangles), 4), dtype=np.uint8)
            section_size = max(1, len(triangles) // 5)  # At most 5 sections
            
            # Apply different colors to sections
            section_colors = [
                [255, 102, 178, 255],  # Pink
                [102, 178, 255, 255],  # Light blue
                [102, 255, 102, 255],  # Light green
                [255, 178, 102, 255],  # Light orange
                [178, 102, 255, 255]   # Light purple
            ]
            
            for i in range(len(triangles)):
                section = min(i // section_size, len(section_colors) - 1)
                colors[i] = section_colors[section]
            
            mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, face_colors=colors)
            
            # Export directly to GLB
            print("Exporting minimal mesh...")
            with open(output_file, 'wb') as f:
                f.write(trimesh.exchange.gltf.export_glb(
                    trimesh.Scene([mesh]),
                ))
                
            print(f"✅ Minimal GLB created successfully at: {output_file}")
            return True
            
        except Exception as e:
            print(f"Minimal export failed: {e}")
            return False
            
    except Exception as e:
        print(f"Fallback export failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Reliable GLB Converter (2025-07-12 21:55)")
    
    # Try to import trimesh
    try:
        import trimesh
    except ImportError:
        print("Installing required packages...")
        import pip
        pip.main(['install', '--user', 'trimesh', 'numpy'])
        import trimesh
    
    # Run converter
    if convert_obj_to_reliable_glb():
        print("\n🎉 Success! Your model is ready to view.")
        print("\nView your model in:")
        print("- Online: https://gltf-viewer.donmccurdy.com/")
        print("- Online: https://3dviewer.net/")
        print("- Online: https://sandbox.babylonjs.com/")
    else:
        print("\n❌ GLB creation failed.")
ENDSCRIPT
    chmod +x reliable_glb_converter.py
  fi
  
  # Run the converter
  echo "🔄 Converting to reliable GLB format..."
  python reliable_glb_converter.py
  
  # Check if GLB file was created
  if ls output/*_reliable.glb 1> /dev/null 2>&1; then
    echo ""
    echo "🎉 GLB file created successfully!"
    
    # Get the path to the reliable GLB file
    RELIABLE_GLB=$(ls -t output/*_reliable.glb | head -1)
    echo "Your 3D model files:"
    echo "- Reliable GLB file: $RELIABLE_GLB"
    echo "- OBJ file: $(ls -t output/*.obj | head -1)"
    echo "- PNG preview: output/3d_model.png"
    echo ""
    
    echo "View your 3D model in:"
    echo "- Online: https://gltf-viewer.donmccurdy.com/"
    echo "- Online: https://3dviewer.net/"
    echo "- Online: https://sandbox.babylonjs.com/"
  else
    echo ""
    echo "❌ GLB file creation failed. Check the errors above."
  fi
else
  echo ""
  echo "❌ Error: Model generation failed."
  echo ""
fi