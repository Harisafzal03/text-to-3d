"""
Improved House Layout Generator
------------------------------
Creates realistic floor plans with proper corridors and room separation
"""

import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

class ImprovedLayoutGenerator:
    def __init__(self):
        # Standard room dimensions (in meters)
        self.standard_dimensions = {
            "bedroom": {"width": 3.5, "length": 4.0, "min_area": 12},
            "kitchen": {"width": 3.0, "length": 3.5, "min_area": 9},
            "bathroom": {"width": 2.0, "length": 2.5, "min_area": 4.5},
            "washroom": {"width": 2.0, "length": 2.5, "min_area": 4.5},
            "living room": {"width": 4.0, "length": 5.0, "min_area": 15},
            "tv lounge": {"width": 4.0, "length": 4.5, "min_area": 15},
            "dining room": {"width": 3.5, "length": 4.0, "min_area": 10},
            "garage": {"width": 3.5, "length": 5.5, "min_area": 16},
            "car parking": {"width": 3.5, "length": 5.5, "min_area": 16},
            "lobby": {"width": 2.0, "length": 4.0, "min_area": 8},
            "hallway": {"width": 1.5, "length": 4.0, "min_area": 6},
            "corridor": {"width": 1.2, "length": 3.0, "min_area": 3.6},
        }
        
        # Wall thickness and door width
        self.wall_thickness = 0.25  # 25cm walls
        self.door_width = 0.9       # 90cm door width
        
        # Corridor width
        self.corridor_width = 1.2   # 1.2m wide corridors
        
        # Minimum spacing between rooms
        self.room_spacing = 0.3 + self.wall_thickness  # Space + wall thickness
    
    def generate_layout(self, rooms, plot_size, stories=1):
        """Generate an improved layout with proper corridors and spacing."""
        if not rooms:
            return {"rooms": [], "connections": [], "doors": []}
            
        # Calculate total available area
        if "width_meters" in plot_size and "length_meters" in plot_size:
            total_width = plot_size["width_meters"]
            total_length = plot_size["length_meters"]
        else:
            # Default dimensions for 10 Marla (assuming ~225 sq meters)
            total_width = 15.0
            total_length = 15.0
        
        # Adjust grid size based on plot size
        # For small plots, use smaller grid to avoid placement issues
        grid_size = max(5, int(min(total_width, total_length) / 3))
        
        # Distribute rooms by story
        rooms_by_story = self._distribute_rooms_by_story(rooms, stories)
        
        # Process each story
        all_rooms = []
        all_connections = []
        all_doors = []
        room_id = 0
        
        for story in range(1, stories + 1):
            story_rooms = rooms_by_story.get(story, [])
            if not story_rooms:
                continue
                
            # Create a structured layout for this story
            story_layout = self._generate_story_layout(
                story_rooms, total_width, total_length, story, room_id, grid_size
            )
            
            # Update room_id counter
            room_id += len(story_layout["rooms"])
            
            # Add to overall layout
            all_rooms.extend(story_layout["rooms"])
            all_connections.extend(story_layout["connections"])
            all_doors.extend(story_layout["doors"])
            
        # Create the complete layout
        layout = {
            "rooms": all_rooms,
            "connections": all_connections,
            "doors": all_doors,
            "stories": stories,
            "plot_size": plot_size
        }
        
        return layout
    
    def _distribute_rooms_by_story(self, rooms, stories):
        """Distribute rooms across stories in a logical way."""
        rooms_by_story = {story: [] for story in range(1, stories + 1)}
        
        # First, categorize rooms by type
        public_rooms = []
        bedrooms = []
        bathrooms = []
        other_rooms = []
        
        for room in rooms:
            room_type = room["type"].lower()
            if room_type in ["living room", "tv lounge", "kitchen", "dining room", 
                            "lobby", "entrance", "garage", "car parking"]:
                public_rooms.append(room)
            elif room_type == "bedroom":
                bedrooms.append(room)
            elif room_type in ["bathroom", "washroom"]:
                bathrooms.append(room)
            else:
                other_rooms.append(room)
        
        # Place public rooms on ground floor
        rooms_by_story[1].extend(public_rooms)
        
        if stories == 1:
            # Everything on one floor
            rooms_by_story[1].extend(bedrooms)
            rooms_by_story[1].extend(bathrooms)
            rooms_by_story[1].extend(other_rooms)
        else:
            # Distribute bedrooms + bathrooms on upper floors
            bedrooms_per_floor = max(1, len(bedrooms) // (stories - 1))
            bathrooms_per_floor = max(1, len(bathrooms) // (stories - 1))
            
            # Add some bedrooms and bathrooms to first floor if we have many
            if len(bedrooms) > 2 * (stories - 1):
                rooms_by_story[1].append(bedrooms.pop(0))
                if bathrooms:
                    rooms_by_story[1].append(bathrooms.pop(0))
            
            # Distribute remaining bedrooms and bathrooms on upper floors
            for story in range(2, stories + 1):
                # Take bedrooms for this floor
                for _ in range(min(bedrooms_per_floor, len(bedrooms))):
                    if bedrooms:
                        rooms_by_story[story].append(bedrooms.pop(0))
                        
                # Take bathrooms for this floor
                for _ in range(min(bathrooms_per_floor, len(bathrooms))):
                    if bathrooms:
                        rooms_by_story[story].append(bathrooms.pop(0))
            
            # Distribute any remaining rooms
            for story in range(2, stories + 1):
                while bedrooms:
                    rooms_by_story[story].append(bedrooms.pop(0))
                    break
                    
                while bathrooms:
                    rooms_by_story[story].append(bathrooms.pop(0))
                    break
            
            # Distribute other rooms
            for room in other_rooms:
                # Find the story with fewest rooms
                min_story = min(range(1, stories + 1), 
                              key=lambda s: len(rooms_by_story[s]))
                rooms_by_story[min_story].append(room)
        
        # Ensure each floor has at least one room
        for story in range(1, stories + 1):
            if not rooms_by_story[story]:
                # Add a hallway if no rooms
                rooms_by_story[story].append({"type": "hallway"})
                
        return rooms_by_story
    
    def _generate_story_layout(self, rooms, total_width, total_length, story, start_id, grid_size=8):
        """Generate a realistic layout for a single story with corridors."""
        # Initialize grid - represents room placement
        grid = np.zeros((grid_size, grid_size), dtype=int)
        
        # Zone definitions - divide the house into functional zones
        zones = {
            "public": {"position": (0, 0), "size": (grid_size // 2, grid_size // 2)},
            "private": {"position": (grid_size // 2, 0), "size": (grid_size // 2, grid_size // 2)},
            "service": {"position": (0, grid_size // 2), "size": (grid_size // 2, grid_size // 2)},
            "other": {"position": (grid_size // 2, grid_size // 2), "size": (grid_size // 2, grid_size // 2)}
        }
        
        # First, place important rooms by zone
        # Split rooms by function
        public_rooms = [r for r in rooms if r["type"].lower() in 
                       ["living room", "tv lounge", "dining room", "lobby", "entrance"]]
        kitchen_rooms = [r for r in rooms if r["type"].lower() in ["kitchen"]]
        bedroom_rooms = [r for r in rooms if r["type"].lower() == "bedroom"]
        bathroom_rooms = [r for r in rooms if r["type"].lower() in ["bathroom", "washroom"]]
        garage_rooms = [r for r in rooms if r["type"].lower() in ["garage", "car parking"]]
        other_rooms = [r for r in rooms if r not in public_rooms + kitchen_rooms + 
                      bedroom_rooms + bathroom_rooms + garage_rooms]
        
        # Place corridor first - this will be the central spine
        corridor = {"type": "corridor", "id": start_id}
        corridor_pos, corridor_size = self._place_corridor(grid, grid_size)
        
        # Place rooms strategically
        room_placements = []
        
        # Place public rooms near entrance (lower part of grid)
        for i, room in enumerate(public_rooms):
            zone = "public"
            if i < len(public_rooms) // 2:
                zone_pos = zones[zone]["position"]
                zone_size = zones[zone]["size"]
            else:
                zone = "other"
                zone_pos = zones[zone]["position"]
                zone_size = zones[zone]["size"]
                
            room_pos, room_size = self._place_room_in_zone(grid, room, zone_pos, zone_size, corridor_pos)
            if room_pos:
                room_placements.append({
                    "room": room,
                    "position": room_pos,
                    "size": room_size
                })
        
        # Place kitchen rooms in service zone
        for room in kitchen_rooms:
            zone = "service"
            zone_pos = zones[zone]["position"]
            zone_size = zones[zone]["size"]
            room_pos, room_size = self._place_room_in_zone(grid, room, zone_pos, zone_size, corridor_pos)
            if room_pos:
                room_placements.append({
                    "room": room,
                    "position": room_pos,
                    "size": room_size
                })
        
        # Place bedrooms in private zone
        for room in bedroom_rooms:
            zone = "private"
            zone_pos = zones[zone]["position"]
            zone_size = zones[zone]["size"]
            room_pos, room_size = self._place_room_in_zone(grid, room, zone_pos, zone_size, corridor_pos)
            if room_pos:
                room_placements.append({
                    "room": room,
                    "position": room_pos,
                    "size": room_size
                })
        
        # Place bathrooms near bedrooms
        for i, room in enumerate(bathroom_rooms):
            if i < len(bedroom_rooms) and len(room_placements) > len(public_rooms) + len(kitchen_rooms) + i:
                # Try to place near a bedroom
                bedroom_idx = len(public_rooms) + len(kitchen_rooms) + i
                if bedroom_idx < len(room_placements):
                    bedroom_placement = room_placements[bedroom_idx]
                    bedroom_pos = bedroom_placement["position"]
                    
                    # Try positions adjacent to the bedroom
                    room_pos, room_size = self._place_room_near_position(grid, room, bedroom_pos)
                    if room_pos:
                        room_placements.append({
                            "room": room,
                            "position": room_pos,
                            "size": room_size
                        })
                        continue
            
            # Fall back to placing in any zone
            zone = "private"
            zone_pos = zones[zone]["position"]
            zone_size = zones[zone]["size"]
            room_pos, room_size = self._place_room_in_zone(grid, room, zone_pos, zone_size, corridor_pos)
            if room_pos:
                room_placements.append({
                    "room": room,
                    "position": room_pos,
                    "size": room_size
                })
        
        # Place garage/car parking near service zone
        for room in garage_rooms:
            zone = "service"
            zone_pos = zones[zone]["position"]
            zone_size = zones[zone]["size"]
            room_pos, room_size = self._place_room_in_zone(grid, room, zone_pos, zone_size, corridor_pos)
            if room_pos:
                room_placements.append({
                    "room": room,
                    "position": room_pos,
                    "size": room_size
                })
        
        # Place remaining rooms in any available space
        for room in other_rooms:
            # Try all zones until we find space
            placed = False
            for zone_name in ["public", "private", "service", "other"]:
                if placed:
                    break
                    
                zone_pos = zones[zone_name]["position"]
                zone_size = zones[zone_name]["size"]
                room_pos, room_size = self._place_room_in_zone(grid, room, zone_pos, zone_size, corridor_pos)
                if room_pos:
                    room_placements.append({
                        "room": room,
                        "position": room_pos,
                        "size": room_size
                    })
                    placed = True
            
            # If can't place in zones, try anywhere
            if not placed:
                room_pos, room_size = self._place_room_anywhere(grid, room)
                if room_pos:
                    room_placements.append({
                        "room": room,
                        "position": room_pos,
                        "size": room_size
                    })
        
        # Convert grid positions to actual coordinates
        scale_x = total_width / grid_size
        scale_y = total_length / grid_size
        
        # Create room objects with real coordinates
        rooms_list = []
        room_id = start_id
        
        # Add corridor first
        corridor_width = self.corridor_width * (grid_size / 8)  # Scale corridor width to grid
        corridor_room = {
            "id": room_id,
            "type": "corridor",
            "name": "Corridor",
            "position": [corridor_pos[0] * scale_x, corridor_pos[1] * scale_y],
            "size": [corridor_size[0] * scale_x, corridor_size[1] * scale_y],
            "story": story
        }
        rooms_list.append(corridor_room)
        room_id += 1
        
        # Add all other rooms
        for placement in room_placements:
            room = placement["room"]
            pos = placement["position"]
            size = placement["size"]
            
            # Calculate real coordinates
            real_x = pos[0] * scale_x
            real_y = pos[1] * scale_y
            real_width = size[0] * scale_x
            real_height = size[1] * scale_y
            
            room_obj = {
                "id": room_id,
                "type": room["type"],
                "name": f"{room['type'].capitalize()}",
                "position": [real_x, real_y],
                "size": [real_width, real_height],
                "story": story
            }
            rooms_list.append(room_obj)
            room_id += 1
        
        # Create connections and doors between rooms and corridor
        connections = []
        doors = []
        
        # Connect all rooms to the corridor
        corridor_id = start_id  # First room is the corridor
        
        for i, room in enumerate(rooms_list[1:], start=1):  # Skip the corridor itself
            room_id = start_id + i
            
            # Create connection
            connections.append({
                "source": corridor_id,
                "target": room_id,
                "type": "door"
            })
            
            # Find a good door position between corridor and room
            door_pos = self._find_door_position(rooms_list[0], room)
            if door_pos:
                doors.append({
                    "position": door_pos["position"],
                    "orientation": door_pos["orientation"],
                    "width": self.door_width,
                    "connects": [corridor_id, room_id]
                })
        
        # Add exterior door for the entrance
        for i, room in enumerate(rooms_list):
            if room["type"].lower() in ["entrance", "lobby", "main entrance"]:
                # Add door to exterior
                x, y = room["position"]
                width, height = room["size"]
                
                # Place at the bottom edge
                door_pos = [x + width/2, y]
                doors.append({
                    "position": door_pos,
                    "orientation": "vertical",
                    "width": self.door_width * 1.2,  # Wider main door
                    "type": "main_entrance",
                    "connects": [start_id + i, -1]  # -1 represents outside
                })
                break
        
        # If we didn't find an entrance room, add a main door to the corridor
        if not any(d.get("type") == "main_entrance" for d in doors):
            x, y = corridor_room["position"]
            width, height = corridor_room["size"]
            
            # Place at the bottom edge
            door_pos = [x + width/2, y]
            doors.append({
                "position": door_pos,
                "orientation": "vertical",
                "width": self.door_width * 1.2,  # Wider main door
                "type": "main_entrance",
                "connects": [start_id, -1]  # -1 represents outside
            })
        
        # Create layout for this story
        story_layout = {
            "rooms": rooms_list,
            "connections": connections,
            "doors": doors
        }
        
        return story_layout
    
    def _place_corridor(self, grid, grid_size):
        """Place a central corridor through the house."""
        # For now, place a simple corridor in the center
        corridor_width = 1  # Grid units
        corridor_length = grid_size - 2  # Grid units
        
        # Place horizontally through the center
        x = 1
        y = grid_size // 2
        
        # Make sure corridor fits in grid
        if y + corridor_width > grid_size:
            y = grid_size - corridor_width - 1
        
        # Mark corridor cells as occupied
        grid[y:y+corridor_width, x:x+corridor_length] = 1
        
        return (x, y), (corridor_length, corridor_width)
    
    def _place_room_in_zone(self, grid, room, zone_pos, zone_size, corridor_pos):
        """Place a room in a specific zone, avoiding the corridor."""
        room_type = room["type"].lower()
        
        # Get standard dimensions for this room type
        if room_type in self.standard_dimensions:
            std_dim = self.standard_dimensions[room_type]
            min_area = std_dim["min_area"]
            
            # Calculate grid units based on minimum area
            grid_area = min_area / 4  # Assuming each grid cell is roughly 2x2 meters
            
            # Calculate width and height in grid units
            grid_width = max(1, int(np.ceil(std_dim["width"] / 2)))
            grid_height = max(1, int(np.ceil(std_dim["length"] / 2)))
            
            # Ensure we meet minimum area
            while grid_width * grid_height < grid_area:
                grid_width += 1
        else:
            # Default size
            grid_width = 2
            grid_height = 2
        
        # Get zone boundaries
        zone_x, zone_y = zone_pos
        zone_w, zone_h = zone_size
        
        # Check if room can fit in zone
        if grid_width > zone_w or grid_height > zone_h:
            # Room too big for zone, try to resize
            if grid_width > zone_w:
                grid_width = zone_w
            if grid_height > zone_h:
                grid_height = zone_h
            
            # If room is still too big (minimum dimension), place anywhere
            if grid_width > zone_w or grid_height > zone_h:
                return self._place_room_anywhere(grid, room)
        
        # Try to place the room in the zone
        for _ in range(50):  # Try 50 times
            # Make sure we have a valid range for random placement
            if zone_x + zone_w - grid_width < zone_x:
                x = zone_x
            else:
                x = random.randint(zone_x, zone_x + zone_w - grid_width)
            
            if zone_y + zone_h - grid_height < zone_y:
                y = zone_y
            else:
                y = random.randint(zone_y, zone_y + zone_h - grid_height)
            
            # Check if this position is valid (doesn't overlap with corridor or other rooms)
            if self._is_position_valid(grid, x, y, grid_width, grid_height):
                # Mark grid as occupied
                grid[y:y+grid_height, x:x+grid_width] = 1
                return (x, y), (grid_width, grid_height)
                
        # If we reach here, we couldn't place the room in the zone
        # Try anywhere on the grid
        return self._place_room_anywhere(grid, room)
    
    def _place_room_anywhere(self, grid, room):
        """Place a room anywhere on the grid where it fits."""
        room_type = room["type"].lower()
        
        # Get dimensions
        if room_type in self.standard_dimensions:
            std_dim = self.standard_dimensions[room_type]
            grid_width = max(1, int(np.ceil(std_dim["width"] / 2)))
            grid_height = max(1, int(np.ceil(std_dim["length"] / 2)))
        else:
            grid_width = 2
            grid_height = 2
        
        # Try to fit in available space
        for _ in range(100):  # Try 100 times
            # Make sure we don't go out of bounds
            if grid.shape[1] <= grid_width:
                x = 0
            else:
                x = random.randint(0, grid.shape[1] - grid_width - 1)
                
            if grid.shape[0] <= grid_height:
                y = 0
            else:
                y = random.randint(0, grid.shape[0] - grid_height - 1)
            
            if self._is_position_valid(grid, x, y, grid_width, grid_height):
                # Mark grid as occupied
                grid[y:y+grid_height, x:x+grid_width] = 1
                return (x, y), (grid_width, grid_height)
        
        # If still can't place, make room smaller
        if grid_width > 1 and grid_height > 1:
            grid_width -= 1
            grid_height -= 1
            
            for _ in range(50):
                # Make sure we don't go out of bounds
                if grid.shape[1] <= grid_width:
                    x = 0
                else:
                    x = random.randint(0, grid.shape[1] - grid_width - 1)
                    
                if grid.shape[0] <= grid_height:
                    y = 0
                else:
                    y = random.randint(0, grid.shape[0] - grid_height - 1)
                
                if self._is_position_valid(grid, x, y, grid_width, grid_height):
                    # Mark grid as occupied
                    grid[y:y+grid_height, x:x+grid_width] = 1
                    return (x, y), (grid_width, grid_height)
        
        # As a last resort, return a fixed position with minimal size
        # Find any open cell
        for y in range(grid.shape[0]):
            for x in range(grid.shape[1]):
                if grid[y, x] == 0:
                    grid[y, x] = 1
                    return (x, y), (1, 1)
                    
        # If we really can't place it anywhere (grid is full)
        return None, None
    
    def _place_room_near_position(self, grid, room, target_pos):
        """Place a room adjacent to a target position."""
        room_type = room["type"].lower()
        target_x, target_y = target_pos
        
        # Get standard dimensions for this room type
        if room_type in self.standard_dimensions:
            std_dim = self.standard_dimensions[room_type]
            min_area = std_dim["min_area"]
            
            # Calculate grid units based on minimum area
            grid_area = min_area / 4  # Assuming each grid cell is roughly 2x2 meters
            
            # Calculate width and height in grid units
            grid_width = max(1, int(np.ceil(std_dim["width"] / 2)))
            grid_height = max(1, int(np.ceil(std_dim["length"] / 2)))
            
            # Ensure we meet minimum area
            while grid_width * grid_height < grid_area:
                grid_width += 1
        else:
            # Default size
            grid_width = 2
            grid_height = 2
        
        # Try positions around the target
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            x = target_x + dx * grid_width
            y = target_y + dy * grid_height
            
            # Ensure we're within grid bounds
            if x < 0 or y < 0 or x + grid_width > grid.shape[1] or y + grid_height > grid.shape[0]:
                continue
            
            # Check if position is valid
            if self._is_position_valid(grid, x, y, grid_width, grid_height):
                # Mark grid as occupied
                grid[y:y+grid_height, x:x+grid_width] = 1
                return (x, y), (grid_width, grid_height)
        
        # If we couldn't place next to target, try nearby
        for _ in range(20):
            # Try random position within 3 cells of target
            x = max(0, min(grid.shape[1] - grid_width, target_x + random.randint(-3, 3)))
            y = max(0, min(grid.shape[0] - grid_height, target_y + random.randint(-3, 3)))
            
            if self._is_position_valid(grid, x, y, grid_width, grid_height):
                # Mark grid as occupied
                grid[y:y+grid_height, x:x+grid_width] = 1
                return (x, y), (grid_width, grid_height)
        
        # If still can't place, try anywhere
        return self._place_room_anywhere(grid, room)
    
    def _is_position_valid(self, grid, x, y, width, height):
        """Check if a position is valid for room placement."""
        # Check grid bounds
        if x < 0 or y < 0 or x + width > grid.shape[1] or y + height > grid.shape[0]:
            return False
        
        # Check if any cell is already occupied
        if np.any(grid[y:y+height, x:x+width] != 0):
            return False
        
        return True
    
    def _find_door_position(self, room1, room2):
        """Find a suitable door position between two rooms."""
        x1, y1 = room1["position"]
        w1, h1 = room1["size"]
        x2, y2 = room2["position"]
        w2, h2 = room2["size"]
        
        # Calculate room boundaries
        r1_left, r1_right = x1, x1 + w1
        r1_bottom, r1_top = y1, y1 + h1
        
        r2_left, r2_right = x2, x2 + w2
        r2_bottom, r2_top = y2, y2 + h2
        
        # Check if rooms share a vertical wall
        if (abs(r1_right - r2_left) < 0.1 or abs(r2_right - r1_left) < 0.1) and \
           ((r1_bottom <= r2_top and r1_top >= r2_bottom) or
            (r2_bottom <= r1_top and r2_top >= r1_bottom)):
            # Find the overlapping section
            overlap_bottom = max(r1_bottom, r2_bottom)
            overlap_top = min(r1_top, r2_top)
            overlap_middle = (overlap_bottom + overlap_top) / 2
            
            # Door on vertical wall
            if abs(r1_right - r2_left) < 0.1:
                return {
                    "position": [r1_right, overlap_middle],
                    "orientation": "horizontal"
                }
            else:  # r2_right ~= r1_left
                return {
                    "position": [r1_left, overlap_middle],
                    "orientation": "horizontal"
                }
        
        # Check if rooms share a horizontal wall
        if (abs(r1_top - r2_bottom) < 0.1 or abs(r2_top - r1_bottom) < 0.1) and \
           ((r1_left <= r2_right and r1_right >= r2_left) or
            (r2_left <= r1_right and r2_right >= r1_left)):
            # Find the overlapping section
            overlap_left = max(r1_left, r2_left)
            overlap_right = min(r1_right, r2_right)
            overlap_middle = (overlap_left + overlap_right) / 2
            
            # Door on horizontal wall
            if abs(r1_top - r2_bottom) < 0.1:
                return {
                    "position": [overlap_middle, r1_top],
                    "orientation": "vertical"
                }
            else:  # r2_top ~= r1_bottom
                return {
                    "position": [overlap_middle, r1_bottom],
                    "orientation": "vertical"
                }
        
        # If rooms aren't adjacent, create a virtual door between their centers
        c1x, c1y = x1 + w1/2, y1 + h1/2
        c2x, c2y = x2 + w2/2, y2 + h2/2
        
        # Check if centers are more aligned horizontally or vertically
        if abs(c1x - c2x) > abs(c1y - c2y):
            # More horizontal distance - vertical door
            return {
                "position": [(c1x + c2x) / 2, (c1y + c2y) / 2],
                "orientation": "vertical"
            }
        else:
            # More vertical distance - horizontal door
            return {
                "position": [(c1x + c2x) / 2, (c1y + c2y) / 2],
                "orientation": "horizontal"
            }