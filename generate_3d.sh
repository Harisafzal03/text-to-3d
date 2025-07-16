#!/bin/bash
# Enhanced 3D House Plan Generator
# Current Date: 2025-07-16 13:17:27
# User: Harisafzal03

# Display help message
show_help() {
  echo "Enhanced 3D House Plan Generator"
  echo "------------------------------"
  echo "Generates 3D house plans from text descriptions with plot size in Marla/Kanal"
  echo ""
  echo "Usage: ./generate_3d.sh \"Your house description\""
  echo ""
  echo "Examples:"
  echo "  ./generate_3d.sh \"A 10 Marla house with two bedrooms with attached washrooms, kitchen, TV lounge, and garage\""
  echo "  ./generate_3d.sh \"A modern 2 story 1 Kanal house with 4 bedrooms, kitchen and lobby\""
  echo ""
  echo "Features:"
  echo "  - Plot sizing in Marla and Kanal units"
  echo "  - Bedrooms with attached washrooms"
  echo "  - Kitchen and washroom proper placement"
  echo "  - Main entrance visualization"
  echo "  - Lobby and terrace support"
  echo "  - Garage/car parking"
  echo "  - Stairs for multi-story buildings"
  echo "  - TV lounge and other room types"
  echo ""
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  show_help
  exit 0
fi

# Check if any text description was provided
if [ $# -eq 0 ]; then
  echo "Error: Please provide a house description."
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

echo "🚀 Enhanced 3D House Plan Generator"
echo "--------------------------------"
echo "Generating 3D house plan from: \"$DESCRIPTION\""

# Generate the 3D model from text description
python generate_model.py "$DESCRIPTION"

# Check if model generation was successful
if [ $? -eq 0 ]; then
  echo ""
  echo "✅ House plan generated successfully!"
  echo ""
  
  # Create the GLB converter script if it doesn't exist
  if [ ! -f reliable_glb_converter.py ]; then
    echo "Creating GLB converter script..."
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
        output_file = os.path.splitext(obj_file)[0] + ".glb"
    
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
            "terrace": [0.7, 0.9, 0.8],      # Mint Green
            "washroom": [0.5, 0.8, 0.5],     # Light Green
            "garage": [0.6, 0.6, 0.7],       # Gray-Blue
            "car": [0.7, 0.7, 0.8],          # Light Purple-Gray
            "lobby": [0.8, 0.8, 0.6],        # Light Brown
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
        
        # Try different export methods based on trimesh version compatibility
        print(f"Exporting to GLB: {output_file}")
        
        try:
            # First try with scipy, which some trimesh installations require
            try:
                import scipy
                has_scipy = True
            except ImportError:
                has_scipy = False
                
            if has_scipy:
                # Use full export with all options
                with open(output_file, 'wb') as f:
                    # Export as GLB with minimal options
                    f.write(trimesh.exchange.gltf.export_glb(scene))
            else:
                # Use direct scene export without relying on scipy
                scene.export(output_file, file_type='glb')
                
        except Exception as e:
            print(f"Standard export failed: {e}")
            print("Trying alternative export method...")
            
            try:
                # Try most basic export method that should work on all trimesh versions
                mesh = combine_scene_meshes(scene)
                if mesh:
                    with open(output_file, 'wb') as f:
                        data = trimesh.exchange.gltf.export_glb(
                            trimesh.Scene([mesh])
                        )
                        f.write(data)
                else:
                    print("Failed to combine meshes")
                    return False
            except Exception as e2:
                print(f"Alternative export also failed: {e2}")
                print("Creating a simple colored mesh as fallback...")
                return create_simple_fallback(vertices, faces, output_file)
        
        print(f"✅ GLB created successfully at: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try a super minimal approach as fallback
        print("Trying minimal fallback export...")
        return create_simple_fallback(vertices, faces, output_file)

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

def combine_scene_meshes(scene):
    """Combine all meshes in a scene into a single mesh with preserved colors."""
    import trimesh
    import numpy as np
    
    if not scene or not scene.geometry:
        return None
    
    # Get all meshes
    meshes = []
    for name, geom in scene.geometry.items():
        if isinstance(geom, trimesh.Trimesh):
            meshes.append(geom)
    
    if not meshes:
        return None
    
    # Combine vertices and faces
    combined_vertices = []
    combined_faces = []
    combined_colors = []
    
    # Process each mesh
    vertex_offset = 0
    for mesh in meshes:
        # Add vertices
        combined_vertices.extend(mesh.vertices)
        
        # Adjust and add faces
        for face in mesh.faces:
            combined_faces.append([idx + vertex_offset for idx in face])
        
        # Add face colors
        if hasattr(mesh.visual, 'face_colors'):
            combined_colors.extend(mesh.visual.face_colors)
        else:
            # Default color if not present
            default_color = np.array([200, 200, 200, 255], dtype=np.uint8)
            combined_colors.extend(np.tile(default_color, (len(mesh.faces), 1)))
        
        # Update offset for next mesh
        vertex_offset += len(mesh.vertices)
    
    # Create new mesh
    combined_mesh = trimesh.Trimesh(
        vertices=np.array(combined_vertices),
        faces=np.array(combined_faces),
        process=False
    )
    
    # Apply colors
    combined_mesh.visual = trimesh.visual.ColorVisuals(
        mesh=combined_mesh, 
        face_colors=np.array(combined_colors)
    )
    
    return combined_mesh

def create_simple_fallback(vertices, faces, output_file):
    """Create a simple colored mesh as a last resort."""
    try:
        import trimesh
        import numpy as np
        
        print("Creating basic colored mesh fallback...")
        
        # Triangulate all faces
        triangles = []
        for face in faces:
            if len(face) == 3:
                triangles.append(face)
            elif len(face) == 4:
                triangles.append([face[0], face[1], face[2]])
                triangles.append([face[0], face[2], face[3]])
            elif len(face) > 4:
                # Simple triangulation for n-gons
                for i in range(1, len(face) - 1):
                    triangles.append([face[0], face[i], face[i+1]])
        
        if not triangles:
            print("No valid triangles to export")
            return False
        
        # Create mesh
        mesh = trimesh.Trimesh(
            vertices=np.array(vertices),
            faces=np.array(triangles),
            process=False
        )
        
        # Color by sections for visual distinction
        colors = []
        section_size = max(1, len(triangles) // 5)
        
        section_colors = [
            [255, 102, 178, 255],  # Pink
            [102, 178, 255, 255],  # Light blue
            [102, 255, 102, 255],  # Light green
            [255, 178, 102, 255],  # Light orange
            [178, 102, 255, 255],  # Light purple
        ]
        
        for i in range(len(triangles)):
            section = min(i // section_size, len(section_colors) - 1)
            colors.append(section_colors[section])
        
        # Apply colors
        mesh.visual = trimesh.visual.ColorVisuals(
            mesh=mesh,
            face_colors=np.array(colors, dtype=np.uint8)
        )
        
        # Export with minimal requirements
        print(f"Exporting fallback GLB: {output_file}")
        with open(output_file, 'wb') as f:
            f.write(trimesh.exchange.gltf.export_glb(
                trimesh.Scene([mesh])
            ))
        
        print("✅ Fallback GLB created successfully!")
        return True
        
    except Exception as e:
        print(f"Fallback export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Reliable GLB Converter (2025-07-16 13:22)")
    
    # Try to import trimesh
    try:
        import trimesh
    except ImportError:
        print("Installing required packages...")
        import pip
        pip.main(['install', '--user', 'trimesh', 'numpy'])
        try:
            import trimesh
        except ImportError:
            print("Failed to import trimesh. Please install manually: pip install trimesh")
            sys.exit(1)
    
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
  echo "🔄 Converting to GLB format..."
  python reliable_glb_converter.py
  
  # Get the latest model files
  LATEST_OBJ=$(ls -t output/*.obj | head -1)
  LATEST_GLB=${LATEST_OBJ%.obj}.glb
  
  # Check if GLB file was created
  if [ -f "$LATEST_GLB" ]; then
    echo ""
    echo "🎉 House plan complete!"
    echo ""
    
    # Show the model files
    echo "Your house plan files:"
    echo "- 2D Floor Plan: output/floor_plan.png"
    echo "- 3D Model View: output/3d_model.png"
    echo "- 3D Model OBJ: $LATEST_OBJ"
    echo "- 3D Model GLB: $LATEST_GLB"
    echo ""
    
    # Show plot information
    if [ -f output/model_info.json ]; then
      PLOT_INFO=$(grep -A3 "plot_size" output/model_info.json | grep "marla\|kanal")
      STORIES_INFO=$(grep -A1 "stories" output/model_info.json | grep -v "plot_size" | head -1)
      
      echo "Property Information:"
      echo "$PLOT_INFO"
      echo "$STORIES_INFO"
      echo ""
    fi
    
    echo "To view your 3D model, use:"
    echo "- Online: https://gltf-viewer.donmccurdy.com/"
    echo "- Online: https://3dviewer.net/"
    echo "- Desktop: Any 3D viewer that supports GLB format"
  else
    echo ""
    echo "❌ GLB file creation failed. Check the errors above."
    echo "You can still view the OBJ file in a 3D modeling application."
  fi
else
  echo ""
  echo "❌ Error: Model generation failed."
  echo ""
fi