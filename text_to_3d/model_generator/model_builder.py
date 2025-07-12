import numpy as np
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import random
import colorsys
import time
import json
from pathlib import Path

class ModelBuilder:
    def __init__(self):
        """Initialize the 3D model builder."""
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Note: We don't actually need to store template methods as attributes
        # Just having the methods defined in the class is sufficient
    
    def generate_3d_model(self, layout):
        """Generate a 3D model from a layout."""
        start_time = time.time()
        print("Building detailed 3D model...")
        
        # Determine what kind of object we're building
        object_type = layout.get("object_type", "house")
        
        # Use the appropriate builder for the object type
        if object_type == "house":
            model = self._build_house_model(layout)
        elif object_type == "car":
            model = self._build_car_model(layout)
        elif object_type == "furniture":
            model = self._build_furniture_model(layout)
        elif object_type == "fruit":
            model = self._build_fruit_model(layout)
        else:
            model = self._build_generic_model(layout)
        
        # Save model information for later use by the GLB exporter
        self._save_model_info(model)
        
        # Visualize the 3D model
        model["visualization_path"] = self._visualize_3d_model(model)
        
        elapsed = time.time() - start_time
        print(f"3D model built in {elapsed:.2f} seconds")
        
        return model
    
    def _save_model_info(self, model):
        """Save model information to a file for use by other components."""
        info = {
            "object_type": model.get("object_type", "house"),
            "rooms": [],
            "colors": {},
        }
        
        # Add room information if applicable
        for room in model.get("room_meshes", []):
            room_info = {
                "type": room["type"],
                "name": str(room["name"]),  # Ensure name is a string
                "color": room.get("color")
            }
            info["rooms"].append(room_info)
        
        # Save the file
        with open('output/model_info.json', 'w') as f:
            json.dump(info, f)
    
    def _build_house_model(self, layout):
        """Build a 3D house model from the layout."""
        rooms = layout.get("rooms", [])
        
        # Initialize 3D model structure
        model = {
            "object_type": "house",
            "vertices": [],
            "faces": [],
            "colors": [],  # Add color data
            "room_meshes": [],
            "furniture": [],
            "layout": layout  # Store original layout for reference
        }
        
        vertex_offset = 0
        
        # Wall height parameter
        wall_height = 3.0  # 3 meters
        
        # Scale factor to convert from grid coordinates to 3D world coordinates
        scale = 1.0
        
        # Convert each room to a 3D box with distinct colors
        for room in rooms:
            room_type = room["type"].lower()
            x, y = room["position"]
            width, height = room["size"]
            
            # Generate a vibrant color for this room based on type
            room_color = self._get_vibrant_room_color(room_type)
            
            # Create 3D mesh for this room
            room_mesh = self._create_detailed_room(
                x, y, width, height, 
                wall_height, 
                scale,
                room_type
            )
            
            # Add vertices and faces to the model
            vertices_count = len(model["vertices"])
            model["vertices"].extend(room_mesh["vertices"])
            
            # Update face indices to account for vertex offset
            offset_faces = [
                [idx + vertex_offset for idx in face]
                for face in room_mesh["faces"]
            ]
            model["faces"].extend(offset_faces)
            
            # Add colors for each face
            for face_type in room_mesh["face_types"]:
                if face_type == "floor":
                    model["colors"].append([0.9, 0.9, 0.9])  # Light gray for floor
                elif face_type == "ceiling":
                    model["colors"].append([0.95, 0.95, 0.95])  # White for ceiling
                else:  # wall
                    model["colors"].append(room_color)  # Room color for walls
            
            # Store room information - ensure name is stored as a string
            room_data = {
                "id": room["id"],
                "type": room["type"],
                "name": str(room.get("id", room_type)),  # Convert to string
                "vertex_start": vertex_offset,
                "vertex_count": len(room_mesh["vertices"]),
                "face_start": len(model["faces"]) - len(room_mesh["faces"]),
                "face_count": len(room_mesh["faces"]),
                "color": room_color
            }
            model["room_meshes"].append(room_data)
            
            # Update vertex offset for the next room
            vertex_offset += len(room_mesh["vertices"])
            
            # Add appropriate furniture based on room type
            furniture = self._add_room_furniture(room_type, x, y, width, height, wall_height)
            if furniture:
                model["furniture"].extend(furniture)
        
        # Add openings (doors/windows) between connected rooms
        model = self._add_openings(model, layout)
        
        # Add a floor and ceiling to the entire house
        model = self._add_house_exterior(model)
        
        return model
    
    def _build_car_model(self, layout):
        """Build a 3D car model."""
        # Extract car features
        car_type = layout.get("car_type", "sedan")
        car_brand = layout.get("car_brand")
        car_colors = layout.get("colors", {})
        
        # Choose primary color
        primary_color = [0.8, 0.0, 0.0]  # Default red
        if car_colors:
            primary_color = list(car_colors.values())[0]
        
        # Initialize 3D model structure
        model = {
            "object_type": "car",
            "vertices": [],
            "faces": [],
            "colors": [],
            "car_type": car_type,
            "car_brand": car_brand,
            "primary_color": primary_color
        }
        
        # Create car body
        body_mesh = self._create_car_body(car_type)
        
        # Add vertices and faces to the model
        vertices_count = len(model["vertices"])
        model["vertices"].extend(body_mesh["vertices"])
        model["faces"].extend(body_mesh["faces"])
        
        # Add colors
        for face_type in body_mesh["face_types"]:
            if face_type == "body":
                model["colors"].append(primary_color)
            elif face_type == "window":
                model["colors"].append([0.7, 0.8, 0.9])  # Light blue for windows
            elif face_type == "wheel":
                model["colors"].append([0.1, 0.1, 0.1])  # Dark for wheels
            else:
                model["colors"].append([0.8, 0.8, 0.8])  # Gray for other parts
        
        return model
    
    def _build_fruit_model(self, layout):
        """Build a 3D fruit model (e.g., apple)."""
        # Extract features
        colors = layout.get("colors", {})
        
        # Choose primary color
        primary_color = [0.8, 0.1, 0.1]  # Default red for apple
        if "red" in colors:
            primary_color = colors["red"]
        elif "green" in colors:
            primary_color = colors["green"]
        elif "yellow" in colors:
            primary_color = colors["yellow"]
        
        # Initialize 3D model structure
        model = {
            "object_type": "fruit",
            "vertices": [],
            "faces": [],
            "colors": [],
            "primary_color": primary_color
        }
        
        # Create fruit mesh
        fruit_mesh = self._create_apple_mesh()
        
        # Add vertices and faces to the model
        model["vertices"].extend(fruit_mesh["vertices"])
        model["faces"].extend(fruit_mesh["faces"])
        
        # Add colors
        for face_type in fruit_mesh["face_types"]:
            if face_type == "body":
                model["colors"].append(primary_color)
            elif face_type == "stem":
                model["colors"].append([0.3, 0.2, 0.0])  # Brown for stem
            else:
                model["colors"].append(primary_color)
        
        return model
    
    def _build_furniture_model(self, layout):
        """Build a 3D furniture model (e.g., chair, table)."""
        # Extract features
        furniture_type = layout.get("furniture_type", "chair")
        colors = layout.get("colors", {})
        
        # Choose primary color
        primary_color = [0.6, 0.4, 0.2]  # Default wood color
        for color_name in ["brown", "black", "white", "blue", "red"]:
            if color_name in colors:
                primary_color = colors[color_name]
                break
        
        # Initialize 3D model structure
        model = {
            "object_type": "furniture",
            "furniture_type": furniture_type,
            "vertices": [],
            "faces": [],
            "colors": [],
            "primary_color": primary_color
        }
        
        # Create furniture mesh
        if furniture_type == "chair":
            furniture_mesh = self._create_chair_mesh()
        elif furniture_type == "table":
            furniture_mesh = self._create_table_mesh()
        else:
            furniture_mesh = self._create_generic_furniture_mesh()
        
        # Add vertices and faces to the model
        model["vertices"].extend(furniture_mesh["vertices"])
        model["faces"].extend(furniture_mesh["faces"])
        
        # Add colors
        for face_type in furniture_mesh["face_types"]:
            model["colors"].append(primary_color)
        
        return model
    
    def _build_generic_model(self, layout):
        """Build a generic 3D model."""
        # Extract features
        colors = layout.get("colors", {})
        
        # Choose primary color
        primary_color = [0.7, 0.7, 0.7]  # Default gray
        if colors:
            primary_color = list(colors.values())[0]
        
        # Initialize 3D model structure
        model = {
            "object_type": "generic",
            "vertices": [],
            "faces": [],
            "colors": [],
            "primary_color": primary_color
        }
        
        # Create a simple box mesh
        box_mesh = {
            "vertices": [
                [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
            ],
            "faces": [
                [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
                [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]
            ],
            "face_types": ["side", "side", "side", "side", "side", "side"]
        }
        
        # Add vertices and faces to the model
        model["vertices"].extend(box_mesh["vertices"])
        model["faces"].extend(box_mesh["faces"])
        
        # Add colors
        for face_type in box_mesh["face_types"]:
            model["colors"].append(primary_color)
        
        return model
    
    def _create_detailed_room(self, x, y, width, height, wall_height, scale, room_type):
        """Create a detailed 3D mesh for a room with windows."""
        # Scale the coordinates
        x1, y1 = x * scale, y * scale
        x2, y2 = (x + width) * scale, (y + height) * scale
        z1, z2 = 0.0, wall_height
        
        # Define the 8 vertices of the room box
        vertices = [
            [x1, y1, z1],  # 0: bottom near left
            [x2, y1, z1],  # 1: bottom near right
            [x2, y2, z1],  # 2: bottom far right
            [x1, y2, z1],  # 3: bottom far left
            [x1, y1, z2],  # 4: top near left
            [x2, y1, z2],  # 5: top near right
            [x2, y2, z2],  # 6: top far right
            [x1, y2, z2]   # 7: top far left
        ]
        
        # Define the 6 faces of the room box
        faces = [
            [0, 1, 2, 3],  # Floor
            [4, 5, 6, 7],  # Ceiling
            [0, 1, 5, 4],  # Wall 1
            [1, 2, 6, 5],  # Wall 2
            [2, 3, 7, 6],  # Wall 3
            [3, 0, 4, 7]   # Wall 4
        ]
        
        # Define face types
        face_types = [
            "floor",
            "ceiling",
            "wall",
            "wall",
            "wall",
            "wall"
        ]
        
        return {
            "vertices": vertices,
            "faces": faces,
            "face_types": face_types
        }
    
    def _get_vibrant_room_color(self, room_type):
        """Get vibrant color for a specific room type."""
        # Define base vibrant colors for different room types
        room_base_colors = {
            "kitchen": [0.4, 0.6, 1.0],       # Vibrant blue
            "bedroom": [1.0, 0.6, 0.8],       # Vibrant pink
            "bathroom": [0.6, 1.0, 0.6],      # Vibrant green
            "living room": [1.0, 0.9, 0.5],   # Vibrant yellow
            "tv lounge": [1.0, 0.7, 0.4],     # Vibrant orange
            "playing room": [0.5, 0.8, 1.0],  # Vibrant cyan
            "dining room": [1.0, 0.5, 0.5]    # Vibrant coral
        }
        
        # If we have a predefined color for this room type, use it
        if room_type in room_base_colors:
            base_color = room_base_colors[room_type]
        else:
            # Generate a vibrant color based on the room type hash
            hue = abs(hash(room_type)) % 360 / 360.0
            base_color = colorsys.hsv_to_rgb(hue, 0.8, 1.0)  # High saturation
        
        # Add some subtle randomness to make each room unique
        jitter = 0.05
        color = [
            min(1.0, max(0.0, c + (random.random() - 0.5) * jitter))
            for c in base_color
        ]
        
        return color
    
    def _add_room_furniture(self, room_type, x, y, width, height, wall_height):
        """Add appropriate furniture based on room type."""
        furniture = []
        room_center_x = x + width/2
        room_center_y = y + height/2
        
        # Scale furniture based on room size
        scale_factor = min(width, height) / 10
        
        if "bedroom" in room_type:
            # Add a bed
            bed = self._create_furniture(
                "bed",
                x + width * 0.2,
                y + height * 0.2,
                width * 0.6,
                height * 0.6,
                0.5,  # height
                [0.6, 0.4, 0.2]  # brown
            )
            furniture.append(bed)
            
            # Add a nightstand
            nightstand = self._create_furniture(
                "nightstand",
                x + width * 0.15,
                y + height * 0.15,
                width * 0.2,
                height * 0.2,
                0.6,
                [0.5, 0.35, 0.2]  # darker brown
            )
            furniture.append(nightstand)
            
        elif "kitchen" in room_type:
            # Add kitchen counter along the walls
            counter1 = self._create_furniture(
                "kitchen_counter",
                x + width * 0.1,
                y + height * 0.1,
                width * 0.8,
                height * 0.2,
                0.9,
                [0.9, 0.9, 0.9]  # white/gray
            )
            furniture.append(counter1)
            
            # Add a second counter perpendicular
            counter2 = self._create_furniture(
                "kitchen_counter",
                x + width * 0.1,
                y + height * 0.3,
                width * 0.2,
                height * 0.6,
                0.9,
                [0.9, 0.9, 0.9]  # white/gray
            )
            furniture.append(counter2)
            
            # Add a table
            table = self._create_furniture(
                "dining_table",
                x + width * 0.5,
                y + height * 0.5,
                width * 0.3,
                height * 0.3,
                0.8,
                [0.8, 0.6, 0.4]  # wood color
            )
            furniture.append(table)
            
        elif "living room" in room_type or "tv lounge" in room_type:
            # Add a sofa
            sofa = self._create_furniture(
                "sofa",
                x + width * 0.2,
                y + height * 0.6,
                width * 0.6,
                height * 0.25,
                0.8,
                [0.3, 0.3, 0.7]  # blue
            )
            furniture.append(sofa)
            
            # Add a TV stand
            tv = self._create_furniture(
                "tv_stand",
                x + width * 0.3,
                y + height * 0.15,
                width * 0.4,
                height * 0.1,
                0.5,
                [0.2, 0.2, 0.2]  # black
            )
            furniture.append(tv)
            
            # Add a coffee table
            table = self._create_furniture(
                "table",
                x + width * 0.35,
                y + height * 0.4,
                width * 0.3,
                height * 0.15,
                0.4,
                [0.7, 0.5, 0.3]  # wood color
            )
            furniture.append(table)
            
        elif "playing room" in room_type or "play" in room_type:
            # Add play area
            play_area = self._create_furniture(
                "play_area",
                x + width * 0.25,
                y + height * 0.25,
                width * 0.5,
                height * 0.5,
                0.1,  # low height
                [0.2, 0.6, 0.8]  # blue
            )
            furniture.append(play_area)
            
            # Add storage units
            storage = self._create_furniture(
                "storage",
                x + width * 0.1,
                y + height * 0.1,
                width * 0.2,
                height * 0.8,
                1.2,
                [1.0, 0.8, 0.0]  # yellow
            )
            furniture.append(storage)
            
        elif "bathroom" in room_type:
            # Add toilet
            toilet = self._create_furniture(
                "toilet",
                x + width * 0.2,
                y + height * 0.15,
                width * 0.25,
                height * 0.25,
                0.4,
                [0.9, 0.9, 0.9]  # white
            )
            furniture.append(toilet)
            
            # Add sink
            sink = self._create_furniture(
                "sink",
                x + width * 0.6,
                y + height * 0.15,
                width * 0.3,
                height * 0.25,
                0.8,
                [0.9, 0.9, 0.9]  # white
            )
            furniture.append(sink)
            
            # Add bathtub or shower
            if width * height > 16:  # If bathroom is large enough
                tub = self._create_furniture(
                    "bathtub",
                    x + width * 0.2,
                    y + height * 0.6,
                    width * 0.6,
                    height * 0.3,
                    0.6,
                    [0.9, 0.9, 0.9]  # white
                )
                furniture.append(tub)
        
        return furniture
    
    def _create_furniture(self, furniture_type, x, y, width, depth, height, color):
        """Create a piece of furniture with the given dimensions."""
        return {
            "type": furniture_type,
            "position": [x, y, 0],  # Place on floor
            "dimensions": [width, depth, height],
            "color": color
        }
    
    def _add_openings(self, model, layout):
        """Add door openings between connected rooms."""
        # Each connection gets a door or opening
        for connection in layout.get("connections", []):
            source_idx = connection.get("source")
            target_idx = connection.get("target")
            
            if source_idx is None or target_idx is None:
                continue
                
            # Get the room data
            if source_idx >= len(model["room_meshes"]) or target_idx >= len(model["room_meshes"]):
                continue
                
            source_room = model["room_meshes"][source_idx]
            target_room = model["room_meshes"][target_idx]
            
            # Add a door connection to the model
            model["furniture"].append({
                "type": "door",
                "connects": [source_idx, target_idx],
                "source_room": source_room["name"],
                "target_room": target_room["name"]
            })
        
        return model
    
    def _add_house_exterior(self, model):
        """Add exterior elements to the house like foundation and roof."""
        # Get the bounds of the house
        all_vertices = model["vertices"]
        if not all_vertices:
            return model
        
        min_x = min(v[0] for v in all_vertices)
        max_x = max(v[0] for v in all_vertices)
        min_y = min(v[1] for v in all_vertices)
        max_y = max(v[1] for v in all_vertices)
        min_z = min(v[2] for v in all_vertices)
        max_z = max(v[2] for v in all_vertices)
        
        # Add foundation
        foundation_height = 0.2  # 20cm thick
        foundation = {
            "type": "foundation",
            "position": [min_x - 0.5, min_y - 0.5, min_z - foundation_height],
            "dimensions": [max_x - min_x + 1, max_y - min_y + 1, foundation_height],
            "color": [0.5, 0.5, 0.5]  # Gray
        }
        model["furniture"].append(foundation)
        
        # Add roof structure
        roof_height = 1.0  # 1m tall roof
        roof = {
            "type": "roof",
            "position": [min_x - 0.5, min_y - 0.5, max_z],
            "dimensions": [max_x - min_x + 1, max_y - min_y + 1, roof_height],
            "color": [0.7, 0.3, 0.2]  # Reddish brown
        }
        model["furniture"].append(roof)
        
        return model
    
    def _create_car_body(self, car_type):
        """Create a car body mesh based on car type."""
        # Create a simple car mesh
        if car_type == "sedan":
            return self._create_sedan_mesh()
        elif car_type == "suv":
            return self._create_suv_mesh()
        elif car_type == "sports car":
            return self._create_sports_car_mesh()
        else:
            return self._create_sedan_mesh()  # Default
    
    def _create_sedan_mesh(self):
        """Create a sedan car mesh."""
        # Very simplified car mesh
        vertices = [
            # Bottom of car
            [0, 0, 0], [4, 0, 0], [4, 2, 0], [0, 2, 0],
            # Middle of car (bottom of windows)
            [0.5, 0.2, 1], [3.5, 0.2, 1], [3.5, 1.8, 1], [0.5, 1.8, 1],
            # Top of car
            [1, 0.5, 1.5], [3, 0.5, 1.5], [3, 1.5, 1.5], [1, 1.5, 1.5]
        ]
        
        faces = [
            # Bottom
            [0, 1, 2, 3],
            # Front
            [0, 1, 5, 4],
            # Right side
            [1, 2, 6, 5],
            # Back
            [2, 3, 7, 6],
            # Left side
            [3, 0, 4, 7],
            # Middle to top (front window)
            [4, 5, 9, 8],
            # Middle to top (right side)
            [5, 6, 10, 9],
            # Middle to top (back window)
            [6, 7, 11, 10],
            # Middle to top (left side)
            [7, 4, 8, 11],
            # Roof
            [8, 9, 10, 11]
        ]
        
        face_types = [
            "body", "body", "body", "body", "body",
            "window", "body", "window", "body", "body"
        ]
        
        return {
            "vertices": vertices,
            "faces": faces,
            "face_types": face_types
        }
    
    def _create_suv_mesh(self):
        """Create an SUV car mesh."""
        # SUV is similar to sedan but taller
        vertices = [
            # Bottom of car
            [0, 0, 0], [4, 0, 0], [4, 2, 0], [0, 2, 0],
            # Middle of car (bottom of windows)
            [0.5, 0.2, 1.2], [3.5, 0.2, 1.2], [3.5, 1.8, 1.2], [0.5, 1.8, 1.2],
            # Top of car
            [0.7, 0.3, 2.0], [3.3, 0.3, 2.0], [3.3, 1.7, 2.0], [0.7, 1.7, 2.0]
        ]
        
        faces = [
            # Bottom
            [0, 1, 2, 3],
            # Front
            [0, 1, 5, 4],
            # Right side
            [1, 2, 6, 5],
            # Back
            [2, 3, 7, 6],
            # Left side
            [3, 0, 4, 7],
            # Middle to top (front window)
            [4, 5, 9, 8],
            # Middle to top (right side)
            [5, 6, 10, 9],
            # Middle to top (back window)
            [6, 7, 11, 10],
            # Middle to top (left side)
            [7, 4, 8, 11],
            # Roof
            [8, 9, 10, 11]
        ]
        
        face_types = [
            "body", "body", "body", "body", "body",
            "window", "window", "window", "window", "body"
        ]
        
        return {
            "vertices": vertices,
            "faces": faces,
            "face_types": face_types
        }
    
    def _create_sports_car_mesh(self):
        """Create a sports car mesh."""
        # Sports car is lower and sleeker
        vertices = [
            # Bottom of car
            [0, 0, 0], [4, 0, 0], [4, 2, 0], [0, 2, 0],
            # Middle of car (bottom of windows)
            [0.8, 0.3, 0.8], [3.2, 0.3, 0.8], [3.2, 1.7, 0.8], [0.8, 1.7, 0.8],
            # Top of car
            [1.2, 0.5, 1.2], [2.8, 0.5, 1.2], [2.8, 1.5, 1.2], [1.2, 1.5, 1.2]
        ]
        
        faces = [
            # Bottom
            [0, 1, 2, 3],
            # Front (sloped)
            [0, 1, 5, 4],
            # Right side
            [1, 2, 6, 5],
            # Back (sloped)
            [2, 3, 7, 6],
            # Left side
            [3, 0, 4, 7],
            # Middle to top (front window)
            [4, 5, 9, 8],
            # Middle to top (right side)
            [5, 6, 10, 9],
            # Middle to top (back window)
            [6, 7, 11, 10],
            # Middle to top (left side)
            [7, 4, 8, 11],
            # Roof
            [8, 9, 10, 11]
        ]
        
        face_types = [
            "body", "body", "body", "body", "body",
            "window", "body", "window", "body", "body"
        ]
        
        return {
            "vertices": vertices,
            "faces": faces,
            "face_types": face_types
        }
    
    def _create_apple_mesh(self):
        """Create a 3D apple mesh."""
        # Create a sphere-like apple
        radius = 1.0
        
        # Create vertices for a UV sphere
        vertices = []
        stacks = 10
        slices = 12
        
        # Add top vertex
        vertices.append([0, 0, radius])
        
        # Add middle vertices
        for i in range(1, stacks):
            phi = np.pi * i / stacks
            for j in range(slices):
                theta = 2 * np.pi * j / slices
                x = radius * np.sin(phi) * np.cos(theta)
                y = radius * np.sin(phi) * np.sin(theta)
                z = radius * np.cos(phi)
                vertices.append([x, y, z])
        
        # Add bottom vertex
        vertices.append([0, 0, -radius])
        
        # Create faces
        faces = []
        face_types = []
        
        # Top faces
        for i in range(slices):
            next_i = (i + 1) % slices
            faces.append([0, i + 1, next_i + 1])
            face_types.append("body")
        
        # Middle faces
        for i in range(1, stacks - 1):
            for j in range(slices):
                next_j = (j + 1) % slices
                top_left = (i - 1) * slices + j + 1
                top_right = (i - 1) * slices + next_j + 1
                bottom_left = i * slices + j + 1
                bottom_right = i * slices + next_j + 1
                
                faces.append([top_left, bottom_left, bottom_right, top_right])
                face_types.append("body")
        
        # Bottom faces
        bottom_idx = len(vertices) - 1
        offset = (stacks - 2) * slices + 1
        for i in range(slices):
            next_i = (i + 1) % slices
            faces.append([bottom_idx, offset + next_i, offset + i])
            face_types.append("body")
        
        # Add a stem
        stem_height = 0.3
        stem_radius = 0.1
        stem_base_z = radius
        
        stem_base_idx = len(vertices)
        vertices.append([0, 0, stem_base_z])
        vertices.append([stem_radius, 0, stem_base_z + stem_height/3])
        vertices.append([0, stem_radius, stem_base_z + stem_height/3])
        vertices.append([-stem_radius, 0, stem_base_z + stem_height/3])
        vertices.append([0, -stem_radius, stem_base_z + stem_height/3])
        vertices.append([0, 0, stem_base_z + stem_height])
        
        # Stem faces
        faces.append([stem_base_idx, stem_base_idx+1, stem_base_idx+2])
        face_types.append("stem")
        faces.append([stem_base_idx, stem_base_idx+2, stem_base_idx+3])
        face_types.append("stem")
        faces.append([stem_base_idx, stem_base_idx+3, stem_base_idx+4])
        face_types.append("stem")
        faces.append([stem_base_idx, stem_base_idx+4, stem_base_idx+1])
        face_types.append("stem")
        
        faces.append([stem_base_idx+1, stem_base_idx+5, stem_base_idx+2])
        face_types.append("stem")
        faces.append([stem_base_idx+2, stem_base_idx+5, stem_base_idx+3])
        face_types.append("stem")
        faces.append([stem_base_idx+3, stem_base_idx+5, stem_base_idx+4])
        face_types.append("stem")
        faces.append([stem_base_idx+4, stem_base_idx+5, stem_base_idx+1])
        face_types.append("stem")
        
        return {
            "vertices": vertices,
            "faces": faces,
            "face_types": face_types
        }
    
    def _create_chair_mesh(self):
        """Create a 3D chair mesh."""
        # Create a simple chair
        vertices = []
        faces = []
        face_types = []
        
        # Chair dimensions
        seat_width = 1.0
        seat_depth = 1.0
        seat_height = 0.5
        leg_thickness = 0.1
        back_height = 1.0
        
        # Create seat
        seat_vertices = [
            [0, 0, seat_height], [seat_width, 0, seat_height],
            [seat_width, seat_depth, seat_height], [0, seat_depth, seat_height],
            [0, 0, seat_height + 0.1], [seat_width, 0, seat_height + 0.1],
            [seat_width, seat_depth, seat_height + 0.1], [0, seat_depth, seat_height + 0.1]
        ]
        
        vertices.extend(seat_vertices)
        
        # Seat faces
        seat_faces = [
            [0, 1, 2, 3],  # bottom
            [4, 5, 6, 7],  # top
            [0, 4, 5, 1],  # front
            [1, 5, 6, 2],  # right
            [2, 6, 7, 3],  # back
            [3, 7, 4, 0]   # left
        ]
        
        for i in range(len(seat_faces)):
            faces.append(seat_faces[i])
            face_types.append("seat")
        
        # Create legs
        leg_positions = [
            [leg_thickness/2, leg_thickness/2, 0],
            [seat_width - leg_thickness/2, leg_thickness/2, 0],
            [seat_width - leg_thickness/2, seat_depth - leg_thickness/2, 0],
            [leg_thickness/2, seat_depth - leg_thickness/2, 0]
        ]
        
        for i, pos in enumerate(leg_positions):
            leg_vertices = [
                [pos[0] - leg_thickness/2, pos[1] - leg_thickness/2, 0],
                [pos[0] + leg_thickness/2, pos[1] - leg_thickness/2, 0],
                [pos[0] + leg_thickness/2, pos[1] + leg_thickness/2, 0],
                [pos[0] - leg_thickness/2, pos[1] + leg_thickness/2, 0],
                [pos[0] - leg_thickness/2, pos[1] - leg_thickness/2, seat_height],
                [pos[0] + leg_thickness/2, pos[1] - leg_thickness/2, seat_height],
                [pos[0] + leg_thickness/2, pos[1] + leg_thickness/2, seat_height],
                [pos[0] - leg_thickness/2, pos[1] + leg_thickness/2, seat_height]
            ]
            
            leg_vertex_offset = len(vertices)
            vertices.extend(leg_vertices)
            
            leg_faces = [
                [0, 1, 2, 3],  # bottom
                [4, 5, 6, 7],  # top
                [0, 4, 5, 1],  # front
                [1, 5, 6, 2],  # right
                [2, 6, 7, 3],  # back
                [3, 7, 4, 0]   # left
            ]
            
            for j in range(len(leg_faces)):
                faces.append([x + leg_vertex_offset for x in leg_faces[j]])
                face_types.append("leg")
        
        # Create back
        back_vertices = [
            [0, seat_depth - leg_thickness/2, seat_height],
            [seat_width, seat_depth - leg_thickness/2, seat_height],
            [seat_width, seat_depth + leg_thickness/2, seat_height],
            [0, seat_depth + leg_thickness/2, seat_height],
            [0, seat_depth - leg_thickness/2, seat_height + back_height],
            [seat_width, seat_depth - leg_thickness/2, seat_height + back_height],
            [seat_width, seat_depth + leg_thickness/2, seat_height + back_height],
            [0, seat_depth + leg_thickness/2, seat_height + back_height]
        ]
        
        back_vertex_offset = len(vertices)
        vertices.extend(back_vertices)
        
        back_faces = [
            [0, 1, 2, 3],  # bottom
            [4, 5, 6, 7],  # top
            [0, 4, 5, 1],  # front
            [1, 5, 6, 2],  # right
            [2, 6, 7, 3],  # back
            [3, 7, 4, 0]   # left
        ]
        
        for i in range(len(back_faces)):
            faces.append([x + back_vertex_offset for x in back_faces[i]])
            face_types.append("back")
        
        return {
            "vertices": vertices,
            "faces": faces,
            "face_types": face_types
        }
    
    def _create_table_mesh(self):
        """Create a 3D table mesh."""
        # Create a simple table
        vertices = []
        faces = []
        face_types = []
        
        # Table dimensions
        table_width = 1.5
        table_depth = 1.0
        table_height = 0.75
        leg_thickness = 0.1
        top_thickness = 0.05
        
        # Create table top
        top_vertices = [
            [0, 0, table_height - top_thickness], 
            [table_width, 0, table_height - top_thickness],
            [table_width, table_depth, table_height - top_thickness], 
            [0, table_depth, table_height - top_thickness],
            [0, 0, table_height], 
            [table_width, 0, table_height],
            [table_width, table_depth, table_height], 
            [0, table_depth, table_height]
        ]
        
        vertices.extend(top_vertices)
        
        top_faces = [
            [0, 1, 2, 3],  # bottom
            [4, 5, 6, 7],  # top
            [0, 4, 5, 1],  # front
            [1, 5, 6, 2],  # right
            [2, 6, 7, 3],  # back
            [3, 7, 4, 0]   # left
        ]
        
        for i in range(len(top_faces)):
            faces.append(top_faces[i])
            face_types.append("top")
        
        # Create legs
        leg_positions = [
            [leg_thickness/2, leg_thickness/2, 0],
            [table_width - leg_thickness/2, leg_thickness/2, 0],
            [table_width - leg_thickness/2, table_depth - leg_thickness/2, 0],
            [leg_thickness/2, table_depth - leg_thickness/2, 0]
        ]
        
        for i, pos in enumerate(leg_positions):
            leg_vertices = [
                [pos[0] - leg_thickness/2, pos[1] - leg_thickness/2, 0],
                [pos[0] + leg_thickness/2, pos[1] - leg_thickness/2, 0],
                [pos[0] + leg_thickness/2, pos[1] + leg_thickness/2, 0],
                [pos[0] - leg_thickness/2, pos[1] + leg_thickness/2, 0],
                [pos[0] - leg_thickness/2, pos[1] - leg_thickness/2, table_height - top_thickness],
                [pos[0] + leg_thickness/2, pos[1] - leg_thickness/2, table_height - top_thickness],
                [pos[0] + leg_thickness/2, pos[1] + leg_thickness/2, table_height - top_thickness],
                [pos[0] - leg_thickness/2, pos[1] + leg_thickness/2, table_height - top_thickness]
            ]
            
            leg_vertex_offset = len(vertices)
            vertices.extend(leg_vertices)
            
            leg_faces = [
                [0, 1, 2, 3],  # bottom
                [4, 5, 6, 7],  # top
                [0, 4, 5, 1],  # front
                [1, 5, 6, 2],  # right
                [2, 6, 7, 3],  # back
                [3, 7, 4, 0]   # left
            ]
            
            for j in range(len(leg_faces)):
                faces.append([x + leg_vertex_offset for x in leg_faces[j]])
                face_types.append("leg")
        
        return {
            "vertices": vertices,
            "faces": faces,
            "face_types": face_types
        }
    
    def _create_generic_furniture_mesh(self):
        """Create a generic furniture mesh."""
        # Create a simple box
        width, depth, height = 1.0, 1.0, 1.0
        
        vertices = [
            [0, 0, 0], [width, 0, 0], [width, depth, 0], [0, depth, 0],
            [0, 0, height], [width, 0, height], [width, depth, height], [0, depth, height]
        ]
        
        faces = [
            [0, 1, 2, 3],  # bottom
            [4, 5, 6, 7],  # top
            [0, 4, 5, 1],  # front
            [1, 5, 6, 2],  # right
            [2, 6, 7, 3],  # back
            [3, 7, 4, 0]   # left
        ]
        
        face_types = ["body", "body", "body", "body", "body", "body"]
        
        return {
            "vertices": vertices,
            "faces": faces,
            "face_types": face_types
        }
    
    def _create_house_template(self):
        """Create a house template (for reference only)."""
        return "house_template"
    
    def _create_car_template(self):
        """Create a car template (for reference only)."""
        return "car_template"
    
    def _create_apple_template(self):
        """Create an apple template (for reference only)."""
        return "apple_template"
    
    def _create_chair_template(self):
        """Create a chair template (for reference only)."""
        return "chair_template"
    
    def _visualize_3d_model(self, model):
        """Create an enhanced visualization of the 3D model with clear room visibility."""
        # Create figure with multiple views for better visualization
        fig = plt.figure(figsize=(18, 12))
        
        # Main top-down view to see room layout
        ax1 = fig.add_subplot(121, projection='3d')
        
        # Determine what kind of model we have
        object_type = model.get("object_type", "house")
        
        # Set background color for better contrast
        ax1.set_facecolor('#f0f0f0')
        fig.patch.set_facecolor('#f0f0f0')
        
        # Create enhanced visualization
        if object_type == "house":
            # Draw walls with better styling
            self._visualize_house_enhanced(ax1, model)
        else:
            self._visualize_generic(ax1, model)
        
        # Set labels and title for main view
        ax1.set_xlabel('X', fontsize=12, labelpad=10)
        ax1.set_ylabel('Y', fontsize=12, labelpad=10)
        ax1.set_zlabel('Z', fontsize=12, labelpad=10)
        ax1.set_title('Top-Down View of House Interior', fontsize=16, pad=20)
        
        # Optimize view angle for seeing inside the house
        ax1.view_init(elev=50, azim=30)  # Better angle for seeing inside
        
        # Add a second view - perspective view
        ax2 = fig.add_subplot(122, projection='3d')
        ax2.set_facecolor('#f0f0f0')
        
        # Angled view to see 3D structure better
        if object_type == "house":
            self._visualize_house_enhanced(ax2, model)
        else:
            self._visualize_generic(ax2, model)
            
        ax2.set_xlabel('X', fontsize=12, labelpad=10)
        ax2.set_ylabel('Y', fontsize=12, labelpad=10)
        ax2.set_zlabel('Z', fontsize=12, labelpad=10)
        ax2.set_title('3D Perspective View', fontsize=16, pad=20)
        
        # Set a different viewing angle for the second view
        ax2.view_init(elev=25, azim=135)  # Lower angle to see 3D structure
        
        # Auto-adjust the view for both plots
        vertices = model.get("vertices", [])
        if vertices:
            all_coords = np.array(vertices)
            max_range = np.max(all_coords.max(axis=0) - all_coords.min(axis=0)) / 2.0
            
            mid_x = (all_coords[:,0].min() + all_coords[:,0].max()) / 2
            mid_y = (all_coords[:,1].min() + all_coords[:,1].max()) / 2
            mid_z = (all_coords[:,2].min() + all_coords[:,2].max()) / 2
            
            for ax in [ax1, ax2]:
                ax.set_xlim(mid_x - max_range, mid_x + max_range)
                ax.set_ylim(mid_y - max_range, mid_y + max_range)
                ax.set_zlim(mid_z - max_range*0.8, mid_z + max_range*1.2)
                
                # Turn off grid for cleaner look
                ax.grid(False)
                # Improve axis visibility
                ax.xaxis.pane.fill = False
                ax.yaxis.pane.fill = False
                ax.zaxis.pane.fill = False
        
        # Add a timestamp and title to the figure
        timestamp = "2025-07-12 19:45:42"  # Using the current timestamp provided
        plt.figtext(0.5, 0.01, f"Generated on {timestamp}", ha="center", fontsize=10)
        plt.suptitle(f"3D {object_type.capitalize()} Model", fontsize=18, y=0.98)
        
        # Add a legend for room types
        custom_lines = []
        custom_labels = []
        
        if object_type == "house":
            room_types = set()
            for room in model.get("room_meshes", []):
                room_type = room.get("type", "").lower()
                if room_type and room_type not in room_types:
                    room_types.add(room_type)
                    color = room.get("color", [0.8, 0.8, 0.8])
                    custom_lines.append(plt.Line2D([0], [0], color=color, lw=10))
                    custom_labels.append(room_type.capitalize())
        
            # Add legend to the figure
            if custom_lines:
                fig.legend(custom_lines, custom_labels, loc='upper center', 
                          bbox_to_anchor=(0.5, 0.05), ncol=len(custom_lines),
                          frameon=True, fancybox=True, shadow=True)
        
        # Add layout adjustment
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # Save to file with higher DPI for better quality
        output_path = 'output/3d_model.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        return output_path

    def _visualize_house_enhanced(self, ax, model):
        """Enhanced visualization for house models with better styling."""
        # First draw floors (bottom layer)
        self._draw_floors(ax, model)
        
        # Then draw walls (middle layer)
        self._draw_walls(ax, model)
        
        # Draw furniture (top layer)
        self._draw_furniture_enhanced(ax, model)
        
        # Add room labels with better styling
        self._add_room_labels(ax, model)

    def _draw_floors(self, ax, model):
        """Draw room floors with distinct colors and patterns."""
        for room_idx, room_mesh in enumerate(model.get("room_meshes", [])):
            vertex_start = room_mesh["vertex_start"]
            vertex_count = room_mesh["vertex_count"]
            face_start = room_mesh["face_start"]
            face_count = room_mesh["face_count"]
            room_color = room_mesh.get("color", [0.8, 0.8, 0.8])
            
            # Get room vertices
            room_vertices = model["vertices"][vertex_start:vertex_start+vertex_count]
            
            # Draw only the floor face
            for i in range(face_count):
                face_idx = face_start + i
                if face_idx >= len(model["faces"]):
                    continue
                    
                face = model["faces"][face_idx]
                
                # Skip if face is invalid
                if not face or max(face) >= len(model["vertices"]):
                    continue
                
                # Get the vertices for this face
                face_vertices = [model["vertices"][idx] for idx in face]
                
                # Check if this is a floor face
                z_coords = [v[2] for v in face_vertices]
                is_horizontal = max(z_coords) - min(z_coords) < 0.1
                is_bottom = np.mean(z_coords) < 0.1
                
                if is_horizontal and is_bottom:  # It's a floor
                    # Make the floor slightly darker
                    floor_color = [c * 0.85 for c in room_color]
                    
                    # Draw floor with slight transparency
                    poly = Poly3DCollection([face_vertices], alpha=0.95)
                    poly.set_facecolor(floor_color)
                    poly.set_edgecolor('black')
                    poly.set_linewidth(0.5)
                    ax.add_collection3d(poly)

    def _draw_walls(self, ax, model):
        """Draw walls with enhanced styling."""
        for room_idx, room_mesh in enumerate(model.get("room_meshes", [])):
            vertex_start = room_mesh["vertex_start"]
            vertex_count = room_mesh["vertex_count"]
            face_start = room_mesh["face_start"]
            face_count = room_mesh["face_count"]
            room_color = room_mesh.get("color", [0.8, 0.8, 0.8])
            
            # Get faces for this room
            for i in range(face_count):
                face_idx = face_start + i
                if face_idx >= len(model["faces"]):
                    continue
                    
                face = model["faces"][face_idx]
                
                # Skip if face is invalid
                if not face or max(face) >= len(model["vertices"]):
                    continue
                
                # Get the vertices for this face
                face_vertices = [model["vertices"][idx] for idx in face]
                
                # Check what type of face this is
                z_coords = [v[2] for v in face_vertices]
                is_horizontal = max(z_coords) - min(z_coords) < 0.1
                avg_z = np.mean(z_coords)
                
                # Skip ceilings (top horizontal faces)
                if is_horizontal and avg_z > 2.5:  # Ceiling height check
                    continue
                    
                # Skip floors (already drawn)
                if is_horizontal and avg_z < 0.1:  # Floor height check
                    continue
                    
                # This must be a wall - draw it semi-transparent
                # Adjust color based on which wall it is (for visual distinction)
                x_coords = [v[0] for v in face_vertices]
                y_coords = [v[1] for v in face_vertices]
                
                # Determine if it's an outer wall or inner wall
                wall_color = room_color.copy()
                
                # Use original color but with transparency for walls
                poly = Poly3DCollection([face_vertices], alpha=0.7)
                poly.set_facecolor(wall_color)
                poly.set_edgecolor('black')
                poly.set_linewidth(1)
                ax.add_collection3d(poly)

    def _draw_furniture_enhanced(self, ax, model):
        """Draw furniture with enhanced styling."""
        for furniture in model.get("furniture", []):
            if "position" in furniture and "dimensions" in furniture:
                pos = furniture["position"]
                dim = furniture["dimensions"]
                color = furniture.get("color", [0.5, 0.5, 0.5])
                furniture_type = furniture.get("type", "").lower()
                
                # Skip roof and foundation for visualization
                if furniture_type in ["roof", "foundation"]:
                    continue
                
                # Get position and dimensions
                x, y, z = pos
                w, d, h = dim
                
                # Darken the color slightly for furniture
                furniture_color = [max(0, c * 0.9) for c in color]
                
                # Draw based on furniture type for more realistic visualization
                if "bed" in furniture_type:
                    self._draw_bed(ax, x, y, z, w, d, h, furniture_color)
                elif "counter" in furniture_type or "kitchen" in furniture_type:
                    self._draw_counter(ax, x, y, z, w, d, h, furniture_color)
                elif "table" in furniture_type:
                    self._draw_table(ax, x, y, z, w, d, h, furniture_color)
                elif "sofa" in furniture_type:
                    self._draw_sofa(ax, x, y, z, w, d, h, furniture_color)
                else:
                    # Generic furniture as a box
                    self._draw_box(ax, x, y, z, w, d, h, furniture_color)
                
                # Add small label for furniture
                label_pos = [x + w/2, y + d/2, z + h + 0.1]
                if h > 0.3:  # Only label larger furniture
                    ax.text(label_pos[0], label_pos[1], label_pos[2], 
                           furniture_type.replace('_', ' '), fontsize=8, 
                           color='black', ha='center', va='bottom')

    def _draw_box(self, ax, x, y, z, w, d, h, color):
        """Draw a simple box for generic furniture."""
        # Define vertices
        vertices = [
            [x, y, z], [x+w, y, z], [x+w, y+d, z], [x, y+d, z],
            [x, y, z+h], [x+w, y, z+h], [x+w, y+d, z+h], [x, y+d, z+h]
        ]
        
        # Define faces
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
            [vertices[1], vertices[2], vertices[6], vertices[5]],  # right
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
            [vertices[3], vertices[0], vertices[4], vertices[7]]   # left
        ]
        
        # Draw each face
        for face in faces:
            poly = Poly3DCollection([face], alpha=0.9)
            poly.set_facecolor(color)
            poly.set_edgecolor('black')
            poly.set_linewidth(0.5)
            ax.add_collection3d(poly)

    def _draw_bed(self, ax, x, y, z, w, d, h, color):
        """Draw a bed with more detailed styling."""
        # Base/frame - slightly larger than mattress
        frame_extend = 0.1
        frame_height = h * 0.3
        
        # Draw bed frame
        frame_color = [c * 0.8 for c in color]  # Darker color for frame
        self._draw_box(ax, x-frame_extend, y-frame_extend, z, 
                      w+2*frame_extend, d+2*frame_extend, frame_height, frame_color)
        
        # Draw mattress
        mattress_color = [0.9, 0.9, 0.95]  # Off-white for mattress
        self._draw_box(ax, x, y, z+frame_height, w, d, h-frame_height, mattress_color)
        
        # Draw pillow
        pillow_width = w * 0.8
        pillow_depth = d * 0.2
        pillow_height = (h - frame_height) * 0.3
        pillow_x = x + (w - pillow_width) / 2
        pillow_y = y + d - pillow_depth - 0.05
        pillow_z = z + frame_height + (h - frame_height) - pillow_height
        
        pillow_color = [0.95, 0.95, 1.0]  # White for pillow
        self._draw_box(ax, pillow_x, pillow_y, pillow_z, 
                      pillow_width, pillow_depth, pillow_height, pillow_color)

    def _draw_counter(self, ax, x, y, z, w, d, h, color):
        """Draw a kitchen counter with more detail."""
        # Base cabinet
        base_height = h * 0.9
        cabinet_color = color
        self._draw_box(ax, x, y, z, w, d, base_height, cabinet_color)
        
        # Counter top - slightly wider than base
        extend = 0.02
        counter_color = [0.9, 0.9, 0.9]  # Light gray for counter
        self._draw_box(ax, x-extend, y-extend, z+base_height, 
                      w+2*extend, d+2*extend, h-base_height, counter_color)

    def _draw_sofa(self, ax, x, y, z, w, d, h, color):
        """Draw a sofa with more detail."""
        # Base
        base_height = h * 0.3
        self._draw_box(ax, x, y, z, w, d, base_height, color)
        
        # Back cushion - taller part at the back
        back_depth = d * 0.2
        back_height = h - base_height
        self._draw_box(ax, x, y, z+base_height, w, back_depth, back_height, color)
        
        # Seat cushion
        seat_height = h * 0.2
        cushion_color = [min(1.0, c * 1.1) for c in color]  # Slightly lighter
        self._draw_box(ax, x, y+back_depth, z+base_height, w, d-back_depth, seat_height, cushion_color)

    def _draw_table(self, ax, x, y, z, w, d, h, color):
        """Draw a table with more detail."""
        # Table top
        top_height = h * 0.1
        top_z = z + h - top_height
        self._draw_box(ax, x, y, top_z, w, d, top_height, color)
        
        # Table legs
        leg_width = 0.1
        leg_locations = [
            [x, y], 
            [x+w-leg_width, y],
            [x, y+d-leg_width],
            [x+w-leg_width, y+d-leg_width]
        ]
        
        for leg_pos in leg_locations:
            self._draw_box(ax, leg_pos[0], leg_pos[1], z, leg_width, leg_width, h-top_height, color)

    def _add_room_labels(self, ax, model):
        """Add clear room labels with better styling."""
        for room_idx, room_mesh in enumerate(model.get("room_meshes", [])):
            vertex_start = room_mesh["vertex_start"]
            vertex_count = room_mesh["vertex_count"]
            
            # Get room center
            room_vertices = model["vertices"][vertex_start:vertex_start+vertex_count]
            room_center = np.mean(room_vertices, axis=0)
            
            # Get room type and prepare label
            room_type = room_mesh.get("type", "")
            room_name = str(room_mesh.get("name", f"Room {room_idx}"))
            
            # Make label more descriptive
            if room_type:
                label = f"{room_type.upper()}"
            else:
                label = room_name
                
            # Position label in the center of the room but higher up
            label_pos = [room_center[0], room_center[1], room_center[2] + 1.0]
            
            # Add text with better visibility - larger font and background
            ax.text(label_pos[0], label_pos[1], label_pos[2], label,
                  fontsize=12, fontweight='bold', color='black', ha='center', va='center',
                  bbox=dict(facecolor='white', alpha=0.7, edgecolor='black', boxstyle='round,pad=0.5'))

    def _visualize_car(self, ax, model):
        """Visualize a car model."""
        self._visualize_mesh(ax, model)
    
    def _visualize_fruit(self, ax, model):
        """Visualize a fruit model."""
        self._visualize_mesh(ax, model)
    
    def _visualize_furniture(self, ax, model):
        """Visualize furniture."""
        self._visualize_mesh(ax, model)
    
    def _visualize_generic(self, ax, model):
        """Visualize a generic model."""
        self._visualize_mesh(ax, model)
    
    def _visualize_mesh(self, ax, model):
        """Visualize a mesh model with colored faces."""
        vertices = model.get("vertices", [])
        faces = model.get("faces", [])
        colors = model.get("colors", [])
        
        # Default color if none provided
        default_color = model.get("primary_color", [0.7, 0.7, 0.7])
        
        # Draw each face
        for i, face in enumerate(faces):
            # Get the vertices for this face
            face_vertices = [vertices[idx] for idx in face]
            
            # Use color if available
            if i < len(colors):
                color = colors[i]
            else:
                color = default_color
            
            # Draw face
            poly = Poly3DCollection([face_vertices], alpha=0.7)
            poly.set_facecolor(color)
            poly.set_edgecolor('black')
            poly.set_linewidth(0.5)
            ax.add_collection3d(poly)
    
    def export_obj(self, model, filename):
        """Export the 3D model to OBJ format with enhanced materials."""
        start_time = time.time()
        print(f"Exporting 3D model to {filename}...")
        
        # Create an OBJ exporter that adds materials
        with open(filename, 'w') as f:
            # Write OBJ header with current date
            timestamp = "2025-07-12 19:50:26"  # Using the provided timestamp
            f.write("# Generated by Text-to-3D Model Generator\n")
            f.write(f"# Date: {timestamp}\n\n")
            
            # Reference MTL file
            mtl_filename = filename.replace('.obj', '.mtl')
            base_mtl = os.path.basename(mtl_filename)
            f.write(f"mtllib {base_mtl}\n\n")
            
            # Write vertices (v x y z)
            for vertex in model["vertices"]:
                f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
            
            f.write("\n# Faces\n")
            
            # Different export based on object type
            object_type = model.get("object_type", "house")
            
            if object_type == "house":
                self._export_house_obj(f, model)
            else:
                self._export_generic_obj(f, model)
        
        # Create MTL file with materials
        with open(mtl_filename, 'w') as f:
            f.write("# Material file for 3D model\n\n")
            
            # Object-type specific material export
            if object_type == "house":
                self._export_house_mtl(f, model)
            else:
                self._export_generic_mtl(f, model)
        
        # Also export to GLB format if possible
        try:
            glb_filename = filename.replace('.obj', '.glb')
            self.export_glb(model, glb_filename)
        except Exception as e:
            print(f"Note: GLB export skipped - {e}")
        
        print(f"Model exported successfully in {time.time() - start_time:.2f} seconds")
        return True
    
    def _export_house_obj(self, f, model):
        """Export house-specific OBJ content."""
        # Write room groups and their faces
        for room_idx, room in enumerate(model["room_meshes"]):
            # Fix: Convert room name to string if it's not already
            if "name" in room:
                # Ensure name is a string and replace spaces with underscores
                room_name = str(room["name"]).replace(" ", "_")
            else:
                room_name = f"room_{room_idx}"
            
            f.write(f"\ng {room_name}\n")
            f.write(f"usemtl room_{room_idx}\n")
            
            # Write faces for this room
            for i in range(room["face_count"]):
                face_idx = room["face_start"] + i
                if face_idx < len(model["faces"]):
                    face = model["faces"][face_idx]
                    face_str = " ".join([f"{idx + 1}" for idx in face])
                    f.write(f"f {face_str}\n")
            
            f.write("\n")
        
        # Write furniture
        vertex_offset = len(model["vertices"])
        
        for i, furniture in enumerate(model["furniture"]):
            if "position" not in furniture or "dimensions" not in furniture:
                continue
                
            pos = furniture["position"]
            dim = furniture["dimensions"]
            ftype = furniture["type"]
            
            f.write(f"\ng furniture_{i}_{ftype}\n")
            f.write(f"usemtl furniture_{i}\n")
            
            x, y, z = pos
            w, d, h = dim
            
            # Define furniture vertices
            furniture_vertices = [
                [x, y, z], [x+w, y, z], [x+w, y+d, z], [x, y+d, z],
                [x, y, z+h], [x+w, y, z+h], [x+w, y+d, z+h], [x, y+d, z+h]
            ]
            
            # Write vertices
            for v in furniture_vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            
            # Calculate base index for this furniture
            base_idx = vertex_offset + i * 8 + 1  # OBJ is 1-indexed
            
            # Define faces
            f.write(f"f {base_idx} {base_idx+1} {base_idx+2} {base_idx+3}\n")  # bottom
            f.write(f"f {base_idx+4} {base_idx+5} {base_idx+6} {base_idx+7}\n")  # top
            f.write(f"f {base_idx} {base_idx+1} {base_idx+5} {base_idx+4}\n")  # front
            f.write(f"f {base_idx+1} {base_idx+2} {base_idx+6} {base_idx+5}\n")  # right
            f.write(f"f {base_idx+2} {base_idx+3} {base_idx+7} {base_idx+6}\n")  # back
            f.write(f"f {base_idx+3} {base_idx} {base_idx+4} {base_idx+7}\n")  # left
            
            f.write("\n")
    
    def _export_generic_obj(self, f, model):
        """Export generic OBJ content."""
        # Write all faces with a single material
        f.write("g model\n")
        f.write("usemtl material_0\n")
        
        for face in model["faces"]:
            face_str = " ".join([f"{idx + 1}" for idx in face])
            f.write(f"f {face_str}\n")
    
    def _export_house_mtl(self, f, model):
        """Export house-specific MTL content."""
        # Materials for rooms
        for i, room in enumerate(model["room_meshes"]):
            color = room.get("color", [0.8, 0.8, 0.8])
            f.write(f"newmtl room_{i}\n")
            f.write(f"Ka {color[0]} {color[1]} {color[2]}\n")
            f.write(f"Kd {color[0]} {color[1]} {color[2]}\n")
            f.write("Ks 0.1 0.1 0.1\n")
            f.write("illum 2\n")
            f.write("Ns 10.0\n\n")
        
        # Materials for furniture
        for i, furniture in enumerate(model["furniture"]):
            if "color" in furniture:
                color = furniture["color"]
                f.write(f"newmtl furniture_{i}\n")
                f.write(f"Ka {color[0]} {color[1]} {color[2]}\n")
                f.write(f"Kd {color[0]} {color[1]} {color[2]}\n")
                f.write("Ks 0.2 0.2 0.2\n")
                f.write("illum 2\n")
                f.write("Ns 20.0\n\n")
    
    def _export_generic_mtl(self, f, model):
        """Export generic MTL content."""
        # Use primary color if available
        primary_color = model.get("primary_color", [0.7, 0.7, 0.7])
        
        f.write("newmtl material_0\n")
        f.write(f"Ka {primary_color[0]} {primary_color[1]} {primary_color[2]}\n")
        f.write(f"Kd {primary_color[0]} {primary_color[1]} {primary_color[2]}\n")
        f.write("Ks 0.2 0.2 0.2\n")
        f.write("illum 2\n")
        f.write("Ns 10.0\n")
    
    def export_glb(self, model, filename):
        """Export the 3D model to GLB format."""
        try:
            import trimesh
            
            print(f"Exporting GLB format to {filename}...")
            
            # Create a scene with meshes
            meshes = []
            
            # Process model based on type
            object_type = model.get("object_type", "house")
            
            if object_type == "house":
                # Process each room
                for room_idx, room in enumerate(model["room_meshes"]):
                    # Get room data
                    vertex_start = room["vertex_start"]
                    vertex_count = room["vertex_count"]
                    face_start = room["face_start"]
                    face_count = room["face_count"]
                    color = np.array(room.get("color", [0.8, 0.8, 0.8]) + [1.0]) * 255
                    
                    # Extract room vertices
                    room_vertices = np.array(model["vertices"][vertex_start:vertex_start+vertex_count])
                    
                    # Extract and convert room faces to triangles
                    room_faces = []
                    for i in range(face_count):
                        face_idx = face_start + i
                        if face_idx < len(model["faces"]):
                            face = model["faces"][face_idx]
                            # Adjust indices for this subset of vertices
                            adjusted_face = [idx - vertex_start for idx in face]
                            
                            # Convert quad to triangles
                            if len(adjusted_face) == 4:
                                room_faces.append([adjusted_face[0], adjusted_face[1], adjusted_face[2]])
                                room_faces.append([adjusted_face[0], adjusted_face[2], adjusted_face[3]])
                            elif len(adjusted_face) == 3:
                                room_faces.append(adjusted_face)
                    
                    # Create mesh for this room if we have faces
                    if room_faces and len(room_vertices) > 0:
                        try:
                            room_faces_array = np.array(room_faces)
                            
                            # Create the trimesh with the room data
                            room_mesh = trimesh.Trimesh(
                                vertices=room_vertices,
                                faces=room_faces_array,
                                process=False
                            )
                            
                            # Set the color for all faces
                            face_colors = np.tile(color, (len(room_faces), 1))
                            room_mesh.visual.face_colors = face_colors.astype(np.uint8)
                            
                            # Add metadata for this room
                            room_mesh.metadata = {
                                'name': str(room.get("name", f"room_{room_idx}")),
                                'type': str(room.get("type", "room"))
                            }
                            
                            # Add to meshes list
                            meshes.append(room_mesh)
                        except Exception as e:
                            print(f"Warning: Could not create mesh for room {room_idx}: {e}")
                
                # Add furniture
                for furn_idx, furniture in enumerate(model["furniture"]):
                    if "position" not in furniture or "dimensions" not in furniture:
                        continue
                        
                    pos = furniture["position"]
                    dim = furniture["dimensions"]
                    color = np.array(furniture.get("color", [0.5, 0.5, 0.5]) + [1.0]) * 255
                    ftype = furniture["type"]
                    
                    # Skip roof for visualization
                    if ftype == "roof":
                        continue
                    
                    # Create box for furniture
                    try:
                        # Create a box at origin
                        furniture_mesh = trimesh.creation.box(extents=dim)
                        
                        # Move to correct position (trimesh centers the box on the extents)
                        translation = [
                            pos[0] + dim[0]/2,  # X center
                            pos[1] + dim[1]/2,  # Y center
                            pos[2] + dim[2]/2   # Z center
                        ]
                        furniture_mesh.apply_translation(translation)
                        
                        # Set color for all faces
                        furniture_mesh.visual.face_colors = np.tile(
                            color.astype(np.uint8),
                            (len(furniture_mesh.faces), 1)
                        )
                        
                        # Add to meshes
                        meshes.append(furniture_mesh)
                    except Exception as e:
                        print(f"Warning: Could not create furniture {ftype}: {e}")
            
            else:
                # Generic object - create a single mesh
                vertices = np.array(model["vertices"])
                faces_list = []
                
                # Convert all faces to triangles
                for face in model["faces"]:
                    if len(face) == 4:  # Quad
                        faces_list.append([face[0], face[1], face[2]])
                        faces_list.append([face[0], face[2], face[3]])
                    elif len(face) == 3:  # Triangle
                        faces_list.append(face)
                
                if len(faces_list) > 0:
                    faces = np.array(faces_list)
                    
                    # Create the mesh
                    mesh = trimesh.Trimesh(
                        vertices=vertices,
                        faces=faces,
                        process=False
                    )
                    
                    # Set colors
                    if model.get("colors"):
                        # Duplicate colors for triangulated faces
                        colors = []
                        for i, face in enumerate(model["faces"]):
                            if i < len(model["colors"]):
                                color = model["colors"][i]
                                if len(face) == 4:  # Quad became 2 triangles
                                    colors.append(color + [1.0])
                                    colors.append(color + [1.0])
                                elif len(face) == 3:  # Triangle
                                    colors.append(color + [1.0])
                        
                        # Set face colors
                        if colors:
                            color_array = np.array(colors) * 255
                            mesh.visual.face_colors = color_array.astype(np.uint8)
                    else:
                        # Use primary color
                        primary_color = model.get("primary_color", [0.7, 0.7, 0.7])
                        color_array = np.tile(
                            np.array(primary_color + [1.0]) * 255,
                            (len(mesh.faces), 1)
                        )
                        mesh.visual.face_colors = color_array.astype(np.uint8)
                    
                    meshes.append(mesh)
            
            # Create scene and export
            if meshes:
                # Create a scene with all meshes
                scene = trimesh.Scene()
                
                # Add each mesh to the scene
                for i, mesh in enumerate(meshes):
                    scene.add_geometry(mesh, node_name=f"mesh_{i}")
                
                # Set export options for proper compatibility with viewers
                export_options = {
                    'include_normals': True,
                    'include_metadata': True
                }
                
                # Export to GLB format
                success = scene.export(filename, file_type='glb', **export_options)
                
                if success:
                    print(f"GLB export successful: {filename}")
                    return True
                else:
                    print("GLB export failed")
                    return False
            else:
                print("Warning: No meshes to export")
                return False
                
        except ImportError as e:
            print(f"GLB export requires trimesh: {e}")
            return False
        except Exception as e:
            print(f"Error exporting GLB: {e}")
            return False