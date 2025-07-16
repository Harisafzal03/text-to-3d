#!/usr/bin/env python3
"""
3D Model Builder
---------------
Converts 2D layouts to 3D models with proper doors and movement space.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patches as patches
from matplotlib.path import Path
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
        
        # Set standard measurements
        self.wall_height = 3.0  # 3 meters
        self.floor_thickness = 0.3  # 30cm
        self.door_height = 2.1  # Standard door height 2.1m
        self.door_width = 0.9  # Standard door width 0.9m
        self.window_height = 1.2  # Window height
        self.window_width = 1.0  # Window width
        self.window_sill = 1.0  # Window sill height
        
        # Pakistani land measurements conversions
        self.marla_to_sqm = 25.2929  # 1 Marla = 25.2929 square meters
        self.kanal_to_marla = 20     # 1 Kanal = 20 Marla
        
        # Room relation constraints
        self.room_constraints = {
            "kitchen": ["washroom", "bathroom"],  # Kitchen shouldn't be next to washrooms
            "bedroom": [],  # No special constraints for bedrooms
            "washroom": ["kitchen"],  # Washrooms shouldn't be next to kitchen
            "bathroom": ["kitchen"],  # Bathrooms shouldn't be next to kitchen
        }
        
    def generate_3d_model(self, layout):
        """Generate a 3D model from a layout."""
        start_time = time.time()
        print("Building detailed 3D model...")
        
        # Determine what kind of object we're building
        object_type = layout.get("object_type", "house")
        
        # Use the appropriate builder for the object type
        if object_type == "house":
            model = self._build_house_model(layout)
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
            "doors": model.get("doors", []),
            "colors": {},
            "plot_size": model.get("plot_size", {}),
            "stories": model.get("stories", 1)
        }
        
        # Add room information
        for room in model.get("room_meshes", []):
            room_info = {
                "type": room["type"],
                "name": str(room["name"]),
                "color": room.get("color"),
                "story": room.get("story", 1)
            }
            info["rooms"].append(room_info)
        
        # Save the file
        with open('output/model_info.json', 'w') as f:
            json.dump(info, f, indent=2)
    
    def _build_house_model(self, layout):
        """Build a 3D house model from the layout with doors and windows."""
        rooms = layout.get("rooms", [])
        doors = layout.get("doors", [])
        
        # Get plot size in Pakistani units if available
        plot_size = layout.get("plot_size", {})
        if not plot_size:
            # Calculate from the layout size
            max_x = max([r["position"][0] + r["size"][0] for r in rooms]) if rooms else 10
            max_y = max([r["position"][1] + r["size"][1] for r in rooms]) if rooms else 10
            area_sqm = max_x * max_y
            area_marla = area_sqm / self.marla_to_sqm
            
            plot_size = {
                "marla": area_marla,
                "kanal": area_marla / self.kanal_to_marla,
                "width_meters": max_x,
                "length_meters": max_y
            }
        
        # Get number of stories
        stories = layout.get("stories", 1)
        
        # Initialize 3D model structure
        model = {
            "object_type": "house",
            "vertices": [],
            "faces": [],
            "face_types": [],  # Type of each face (wall, floor, ceiling, door, window)
            "colors": [],  # Color data
            "room_meshes": [],
            "furniture": [],
            "doors": [],
            "windows": [],
            "stairs": [],
            "layout": layout,  # Store original layout for reference
            "plot_size": plot_size,
            "stories": stories
        }
        
        vertex_offset = 0
        
        # Scale factor to convert from grid coordinates to 3D world coordinates
        scale = 1.0
        
        # Process each story
        for story in range(1, stories + 1):
            # Filter rooms for this story
            story_rooms = [r for r in rooms if r.get("story", 1) == story]
            
            # Adjust floor height based on story
            floor_z_offset = (story - 1) * (self.wall_height + self.floor_thickness)
            
            # Convert each room to a 3D box with distinct colors
            for room in story_rooms:
                room_type = room["type"].lower()
                x, y = room["position"]
                width, height = room["size"]
                
                # Generate a vibrant color for this room based on type
                room_color = self._get_vibrant_room_color(room_type)
                
                # Create 3D mesh for this room
                room_mesh = self._create_detailed_room(
                    x, y, width, height, 
                    self.wall_height, 
                    scale,
                    room_type,
                    floor_z_offset
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
                model["face_types"].extend(room_mesh["face_types"])
                
                # Add colors for each face
                for face_type in room_mesh["face_types"]:
                    if face_type == "floor":
                        model["colors"].append([0.9, 0.9, 0.9])  # Light gray for floor
                    elif face_type == "ceiling":
                        model["colors"].append([0.95, 0.95, 0.95])  # White for ceiling
                    else:  # wall
                        model["colors"].append(room_color)  # Room color for walls
                
                # Store room information
                room_data = {
                    "id": room.get("id", f"{room_type}_{len(model['room_meshes'])}"),
                    "type": room_type,
                    "name": str(room.get("name", room_type)),
                    "vertex_start": vertex_offset,
                    "vertex_count": len(room_mesh["vertices"]),
                    "face_start": len(model["faces"]) - len(room_mesh["faces"]),
                    "face_count": len(room_mesh["faces"]),
                    "color": room_color,
                    "story": story,
                    "position": [x, y],
                    "size": [width, height]
                }
                model["room_meshes"].append(room_data)
                
                # Update vertex offset for the next room
                vertex_offset += len(room_mesh["vertices"])
                
                # Add appropriate furniture based on room type, leaving space for movement
                furniture = self._add_room_furniture(room_type, x, y, width, height, self.wall_height, floor_z_offset)
                if furniture:
                    model["furniture"].extend(furniture)
        
        # Add doors between rooms
        model = self._add_doors_to_model(model, layout)
        
        # Add windows to exterior walls
        model = self._add_windows_to_model(model, layout)
        
        # Add staircases if more than one story
        model = self._add_staircases_to_model(model, layout)
        
        # Add a floor and ceiling to the entire house
        model = self._add_house_exterior(model)
        
        return model
    
    def _build_generic_model(self, layout):
        """Build a generic 3D model."""
        # Get plot size in Pakistani units if available
        plot_size = layout.get("plot_size", {
            "marla": 5,
            "kanal": 0.25,
            "width_meters": 10,
            "length_meters": 12.5
        })
        
        # Get number of stories
        stories = layout.get("stories", 1)
        
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
            "face_types": [],
            "primary_color": primary_color,
            "plot_size": plot_size,
            "stories": stories
        }
        
        # Create a simple box mesh
        box_mesh = {
            "vertices": [
                [0, 0, 0], [10, 0, 0], [10, 12.5, 0], [0, 12.5, 0],
                [0, 0, 3], [10, 0, 3], [10, 12.5, 3], [0, 12.5, 3]
            ],
            "faces": [
                [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
                [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]
            ],
            "face_types": ["floor", "ceiling", "wall", "wall", "wall", "wall"]
        }
        
        # Add vertices and faces to the model
        model["vertices"].extend(box_mesh["vertices"])
        model["faces"].extend(box_mesh["faces"])
        model["face_types"].extend(box_mesh["face_types"])
        
        # Add colors based on face type
        for face_type in box_mesh["face_types"]:
            if face_type == "floor":
                model["colors"].append([0.9, 0.9, 0.9])  # Light gray for floor
            elif face_type == "ceiling":
                model["colors"].append([0.95, 0.95, 0.95])  # White for ceiling
            else:  # wall
                model["colors"].append(primary_color)
        
        return model
    
    def _create_detailed_room(self, x, y, width, height, wall_height, scale, room_type, z_offset=0):
        """Create a detailed 3D mesh for a room."""
        # Scale the coordinates
        x1, y1 = x * scale, y * scale
        x2, y2 = (x + width) * scale, (y + height) * scale
        z1, z2 = z_offset, z_offset + wall_height
        
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
            [0, 1, 5, 4],  # Wall 1 (front)
            [1, 2, 6, 5],  # Wall 2 (right)
            [2, 3, 7, 6],  # Wall 3 (back)
            [3, 0, 4, 7]   # Wall 4 (left)
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
            "washroom": [0.5, 0.9, 0.6],      # Light green
            "living room": [1.0, 0.9, 0.5],   # Vibrant yellow
            "tv lounge": [1.0, 0.7, 0.4],     # Vibrant orange
            "lobby": [0.9, 0.8, 0.5],         # Light orange/tan
            "hallway": [0.9, 0.8, 0.7],       # Beige
            "entrance": [0.8, 0.8, 0.6],      # Light brown
            "main entrance": [0.8, 0.7, 0.5], # Tan
            "terrace": [0.7, 0.9, 0.8],       # Mint green
            "garage": [0.6, 0.6, 0.7],        # Gray-blue
            "car parking": [0.7, 0.7, 0.8],   # Light purple-gray
            "stairs": [0.8, 0.8, 0.9],        # Light blue-gray
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
    
    def _add_room_furniture(self, room_type, x, y, width, height, wall_height, z_offset=0):
        """Add appropriate furniture based on room type, with space for movement."""
        furniture = []
        
        # Calculate movement corridor size - central area that should remain empty for movement
        corridor_width = min(width * 0.4, 1.2)  # Max 1.2m wide corridor 
        corridor_height = min(height * 0.4, 1.2)  # Max 1.2m high corridor
        
        # Determine furniture placement zones - avoiding the central movement area
        zones = {
            "top": {
                "x": x + width/2 - corridor_width/2,
                "y": y + height * 0.75,
                "width": corridor_width,
                "height": height * 0.2
            },
            "bottom": {
                "x": x + width/2 - corridor_width/2,
                "y": y + height * 0.05,
                "width": corridor_width,
                "height": height * 0.2
            },
            "left": {
                "x": x + width * 0.05,
                "y": y + height/2 - corridor_height/2,
                "width": width * 0.2,
                "height": corridor_height
            },
            "right": {
                "x": x + width * 0.75,
                "y": y + height/2 - corridor_height/2,
                "width": width * 0.2,
                "height": corridor_height
            }
        }
        
        # Base height for furniture
        base_z = z_offset
        
        if "bedroom" in room_type:
            # Add a bed - placed against one wall to maximize space
            bed_width = width * 0.5
            bed_height = height * 0.4
            
            # Place bed against top wall
            bed = self._create_furniture(
                "bed",
                x + width/2 - bed_width/2,
                y + height - bed_height - 0.1,
                bed_width,
                bed_height,
                0.5,  # height
                [0.6, 0.4, 0.2],  # brown
                base_z
            )
            furniture.append(bed)
            
            # Add a nightstand next to bed
            ns_width = width * 0.15
            ns_height = height * 0.15
            
            nightstand = self._create_furniture(
                "nightstand",
                x + width * 0.05,
                y + height - ns_height - 0.15,
                ns_width,
                ns_height,
                0.6,
                [0.5, 0.35, 0.2],  # darker brown
                base_z
            )
            furniture.append(nightstand)
            
            # Add dresser on opposite wall
            dresser = self._create_furniture(
                "dresser",
                x + width * 0.7,
                y + height * 0.1,
                width * 0.25,
                height * 0.15,
                1.0,
                [0.65, 0.5, 0.4],  # medium brown
                base_z
            )
            furniture.append(dresser)
            
        elif "kitchen" in room_type:
            # Add kitchen counter along the back wall
            counter1 = self._create_furniture(
                "kitchen_counter",
                x + width * 0.1,
                y + height * 0.8,
                width * 0.8,
                height * 0.15,
                0.9,
                [0.9, 0.9, 0.9],  # white/gray
                base_z
            )
            furniture.append(counter1)
            
            # Add a second counter along a side wall
            counter2 = self._create_furniture(
                "kitchen_counter",
                x + width * 0.1,
                y + height * 0.1,
                width * 0.15,
                height * 0.7,
                0.9,
                [0.9, 0.9, 0.9],  # white/gray
                base_z
            )
            furniture.append(counter2)
            
            # Add a small table
            if width * height > 15:  # Only in larger kitchens
                table = self._create_furniture(
                    "dining_table",
                    x + width * 0.6,
                    y + height * 0.4,
                    width * 0.25,
                    height * 0.25,
                    0.8,
                    [0.8, 0.6, 0.4],  # wood color
                    base_z
                )
                furniture.append(table)
            
        elif "living" in room_type or "tv lounge" in room_type:
            # Add a sofa along the back wall
            sofa = self._create_furniture(
                "sofa",
                x + width * 0.1,
                y + height * 0.75,
                width * 0.6,
                height * 0.2,
                0.8,
                [0.3, 0.3, 0.7],  # blue
                base_z
            )
            furniture.append(sofa)
            
            # Add a TV stand on opposite wall
            tv = self._create_furniture(
                "tv_stand",
                x + width * 0.3,
                y + height * 0.05,
                width * 0.4,
                height * 0.1,
                0.5,
                [0.2, 0.2, 0.2],  # black
                base_z
            )
            furniture.append(tv)
            
            # Add a coffee table in the center
            table = self._create_furniture(
                "coffee_table",
                x + width * 0.35,
                y + height * 0.4,
                width * 0.3,
                height * 0.15,
                0.4,
                [0.7, 0.5, 0.3],  # wood color
                base_z
            )
            furniture.append(table)
            
        elif "bathroom" in room_type or "washroom" in room_type:
            # Add toilet against a wall
            toilet = self._create_furniture(
                "toilet",
                x + width * 0.1,
                y + height * 0.1,
                width * 0.25,
                height * 0.25,
                0.4,
                [0.9, 0.9, 0.9],  # white
                base_z
            )
            furniture.append(toilet)
            
            # Add sink 
            sink = self._create_furniture(
                "sink",
                x + width * 0.6,
                y + height * 0.1,
                width * 0.3,
                height * 0.2,
                0.8,
                [0.9, 0.9, 0.9],  # white
                base_z
            )
            furniture.append(sink)
            
            # Add shower in larger bathrooms
            if width * height > 5:  # If bathroom is large enough
                shower = self._create_furniture(
                    "shower",
                    x + width * 0.6,
                    y + height * 0.6,
                    width * 0.35,
                    height * 0.35,
                    0.1,
                    [0.8, 0.8, 0.95],  # light blue
                    base_z
                )
                furniture.append(shower)
        
        elif "garage" in room_type or "car parking" in room_type:
            # Add a car, leaving plenty of space for doors to open
            car = self._create_furniture(
                "car",
                x + width * 0.2,
                y + height * 0.3,
                width * 0.6,
                height * 0.4,
                1.5,
                [0.7, 0.1, 0.1],  # red car
                base_z
            )
            furniture.append(car)
            
        elif "terrace" in room_type:
            # Add outdoor furniture
            table = self._create_furniture(
                "outdoor_table",
                x + width * 0.4,
                y + height * 0.4,
                width * 0.2,
                height * 0.2,
                0.7,
                [0.4, 0.5, 0.4],  # dark green
                base_z
            )
            furniture.append(table)
        
        elif "lobby" in room_type or "entrance" in room_type:
            # Add a console table
            table = self._create_furniture(
                "console_table",
                x + width * 0.1,
                y + height * 0.8,
                width * 0.3,
                height * 0.15,
                0.9,
                [0.6, 0.4, 0.2],  # wood
                base_z
            )
            furniture.append(table)
        
        elif "dining" in room_type:
            # Add dining table in center
            dining_table = self._create_furniture(
                "dining_table",
                x + width * 0.25,
                y + height * 0.25,
                width * 0.5,
                height * 0.5,
                0.8,
                [0.7, 0.5, 0.3],  # wood
                base_z
            )
            furniture.append(dining_table)
        
        return furniture
    
    def _create_furniture(self, furniture_type, x, y, width, depth, height, color, z_offset=0):
        """Create a piece of furniture with the given dimensions."""
        return {
            "type": furniture_type,
            "position": [x, y, z_offset],  # Place on floor
            "dimensions": [width, depth, height],
            "color": color
        }
    
    def _add_doors_to_model(self, model, layout):
        """Add doors to the 3D model based on the layout."""
        # Get door information from layout
        doors = layout.get("doors", [])
        
        for door in doors:
            door_pos = door["position"]
            orientation = door["orientation"]
            width = door.get("width", self.door_width)
            connects = door.get("connects", [-1, -1])
            door_type = door.get("type", "standard")
            
            # Determine door height based on type
            height = self.door_height
            if door_type == "main_entrance":
                height = self.door_height * 1.1  # Slightly taller main door
            
            # Determine which story this door is on
            story = 1
            if connects[0] >= 0 and connects[0] < len(layout["rooms"]):
                story = layout["rooms"][connects[0]].get("story", 1)
            
            # Calculate z position based on story
            z_offset = (story - 1) * (self.wall_height + self.floor_thickness)
            
            # Create door object
            door_obj = {
                "type": door_type,
                "position": [door_pos[0], door_pos[1], z_offset],
                "orientation": orientation,
                "dimensions": [width, 0.1, height],  # 10cm thick door
                "color": [0.6, 0.4, 0.2],  # Brown door
                "connects": connects
            }
            
            model["doors"].append(door_obj)
        
        return model
    
    def _add_windows_to_model(self, model, layout):
        """Add windows to exterior walls."""
        # Find exterior walls based on room layout
        rooms = layout.get("rooms", [])
        stories = layout.get("stories", 1)
        
        for story in range(1, stories + 1):
            # Filter rooms for this story
            story_rooms = [r for r in rooms if r.get("story", 1) == story]
            
            # Calculate z position based on story
            z_offset = (story - 1) * (self.wall_height + self.floor_thickness)
            
            # Find bounds of the story
            if not story_rooms:
                continue
                
            min_x = min(r["position"][0] for r in story_rooms)
            max_x = max(r["position"][0] + r["size"][0] for r in story_rooms)
            min_y = min(r["position"][1] for r in story_rooms)
            max_y = max(r["position"][1] + r["size"][1] for r in story_rooms)
            
            # For each room, check if it has exterior walls
            for room in story_rooms:
                x, y = room["position"]
                width, height = room["size"]
                
                # Check each wall
                walls = []
                
                # Bottom wall (y = y)
                if abs(y - min_y) < 0.1:  # This wall is exterior
                    walls.append({
                        "start": [x, y],
                        "end": [x + width, y],
                        "orientation": "horizontal"
                    })
                
                # Right wall (x = x + width)
                if abs((x + width) - max_x) < 0.1:
                    walls.append({
                        "start": [x + width, y],
                        "end": [x + width, y + height],
                        "orientation": "vertical"
                    })
                
                # Top wall (y = y + height)
                if abs((y + height) - max_y) < 0.1:
                    walls.append({
                        "start": [x, y + height],
                        "end": [x + width, y + height],
                        "orientation": "horizontal"
                    })
                
                # Left wall (x = x)
                if abs(x - min_x) < 0.1:
                    walls.append({
                        "start": [x, y],
                        "end": [x, y + height],
                        "orientation": "vertical"
                    })
                
                # For each exterior wall, add windows
                for wall in walls:
                    orientation = wall["orientation"]
                    start = wall["start"]
                    end = wall["end"]
                    
                    if orientation == "horizontal":
                        wall_length = end[0] - start[0]
                        
                        # Skip short walls
                        if wall_length < 2.0:
                            continue
                        
                        # Add window in the middle of the wall
                        window_pos_x = start[0] + wall_length/2 - self.window_width/2
                        window_pos_y = start[1]
                        
                        window = {
                            "position": [window_pos_x, window_pos_y, z_offset + self.window_sill],
                            "dimensions": [self.window_width, 0.1, self.window_height],
                            "orientation": "horizontal"
                        }
                        model["windows"].append(window)
                    else:  # vertical
                        wall_length = end[1] - start[1]
                        
                        # Skip short walls
                        if wall_length < 2.0:
                            continue
                        
                        # Add window in the middle of the wall
                        window_pos_x = start[0]
                        window_pos_y = start[1] + wall_length/2 - self.window_width/2
                        
                        window = {
                            "position": [window_pos_x, window_pos_y, z_offset + self.window_sill],
                            "dimensions": [0.1, self.window_width, self.window_height],
                            "orientation": "vertical"
                        }
                        model["windows"].append(window)
        
        return model
    
    def _add_staircases_to_model(self, model, layout):
        """Add staircases between stories."""
        stories = layout.get("stories", 1)
        stairs = layout.get("stairs", [])
        
        for stair in stairs:
            pos = stair["position"]
            dims = stair["dimensions"]
            from_story = stair.get("from_story", 1)
            to_story = stair.get("to_story", 2)
            
            # Calculate z position based on story
            z_offset = (from_story - 1) * (self.wall_height + self.floor_thickness)
            z_height = self.wall_height + self.floor_thickness
            
            # Create staircase
            staircase = self._create_staircase(
                pos[0], pos[1], dims[0], dims[1],
                z_offset, z_height
            )
            
            model["stairs"].append(staircase)
        
        return model
    
    def _create_staircase(self, x, y, width, depth, z_start, z_height):
        """Create a staircase object."""
        # Number of steps
        num_steps = 12
        
        return {
            "type": "stairs",
            "position": [x, y, z_start],
            "dimensions": [width, depth, z_height],
            "steps": num_steps,
            "color": [0.6, 0.5, 0.4]  # Wood color
        }
    
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
        
        # Add plot size and stories information
        plot_info = ""
        if "plot_size" in model:
            plot_size = model["plot_size"]
            if "marla" in plot_size and "kanal" in plot_size:
                plot_info += f"Plot Size: {plot_size['marla']:.2f} Marla ({plot_size['kanal']:.2f} Kanal)\n"
            if "width_meters" in plot_size and "length_meters" in plot_size:
                plot_info += f"Dimensions: {plot_size['width_meters']:.1f}m × {plot_size['length_meters']:.1f}m\n"
        
        stories_info = f"Stories: {model.get('stories', 1)}"
        
        # Add a timestamp and title to the figure
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        plt.figtext(0.5, 0.01, f"Generated on {timestamp}", ha="center", fontsize=10)
        plt.suptitle(f"3D House Model - {plot_info}{stories_info}", fontsize=18, y=0.98)
        
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
                          bbox_to_anchor=(0.5, 0.05), ncol=min(5, len(custom_lines)),
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
        
        # Draw doors (above walls)
        self._draw_doors(ax, model)
        
        # Draw windows (above walls)
        self._draw_windows(ax, model)
        
        # Draw furniture (top layer)
        self._draw_furniture_enhanced(ax, model)
        
        # Draw stairs if they exist
        self._draw_stairs(ax, model)
        
        # Add room labels with better styling
        self._add_room_labels(ax, model)
        
    def _visualize_generic(self, ax, model):
        """Generic visualization for simple models."""
        vertices = np.array(model["vertices"])
        faces = model["faces"]
        colors = model["colors"]
        
        for i, face in enumerate(faces):
            # Get vertices for this face
            face_vertices = vertices[face]
            
            # Draw face
            color = colors[i % len(colors)]
            poly = Poly3DCollection([face_vertices], alpha=0.7)
            poly.set_facecolor(color)
            poly.set_edgecolor('black')
            poly.set_linewidth(0.5)
            ax.add_collection3d(poly)

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
                is_bottom = np.mean(z_coords) < 0.1 + (room_mesh.get("story", 1) - 1) * self.wall_height
                
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
            story = room_mesh.get("story", 1)
            
            # Story-based z-offset
            z_offset = (story - 1) * self.wall_height
            
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
                if is_horizontal and avg_z > z_offset + self.wall_height - 0.1:  # Ceiling height check
                    continue
                    
                # Skip floors (already drawn)
                if is_horizontal and abs(avg_z - z_offset) < 0.1:  # Floor height check
                    continue
                    
                # This must be a wall - draw it semi-transparent
                # Use original color but with transparency for walls
                poly = Poly3DCollection([face_vertices], alpha=0.7)
                poly.set_facecolor(room_color)
                poly.set_edgecolor('black')
                poly.set_linewidth(1)
                ax.add_collection3d(poly)
    
    def _draw_doors(self, ax, model):
        """Draw doors in the 3D visualization."""
        for door in model.get("doors", []):
            x, y, z = door["position"]
            width, thickness, height = door["dimensions"]
            orientation = door.get("orientation", "horizontal")
            color = door.get("color", [0.6, 0.4, 0.2])  # Brown door
            
            # Draw door frame
            if orientation == "horizontal":
                # Door on vertical wall
                vertices = [
                    [x - width/2, y, z],
                    [x + width/2, y, z],
                    [x + width/2, y, z + height],
                    [x - width/2, y, z + height]
                ]
            else:
                # Door on horizontal wall
                vertices = [
                    [x, y - width/2, z],
                    [x, y + width/2, z],
                    [x, y + width/2, z + height],
                    [x, y - width/2, z + height]
                ]
                
            # Draw door
            poly = Poly3DCollection([vertices], alpha=0.8)
            poly.set_facecolor(color)
            poly.set_edgecolor('black')
            poly.set_linewidth(1)
            ax.add_collection3d(poly)
    
    def _draw_windows(self, ax, model):
        """Draw windows in the 3D visualization."""
        for window in model.get("windows", []):
            x, y, z = window["position"]
            width, thickness, height = window["dimensions"]
            orientation = window.get("orientation", "horizontal")
            
            # Draw window as blue transparent rectangle
            if orientation == "horizontal":
                # Window on vertical wall
                vertices = [
                    [x, y, z],
                    [x + width, y, z],
                    [x + width, y, z + height],
                    [x, y, z + height]
                ]
            else:
                # Window on horizontal wall
                vertices = [
                    [x, y, z],
                    [x, y + width, z],
                    [x, y + width, z + height],
                    [x, y, z + height]
                ]
                
            # Draw window with blue tint
            poly = Poly3DCollection([vertices], alpha=0.6)
            poly.set_facecolor([0.7, 0.8, 0.95])  # Light blue for glass
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
    
    def _draw_stairs(self, ax, model):
        """Draw stairs in the 3D visualization."""
        for stair in model.get("stairs", []):
            x, y, z = stair["position"]
            width, depth, height = stair["dimensions"]
            steps = stair.get("steps", 12)
            color = stair.get("color", [0.6, 0.5, 0.4])  # Wood color
            
            # Calculate step dimensions
            step_height = height / steps
            step_depth = depth / steps
            
            # Draw each step
            for i in range(steps):
                step_z = z + i * step_height
                step_y = y + i * step_depth
                
                # Draw step
                self._draw_box(ax, x, step_y, step_z, width, step_depth, step_height, color)
    
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
            story = room_mesh.get("story", 1)
            
            # Make label more descriptive
            if room_type:
                label = f"{room_type.upper()}"
                if story > 1:
                    label += f" (F{story})"
            else:
                label = room_name
                if story > 1:
                    label += f" (F{story})"
                
            # Position label in the center of the room but higher up
            label_pos = [room_center[0], room_center[1], room_center[2] + 1.0]
            
            # Add text with better visibility - larger font and background
            ax.text(label_pos[0], label_pos[1], label_pos[2], label,
                  fontsize=10, fontweight='bold', color='black', ha='center', va='center',
                  bbox=dict(facecolor='white', alpha=0.7, edgecolor='black', boxstyle='round,pad=0.5'))
    
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
        
        # Draw each face with slight transparency
        for face in faces:
            poly = Poly3DCollection([face], alpha=0.8)
            poly.set_facecolor(color)
            poly.set_edgecolor('black')
            poly.set_linewidth(0.5)
            ax.add_collection3d(poly)
    
    def _draw_bed(self, ax, x, y, z, w, d, h, color):
        """Draw a bed with more detail."""
        # Base frame
        base_height = h * 0.2
        self._draw_box(ax, x, y, z, w, d, base_height, color)
        
        # Mattress - slightly smaller than base
        mattress_color = [0.9, 0.9, 0.95]  # Off-white
        mattress_inset = 0.1
        self._draw_box(ax, x+mattress_inset, y+mattress_inset, z+base_height,
                      w-2*mattress_inset, d-2*mattress_inset, h-base_height, mattress_color)
        
        # Pillows at the head of the bed
        pillow_width = w * 0.3
        pillow_depth = d * 0.2
        pillow_height = (h - base_height) * 0.5
        pillow_color = [0.95, 0.95, 0.95]  # White
        
        # Two pillows side by side
        self._draw_box(ax, x+w*0.15, y+d*0.05, z+h-pillow_height, 
                      pillow_width, pillow_depth, pillow_height, pillow_color)
        self._draw_box(ax, x+w*0.55, y+d*0.05, z+h-pillow_height, 
                      pillow_width, pillow_depth, pillow_height, pillow_color)
    
    def _draw_sofa(self, ax, x, y, z, w, d, h, color):
        """Draw a sofa with more detail."""
        # Base
        base_height = h * 0.3
        self._draw_box(ax, x, y, z, w, d, base_height, color)
        
        # Back cushion
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
        leg_width = min(w, d) * 0.1
        leg_locations = [
            [x + leg_width/2, y + leg_width/2],
            [x + w - leg_width*1.5, y + leg_width/2],
            [x + leg_width/2, y + d - leg_width*1.5],
            [x + w - leg_width*1.5, y + d - leg_width*1.5]
        ]
        
        for leg_pos in leg_locations:
            self._draw_box(ax, leg_pos[0], leg_pos[1], z, 
                          leg_width, leg_width, h-top_height, color)
    
    def _draw_counter(self, ax, x, y, z, w, d, h, color):
        """Draw a kitchen counter with more detail."""
        # Base cabinets
        base_height = h * 0.8
        self._draw_box(ax, x, y, z, w, d, base_height, color)
        
        # Counter top - slightly wider than base
        extend = 0.02
        counter_color = [0.9, 0.9, 0.9]  # Light gray for counter
        self._draw_box(ax, x-extend, y-extend, z+base_height, 
                      w+2*extend, d+2*extend, h-base_height, counter_color)
    
    def export_obj(self, model, filename):
        """Export the 3D model to OBJ format with enhanced materials."""
        start_time = time.time()
        print(f"Exporting 3D model to {filename}...")
        
        # Create an OBJ exporter that adds materials
        with open(filename, 'w') as f:
            # Write OBJ header with current date
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
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
        
        print(f"Model exported successfully in {time.time() - start_time:.2f} seconds")
        return True
    
    def _export_house_obj(self, f, model):
        """Export house-specific OBJ content."""
        # Write room groups and their faces
        for room_idx, room in enumerate(model.get("room_meshes", [])):
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
        vertex_counter = 0
        
        # Add furniture
        for i, furniture in enumerate(model.get("furniture", [])):
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
                vertex_counter += 1
            
            # Calculate base index for this furniture
            base_idx = vertex_offset + vertex_counter - 7
            
            # Define faces
            f.write(f"f {base_idx} {base_idx+1} {base_idx+2} {base_idx+3}\n")  # bottom
            f.write(f"f {base_idx+4} {base_idx+5} {base_idx+6} {base_idx+7}\n")  # top
            f.write(f"f {base_idx} {base_idx+1} {base_idx+5} {base_idx+4}\n")  # front
            f.write(f"f {base_idx+1} {base_idx+2} {base_idx+6} {base_idx+5}\n")  # right
            f.write(f"f {base_idx+2} {base_idx+3} {base_idx+7} {base_idx+6}\n")  # back
            f.write(f"f {base_idx+3} {base_idx} {base_idx+4} {base_idx+7}\n")  # left
            
            f.write("\n")
            
        # Add doors
        for i, door in enumerate(model.get("doors", [])):
            if "position" not in door or "dimensions" not in door:
                continue
                
            pos = door["position"]
            dim = door["dimensions"]
            dtype = door.get("type", "door")
            orientation = door.get("orientation", "horizontal")
            
            f.write(f"\ng door_{i}_{dtype}\n")
            f.write(f"usemtl door_{i}\n")
            
            x, y, z = pos
            width, thickness, height = dim
            
            # Define door vertices based on orientation
            door_vertices = []
            if orientation == "horizontal":
                # Door on vertical wall
                door_vertices = [
                    [x - width/2, y - thickness/2, z],
                    [x + width/2, y - thickness/2, z],
                    [x + width/2, y + thickness/2, z],
                    [x - width/2, y + thickness/2, z],
                    [x - width/2, y - thickness/2, z + height],
                    [x + width/2, y - thickness/2, z + height],
                    [x + width/2, y + thickness/2, z + height],
                    [x - width/2, y + thickness/2, z + height]
                ]
            else:
                # Door on horizontal wall
                door_vertices = [
                    [x - thickness/2, y - width/2, z],
                    [x + thickness/2, y - width/2, z],
                    [x + thickness/2, y + width/2, z],
                    [x - thickness/2, y + width/2, z],
                    [x - thickness/2, y - width/2, z + height],
                    [x + thickness/2, y - width/2, z + height],
                    [x + thickness/2, y + width/2, z + height],
                    [x - thickness/2, y + width/2, z + height]
                ]
            
            # Write vertices
            for v in door_vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                vertex_counter += 1
            
            # Calculate base index for this door
            base_idx = vertex_offset + vertex_counter - 7
            
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
        for i, room in enumerate(model.get("room_meshes", [])):
            color = room.get("color", [0.8, 0.8, 0.8])
            f.write(f"newmtl room_{i}\n")
            f.write(f"Ka {color[0]} {color[1]} {color[2]}\n")
            f.write(f"Kd {color[0]} {color[1]} {color[2]}\n")
            f.write("Ks 0.1 0.1 0.1\n")
            f.write("illum 2\n")
            f.write("Ns 10.0\n\n")
        
        # Materials for furniture
        for i, furniture in enumerate(model.get("furniture", [])):
            if "color" in furniture:
                color = furniture["color"]
                f.write(f"newmtl furniture_{i}\n")
                f.write(f"Ka {color[0]} {color[1]} {color[2]}\n")
                f.write(f"Kd {color[0]} {color[1]} {color[2]}\n")
                f.write("Ks 0.2 0.2 0.2\n")
                f.write("illum 2\n")
                f.write("Ns 20.0\n\n")
                
        # Materials for doors
        for i, door in enumerate(model.get("doors", [])):
            if "color" in door:
                color = door["color"]
            else:
                color = [0.6, 0.4, 0.2]  # Default door color (brown)
                
            f.write(f"newmtl door_{i}\n")
            f.write(f"Ka {color[0]} {color[1]} {color[2]}\n")
            f.write(f"Kd {color[0]} {color[1]} {color[2]}\n")
            f.write("Ks 0.3 0.3 0.3\n")
            f.write("illum 2\n")
            f.write("Ns 30.0\n\n")
    
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